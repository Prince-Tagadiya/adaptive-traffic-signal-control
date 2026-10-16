# Project Audit & Implementation Verification Report

**Document**: `final_paper/supplementary/project_audit.md`  
**Target Journal**: *Journal of Intelligent Transportation Systems: Technology, Planning, and Operations* (Taylor & Francis)  
**Date**: October 2026  
**Auditor**: Antigravity Autonomous Research Team  
**Audit Status**: VERIFIED AND LOCKED (No code modifications, no parameter adjustments, strictly reproducible)

---

## 1. Executive Summary & Audit Scope

This document provides a comprehensive, rigorous forensic audit of the `traffic_signal_research/` codebase prior to manuscript preparation. The purpose is to guarantee complete scientific defensibility, absolute transparency, and exact correspondence between:
1. The mathematical formulation presented in the manuscript.
2. The software implementation executed in Eclipse SUMO via TraCI.
3. The empirical simulation data recorded during the locked final blind test evaluation.

In accordance with strict publication standards, all assertions in the manuscript must be directly verifiable in the active codebase.

---

## 2. Inventory of Audited Components

| Subdirectory | Core Files Inspected | Audit Finding |
| :--- | :--- | :--- |
| **`controllers/`** | `proposed_adaptive_controller.py`<br>`basic_density_controller.py`<br>`optimized_fixed_time_controller.py`<br>`fixed_time_controller.py`<br>`base_controller.py` | Implementation verified. C3 strictly implements the 5-component composite priority formulation with hysteresis and safety constraints. All parameter values match frozen specifications. |
| **`simulation/`** | `runner.py`<br>`metrics.py` | Simulation lifecycle, TraCI headless execution, and Cohort A data separation verified. Vehicles departing/arriving $< 200\,\text{s}$ are strictly isolated. |
| **`scenarios/`** | `four_arm.net.xml`<br>`four_arm.edg.xml`<br>`four_arm.nod.xml`<br>`demand/*.rou.xml` | Geometric network (250m arms, 1 lane per arm, 50 km/h) and immutable route files verified. |
| **`results/`** | `final_test_results_per_seed.csv`<br>`final_test_summary.csv`<br>`statistical_primary_waiting_time.csv`<br>`statistical_secondary_metrics.csv`<br>`effect_size_summary.csv` | Confirmed 140 runs across 4 controllers, 7 scenarios, and 5 evaluation seeds (42–46). Data integrity confirmed. |
| **`docs/`** | `frozen_parameters.md`<br>`calibration_report.md`<br>`mathematical_derivation.md`<br>`final_test_evaluation_report.md`<br>`final_statistical_analysis.md` | Verification logs confirmed. Strict separation between calibration seeds (101–104) and blind test seeds (42–46). |

---

## 3. Controller Implementation Audit

### 3.1 C3 — Proposed Adaptive Signal Controller (`controllers/proposed_adaptive_controller.py`)
- **Class**: `ProposedAdaptiveSignalController`
- **Architecture**: A multi-factor state-feedback adaptive controller executing at 1.0 Hz control step intervals.
- **Directional Score Formulation**:
  $$S_d(t) = \alpha \sum_{i \in \text{lanes}(d)} q_i(t) + \beta \sum_{i \in \text{lanes}(d)} a_i(t) + \gamma g_d(t) + \delta \sum_{i \in \text{lanes}(d)} w_i(t) + \eta r_d(t)$$
