# Comprehensive Audit Report: Existing Signal Control Implementation & Methodology

**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Scope**: Full evaluation of `controllers/`, `simulation/runner.py`, `scripts/generate_routes.py`, `scripts/run_baseline_experiments.py`, `scripts/run_density_experiments.py`, and generated data files.

---

## Executive Summary

Before implementing or proposing any adaptive signal controller, a rigorous audit of the existing baseline implementation was conducted. The audit revealed five critical methodological issues in the legacy codebase:
1. **Terminology Misnomer**: Halting vehicle count was mislabeled as "spatial traffic density" ($\text{veh/km}$ or $\text{veh/m}$).
2. **Warm-up Boundary Bleed**: Vehicles that departed during the warm-up period ($t < 200\text{s}$) had their pre-warmup queue waiting times accumulated and averaged into post-warmup evaluation metrics.
3. **Traffic Demand Coupling / Overwriting**: The legacy scripts regenerated route files dynamically at runtime, causing potential demand discrepancy between controllers and overwriting baseline route realizations.
4. **Asymmetric Demand Inconsistency**: Directional asymmetry scenarios were poorly specified with ad-hoc multipliers rather than controlled directional Poisson flow rates.
5. **Degradation Under Saturation**: The simple queue-comparison controller degraded significantly under saturated flow ($p \ge 0.18$) because both opposing approaches remained perpetually occupied, causing the controller to alternate continuously between max-green limits with heavy yellow lost-time penalties.

---

## Point-by-Point Audit Findings

### 1. Exact Definition of Queue Length
- **Implementation**: `traci.lane.getLastStepHaltingNumber(lane_id)`
- **Mathematical Definition**: $Q_i(t) = \sum_{v \in \mathcal{L}_i(t)} \mathbb{I}(u_v(t) < 0.1 \text{ m/s})$, where $\mathcal{L}_i(t)$ is the set of vehicles on lane $i$ and $u_v(t)$ is vehicle speed.
- **Physical Meaning**: Count of stationary or near-stationary vehicles ($u < 0.1\text{ m/s}$) on the approach lane.
- **Finding**: The metric is valid for halting queue length, but does NOT include slow decelerating vehicles ($0.1 \le u < 1.0\text{ m/s}$) joining the back of the queue.

### 2. Whether the Term "Density" is Technically Appropriate
- **Finding**: **Technically Inappropriate.**
- **Rationale**: In fundamental traffic flow theory (Lighthill–Whitham–Richards), traffic density $k$ is defined as vehicle count per unit distance:
  $$k_i(t) = \frac{N_i(t)}{L_i} \quad [\text{veh/km or veh/m}]$$
  The legacy codebase used $D_{NS} = Q_N + Q_S$ (an unnormalized integer vehicle count) and termed it "density". 
- **Corrective Action**: The term has been corrected to **"queue length"** or **"queue-demand adaptive control"**. True spatial density is defined as $\rho_i(t) = N_i(t) / L_i$.

### 3. Exact Definition of Waiting Time
- **Implementation**: `traci.vehicle.getAccumulatedWaitingTime(v)`
- **Mathematical Definition**: $W_v = \sum_{t=t_{\text{dep}}}^{t_{\text{arr}}} \mathbb{I}(u_v(t) < 0.1 \text{ m/s}) \cdot \Delta t$
- **Finding**: Accumulated waiting time counts all seconds a vehicle spent with speed $< 0.1\text{ m/s}$. However, in the legacy runner, vehicles departing at $t < 200\text{s}$ carried their pre-warmup waiting time into the post-warmup evaluation average.

### 4. Exact Definition of Travel Time
- **Implementation**: $T_v = t_{\text{arrival}} - t_{\text{depart}}$
- **Mathematical Definition**: Total elapsed seconds from insertion into the network to completion at the boundary edge.
- **Finding**: Unambiguous and exact for completed vehicles.

### 5. Exact Definition of Delay / Time Loss
- **Implementation**: `traci.vehicle.getTimeLoss(v)`
- **Mathematical Definition**: $d_v = T_v - \frac{L_v}{u_{\text{max}}}$, the difference between actual travel time and free-flow travel time.
- **Finding**: SUMO's `getTimeLoss` tracks time lost due to deceleration, signal waiting, and car-following below desired speed. This is the gold-standard delay metric in traffic engineering.

### 6. Exact Definition of Throughput
- **Implementation**: Count of completed vehicles during the evaluation period.
- **Finding**: In the legacy runner, throughput mixed vehicles that departed before warm-up with vehicles that departed during warm-up.

### 7. Exact Definition of Stops
- **Implementation**: Tracked via speed threshold transitions ($u(t) \ge 0.1 \rightarrow u(t) < 0.1$).
- **Finding**: Accurately counts individual stopping events per vehicle.

### 8. Warm-up / Evaluation Methodology
- **Implementation**: Total duration $1000\text{s}$, warm-up duration $200\text{s}$, evaluation duration $800\text{s}$.
- **Finding**: Warm-up duration of $200\text{s}$ is adequate for the 200m approach links (free-flow traversal time $\approx 15\text{s}$). However, data isolation at the boundary was flawed.

### 9. How Vehicles Crossing the Warm-up Boundary are Treated
- **Legacy Issue**: Vehicles entering at $t=180\text{s}$ and leaving at $t=230\text{s}$ were grouped with vehicles departing at $t=250\text{s}$.
- **Resolution**: Strict cohort isolation has been implemented:
  - **Cohort A (Pure Evaluation)**: $t_{\text{depart}} \ge 200\text{s} \land t_{\text{arrive}} \ge 200\text{s}$. (Primary research cohort).
  - **Cohort B (Boundary Crossing)**: $t_{\text{depart}} < 200\text{s} \land t_{\text{arrive}} \ge 200\text{s}$.
  - **Cohort C (Pure Warm-up)**: $t_{\text{depart}} < 200\text{s} \land t_{\text{arrive}} < 200\text{s}$.

### 10. Signal-Phase Transition Logic
- **Phases**:
  - Phase 0: North-South Green (`GGgrrrGGgrrr`)
  - Phase 1: North-South Yellow (`yyyrrryyyrrr`, duration 3s)
  - Phase 2: East-West Green (`rrrGGgrrrGGg`)
  - Phase 3: East-West Yellow (`rrryyyrrryyy`, duration 3s)
- **Finding**: Phase transition is safe and follows NEMA clearance standards with 3s yellow.

### 11. Minimum Green Implementation
- **Value**: $G_{\text{min}} = 15\text{s}$.
- **Mechanism**: Controller is locked in active green phase until $t_{\text{elapsed}} \ge G_{\text{min}}$.
- **Finding**: Effectively prevents driver confusion and phase oscillation.

### 12. Maximum Green Implementation
- **Value**: $G_{\text{max}} = 50\text{s}$.
- **Mechanism**: If $t_{\text{elapsed}} \ge G_{\text{max}}$ and opposing queue $> 0$, phase switch is forced.
- **Finding**: Functional, but under oversaturation it causes cyclic alternation at 50s + 3s yellow, degenerating into an inefficient fixed-time controller.

### 13. Starvation Prevention Implementation
- **Value**: $R_{\text{starve}} = 45\text{s}$.
- **Mechanism**: Hard threshold: if opposing red time $\ge 45\text{s}$ while holding queued vehicles, a switch is triggered as soon as $G_{\text{min}}$ is met.
- **Finding**: Hard switching creates abrupt transitions; a continuous fairness term $F_p(t) = \eta (R_p / R_{\text{ref}})$ provides smoother phase allocation.

### 14. Whether All Traffic Demand is Identical Between Controllers
- **Legacy Issue**: Legacy experiment runners regenerated route files on-the-fly (`python generate_routes.py`), risking subtle divergence if parameters or seed calls differed.
- **Corrected Architecture**: **ONE TRAFFIC REALIZATION $\rightarrow$ MULTIPLE CONTROLLERS.** 37 static, immutable XML route files pre-generated in `scenarios/demand/` and shared across all controllers.

### 15. Whether Random Seeds are Actually Deterministic
- **Finding**: Deterministic. SUMO's internal Mersenne Twister seed (`--seed <val>`) together with Python's `random.seed(<val>)` produce bit-for-bit identical vehicle trajectories when given the same route file.

### 16. Asymmetric Demand Generation
- **Legacy Issue**: Asymmetric tests were generated by scaling global parameters rather than specifying dedicated directional arrival rates.
- **Corrected Architecture**: Dedicated Poisson probabilities:
  - Asymmetric NS: $p_{NS} = 0.14, p_{EW} = 0.03$ (Arterial NS, minor street EW).
  - Asymmetric EW: $p_{NS} = 0.03, p_{EW} = 0.14$ (Arterial EW, minor street NS).

### 17. Result File Overwriting
- **Legacy Issue**: `data/baseline_seed42_summary.csv` was repeatedly overwritten by subsequent scripts.
- **Corrected Architecture**: All experimental suites write to distinct, timestamped/versioned files in `results/` (`multi_demand_comparison_results.csv`, `ablation_study_results.csv`, etc.).

### 18. Methodological Problems Fixed Before Final Paper
- Replaced misnomer "density" with "queue length / queue demand".
- Isolated Cohort A from Cohort B.
- Implemented static immutable demand pipeline.
- Added systematic ablation study (Models 0–6).
- Added multi-seed matched-pair statistical testing.
- Added sensor noise robustness and parameter sensitivity analysis.