- **Observed State Variables**:
  1. **Halting Queue $Q_i(t)$**: Observed using `traci.lane.getLastStepHaltingNumber(lane_id)` ($v < 0.1\,\text{m/s}$). Normalized as $q_i(t) = \min(Q_i(t) / Q_{\text{ref}}, 2.0)$ with $Q_{\text{ref}} = 20.0\,\text{veh}$.
  2. **Upstream Inflow / Arrival Rate $A_i(t)$**: Observed by filtering vehicle positions on the 250m link (`traci.vehicle.getLanePosition(v) < 100.0\,\text{m}`), averaged over rolling window $W_A = 20\,\text{s}$, scaled by 10s. Normalized as $a_i(t) = \min(A_i(t) / A_{\text{ref}}, 2.0)$ with $A_{\text{ref}} = 0.40\,\text{veh/s}$.
  3. **Queue Growth $g_d(t)$**: Computed as backward finite difference over window $W_G = 10\,\text{s}$:
     $$g_i(t) = \frac{Q_i(t) - Q_i(t - W_G)}{W_G}$$
     Normalized as $g_i(t) = \max(-1.0, \min(1.0, g_i(t) / G_{\text{ref}}))$ with $G_{\text{ref}} = 0.50\,\text{veh/s}$. Aggregate directional growth is $g_d(t) = \sum_{i \in d} \max(0, g_i(t))$.
  4. **Waiting Burden $W_i(t)$**: Mean accumulated waiting time across halting vehicles:
     $$W_i(t) = \frac{\sum_{v \in \text{halt}} W_{\text{accum}}(v)}{\max(N_{\text{halt}}, 1)}$$
     Normalized as $w_i(t) = \min(W_i(t) / W_{\text{ref}}, 2.0)$ with $W_{\text{ref}} = 30.0\,\text{s}$.
  5. **Continuous Red-Age / Fairness $r_d(t)$**: Cumulative duration that direction $d$ has been continuously red while experiencing an active queue ($Q_d > 0$). Normalized as $r_d(t) = \min(R_d(t) / R_{\text{ref}}, 1.0)$ with $R_{\text{ref}} = 50.0\,\text{s}$.
- **Switching Constraints**:
  - Minimum Green: $G_{\text{min}} = 15\,\text{s}$ (strict hold).
  - Maximum Green: $G_{\text{max}} = 50\,\text{s}$ (forces transition if competing $Q > 0$).
  - Absolute Starvation Ceiling: $R_{\text{starve}} = 45\,\text{s}$ (forces transition if competing $Q > 0$).
  - Hysteresis Barrier: $H = 0.20$. Competing phase triggers yellow transition only when $S_{\text{opp}}(t) > S_{\text{curr}}(t) + H$.
  - Yellow Clearance: $Y = 3\,\text{s}$.

### 3.2 C2 — Basic Queue-Based Adaptive Controller (`controllers/basic_density_controller.py`)
- **Class**: `BasicDensityController`
- **Logic**: Compares real-time queue sums: $D_{\text{NS}} = Q_N + Q_S$ vs $D_{\text{EW}} = Q_E + Q_W$.
- **Switching**: Switches immediately when $D_{\text{opp}} > D_{\text{curr}}$ provided $t_{\text{green}} \ge G_{\text{min}} = 15\,\text{s}$.
- **Absence of Damping**: Contains no hysteresis ($H=0$), no arrival pressure ($\beta=0$), no queue growth tracking ($\gamma=0$), no waiting time weighting ($\delta=0$), and no continuous red aging ($\eta=0$). Contains only binary starvation override at $R_{\text{starve}} = 45\,\text{s}$.

### 3.3 C1 — Webster-Calibrated Fixed-Time Controller (`controllers/optimized_fixed_time_controller.py`)
- **Class**: `OptimizedFixedTimeSignalController`
- **Logic**: Executes a static, pre-timed plan derived from Webster's optimum cycle formula constrained by safety limit $G_{\text{min}} = 15\,\text{s}$:
  - Phase 0 (NS Green): 15 s
  - Phase 1 (NS Yellow): 3 s
  - Phase 2 (EW Green): 15 s
  - Phase 3 (EW Yellow): 3 s
  - Total Cycle Time: 36 s.

### 3.4 C0 — Original Uncalibrated Fixed-Time Controller (`controllers/fixed_time_controller.py`)
- **Class**: `FixedTimeSignalController`
- **Logic**: Executes a conventional static 90-second cycle:
  - Phase 0 (NS Green): 42 s
  - Phase 1 (NS Yellow): 3 s
  - Phase 2 (EW Green): 42 s
  - Phase 3 (EW Yellow): 3 s
  - Total Cycle Time: 90 s.

---

## 4. Parameter Vector Verification

The parameters implemented in `controllers/proposed_adaptive_controller.py` exactly match the frozen specifications established prior to the blind evaluation:

| Parameter | Code Variable | Implemented Value | Physical Meaning & Grounding |
| :--- | :--- | :---: | :--- |
| $\alpha$ | `self.alpha` | 1.00 | Queue anchor weight (fixed baseline reference) |
| $\beta$ | `self.beta` | 0.75 | Upstream arrival pressure weight (clean calibrated) |
| $\gamma$ | `self.gamma` | 0.10 | Queue growth rate weight (architecture audit verified) |
| $\delta$ | `self.delta` | 0.25 | Accumulated waiting burden weight (clean calibrated) |
| $\eta$ | `self.eta` | 0.25 | Continuous red-age fairness weight (clean calibrated) |
| $H$ | `self.hysteresis`| 0.20 | Dimensionless hysteresis switching threshold |
| $Q_{\text{ref}}$ | `self.q_ref` | 20.0 veh | Link capacity scaling ($200\,\text{m} / 10\,\text{m}$ vehicle spacing) |
| $A_{\text{ref}}$ | `self.a_ref` | 0.40 veh/s | $80\%$ of single-lane saturation flow ($1440\,\text{veh/h}$) |
| $W_{\text{ref}}$ | `self.w_ref` | 30.0 s | Highway Capacity Manual (HCM) LOS C delay boundary |
| $R_{\text{ref}}$ | `self.r_ref` | 50.0 s | Maximum green cycle duration ($G_{\text{max}}$) |
| $G_{\text{ref}}$ | `self.g_ref` | 0.50 veh/s | Saturation accumulation rate |
| $W_A$ | `self.w_arrival` | 20 s | Rolling inflow observation window |
| $W_G$ | `self.w_growth` | 10 s | Backward finite-difference queue growth window |
| $G_{\text{min}}$| `self.min_green`| 15 s | NEMA driver safety minimum green constraint |
| $G_{\text{max}}$| `self.max_green`| 50 s | NEMA maximum green hold ceiling |
| $Y$ | `self.yellow_time`| 3 s | Yellow change clearance interval |
| $R_{\text{starve}}$| `self.starvation_red_time`| 45 s | Absolute red starvation override ceiling |

---

## 5. SUMO Simulation Environment & Sensing Audit

### 5.1 Sensing Modality: Software TraCI Interface Only
> [!IMPORTANT]
> **No Hardware Claim Certification:**  
> The research was conducted exclusively in a microscopic simulation environment using Eclipse SUMO and the TraCI Python API.  
> - **NO** physical hardware cameras, inductive loops, radar, ultrasonic sensors, or microcontrollers (e.g., ESP32, Arduino) were deployed.  
> - All traffic state measurements originate from TraCI function calls (`lane.getLastStepHaltingNumber`, `lane.getLastStepVehicleIDs`, `vehicle.getLanePosition`, `vehicle.getAccumulatedWaitingTime`).  
> - Any discussion of physical sensors in the paper is strictly categorized under "Potential Real-World Deployment Architecture" as future research.

### 5.2 Network Geometry & Simulation Execution
- **Network File**: `scenarios/four_arm.net.xml`
- **Intersection Type**: Isolated 4-arm orthogonal intersection (`J0`).
- **Arm Dimensions**: 250 meters length per approach link.
- **Lane Configuration**: 1 incoming lane and 1 outgoing lane per arm.
- **Speed Limit**: $13.89\,\text{m/s}$ ($50\,\text{km/h}$).
- **Simulation Duration**: $1000\,\text{s}$ per run.
- **Warm-Up Duration**: $200\,\text{s}$ (Cohort A evaluation window: $200\text{--}1000\,\text{s}$).
- **Step Length**: $1.0\,\text{s}$ discrete simulation step.

---

## 6. Experimental Evaluation Matrix

- **Total Runs**: $4\text{ controllers} \times 7\text{ scenarios} \times 5\text{ seeds} = 140\text{ simulation runs}$.
- **Evaluation Seeds**: $k \in \{42, 43, 44, 45, 46\}$.
- **Scenarios**:
  1. `low`: Balanced demand, $p = 0.04$ per lane ($144\,\text{veh/h/lane}$).
  2. `medium`: Balanced demand, $p = 0.08$ per lane ($288\,\text{veh/h/lane}$).
  3. `high`: Balanced demand, $p = 0.14$ per lane ($504\,\text{veh/h/lane}$).
  4. `oversaturated`: Balanced demand exceeding capacity, $p = 0.18$ per lane ($648\,\text{veh/h/lane}$).
  5. `asym_ns`: Major arterial flow NS ($p_{\text{NS}} = 0.14$), minor EW ($p_{\text{EW}} = 0.03$).
  6. `asym_ew`: Major arterial flow EW ($p_{\text{EW}} = 0.14$), minor NS ($p_{\text{NS}} = 0.03$).
  7. `dynamic`: Three-phase surge demand ($0\text{--}300\,\text{s}: p=0.04 \rightarrow 300\text{--}700\,\text{s}: p=0.15 \rightarrow 700\text{--}1000\,\text{s}: p=0.05$).

---

## 7. Supported vs. Prohibited Claims Audit

Based on the verified results in `results/statistical_primary_waiting_time.csv` and `docs/final_statistical_analysis.md`:

### 7.1 Strictly Supported Scientific Claims
1. **Asymmetric Demand Superiority over Fixed Time**: C3 reduces waiting time by **$61.6\%$ to $63.2\%$** relative to Webster-calibrated fixed-time (C1) in directional asymmetry (`asym_ns` and `asym_ew`), supported under Benjamini-Hochberg FDR control ($q < 0.04$).
2. **Universal Phase-Switching Stabilization**: Across all 7 scenarios, C3 executes **$4.6\%$ to $20.3\%$ fewer phase switches** than naive queue control C2 ($p < 0.028$ in all scenarios) and **$9.5\%$ to $46.5\%$ fewer phase switches** than fixed-time C1 ($p < 0.015$ in all scenarios). This proves that the composite objective's smoothing and hysteresis terms prevent erratic phase hunting.
3. **Overwhelming Superiority over Uncalibrated Long-Cycle Fixed Time**: C3 outperforms 90-second uncalibrated fixed-time C0 across all scenarios (reductions of $17.8\%$ to $81.5\%$).
4. **Computational Feasibility**: Average per-step decision time is under $0.5\,\text{ms}$, well within the 1000 ms real-time control budget.

### 7.2 Prohibited Overclaims (Must NOT appear in manuscript)
1. **NO Universal Superiority**: C3 is **not** superior in all scenarios. In symmetric steady-state regimes (`medium` and `high`), Webster-calibrated fixed-time C1 achieves lower waiting times ($14.9\%$ to $26.4\%$ lower) because zero-detector 36-second cycles avoid green extension latency.
2. **NO Statistically Significant Waiting-Time Reduction over C2**: While C3 achieves directional waiting-time reductions of $17.3\%$ to $31.2\%$ in asymmetric demand against C2, these differences do not survive multiple-comparison correction at $N=5$ ($q_{\text{BH}} \ge 0.24$). C3's supported advantage over C2 is signal stability (switching reduction), not waiting-time dominance.
3. **NO Claim of "Solving" Oversaturation**: When demand exceeds intersection capacity ($p=0.18$), queues grow continuously under all controllers; C3 maintains stability and prevents gridlock, but cannot eliminate physical oversaturation.
4. **NO Hyperbolic Terminology**: Terms such as "optimal", "revolutionary", "state-of-the-art", "eliminates congestion", or "first-ever" are strictly prohibited.

---

## 8. Certification Sign-Off

The undersigned audit confirms that the codebase and output data are 100% frozen, verified, and ready for publication synthesis.

**Lead Auditor**: Antigravity Autonomous Research Agent  
**Date**: October 2026  
**Status**: APPROVED FOR JITS SUBMISSION PACKAGE CREATION
