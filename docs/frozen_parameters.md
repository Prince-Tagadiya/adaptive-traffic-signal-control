# Frozen Controller Parameters

**Status:** ALL PARAMETERS AND ARCHITECTURAL WEIGHTS STRICTLY FROZEN  
**Freezing Timestamp:** 2026-10-04T12:58:00  
**Target Evaluation Set:** Blind Test Set (Seeds 42–46)  
**Exposure to Test Set During Calibration & Architecture Audit:** ZERO  

---

## 1. Human-Readable Specification Table

| Parameter | Value | Unit | Source | Selection Method | Frozen Before Test? |
| :--- | :---: | :---: | :--- | :--- | :---: |
| **`alpha`** | `1.00` | dimensionless | Theoretical Control Formulation | Fixed Anchor (Primary Queue Pressure) | **YES** |
| **`beta`** | `0.75` | dimensionless | Clean Calibration Suite (Seeds 101–104) | Pre-declared Loss $J(\theta)$ & Tie-Breaker | **YES** |
| **`gamma`** | `0.10` | dimensionless | Clean Calibration Suite Architecture Audit | Bounded Grid $\gamma \in \{0.0, 0.1, 0.2, 0.3\}$ on Seeds 101–104: $\Delta J = -5.7\%$ | **YES** |
| **`delta`** | `0.25` | dimensionless | Clean Calibration Suite (Seeds 101–104) | Pre-declared Loss $J(\theta)$ & Tie-Breaker | **YES** |
| **`eta`** | `0.25` | dimensionless | Clean Calibration Suite (Seeds 101–104) | Pre-declared Loss $J(\theta)$ & Tie-Breaker | **YES** |
| **`H`** | `0.20` | dimensionless | Clean Calibration Suite (Seeds 101–104) | Pre-declared Loss $J(\theta)$ & Tie-Breaker | **YES** |
| **`Q_ref`** | `20.0` | vehicles | Physical Approach Geometry | Derived: Link length $200\,\text{m}$ / $10\,\text{m}$ jam spacing (Class A) | **YES** |
| **`A_ref`** | `0.40` | vehicles / second | Highway Capacity Theory | Derived: 80% Saturation Flow $1440\,\text{veh/h}$ (Class A) | **YES** |
| **`W_ref`** | `30.0` | seconds | Highway Capacity Manual (HCM 2016) | Standard Practice: HCM Level of Service C Boundary (Class C Rule) | **YES** |
| **`R_ref`** | `50.0` | seconds | Signal Timing Engineering Bounds | Constraint: Matched to Max Green $G_{\text{max}} = 50\,\text{s}$ (Class B) | **YES** |
| **`W_A`** | `20.0` | seconds | Approach Kinematics | Derived: Physical link travel time $200\,\text{m} / 13.89\,\text{m/s} \approx 14.4\,\text{s} \rightarrow 20\,\text{s}$ (Class A) | **YES** |
| **`W_G`** | `10.0` | seconds | Discrete Derivative Window | Standard Practice: 10s backward difference for queue rate estimation | **YES** |
| **`G_ref`** | `0.50` | vehicles / second | Saturation Discharge Flow | Derived: Single-lane saturation accumulation limit (Class A) | **YES** |
| **`G_min`** | `15.0` | seconds | NEMA / MUTCD Standards | Structural Safety: Minimum Driver Expectancy & Pedestrian Crossing (Class B) | **YES** |
| **`G_max`** | `50.0` | seconds | NEMA / MUTCD Standards | Structural Safety: Maximum Arterial Holding Cap (Class B) | **YES** |
| **`R_starve`** | `45.0` | seconds | Signal Control Safety Standards | Structural Safety: Red Phase Starvation Ceiling (Class B) | **YES** |
| **`yellow`** | `3.0` | seconds | ITE Kinematic Clearance Formula | Structural Safety: Urban Approach Clearance Interval (Class B) | **YES** |

---

## 2. Objective Function Normalization Audit

The multi-objective calibration function is:
$$J(\theta) = 0.70 \cdot \left(\frac{\bar{W}(\theta)}{W_{\text{target}}}\right) + 0.20 \cdot \left(\frac{\bar{Y}(\theta)}{Y_{\text{target}}}\right) + 0.10 \cdot \left(\frac{\bar{S}(\theta)}{S_{\text{target}}}\right)$$

The normalization denominators are explicitly classified as **engineering normalization constants**:
- **$W_{\text{target}} = 25.0\,\text{s}$**: Engineering benchmark reflecting the HCM 2016 Level of Service C delay threshold for urban signalized intersections.
- **$Y_{\text{target}} = 150.0\,\text{s}$**: Engineering benchmark for clearance capacity loss (15% of 1000s simulation time; $50\text{ switches} \times 3\text{s yellow}$).
- **$S_{\text{target}} = 100.0\,\text{switches}$**: Engineering ceiling for maximum acceptable switching churn ($0.1\text{ switches/second}$).

**Integrity Audit Confirmation:** These values were fixed directly in the simulation runner and evaluation scripts prior to running any candidate simulations. They were not chosen or tuned post-hoc by observing which values favoured particular candidates.

---

## 3. Machine-Readable Configuration (JSON)

```json
{
  "calibration_metadata": {
    "status": "FROZEN",
    "calibration_seeds": [101, 102, 103, 104],
    "test_seeds_excluded": [42, 43, 44, 45, 46],
    "engineering_normalization_constants": {
      "W_target_s": 25.0,
      "Y_target_s": 150.0,
      "S_target_switches": 100.0
    },
    "loss_formula": "0.70*(mean_wait/25.0) + 0.20*(mean_yellow/150.0) + 0.10*(mean_switches/100.0)",
    "predeclared_tie_break": "1. Lower J; 2. Within 1% -> lower switches; 3. Lower aux weight sum; 4. Smaller H",
    "architecture_audit": {
      "gamma_candidates_tested": [0.0, 0.1, 0.2, 0.3],
      "gamma_selected": 0.1,
      "gamma_selection_rationale": "J reduced from 0.91379 to 0.86146 (-5.7%) with 6.01s wait reduction in high demand and no regime degradation"
    },
    "final_candidate_id": "CFG_094_gamma0.10",
    "final_composite_J": 0.86146,
    "date_frozen": "2026-10-04T12:58:00"
  },
  "controller_parameters": {
    "alpha": 1.0,
    "beta": 0.75,
    "gamma": 0.1,
    "delta": 0.25,
    "eta": 0.25,
    "hysteresis": 0.2,
    "q_ref": 20.0,
    "a_ref": 0.4,
    "w_ref": 30.0,
    "r_ref": 50.0,
    "w_arrival": 20,
    "w_growth": 10,
    "g_ref": 0.5,
    "min_green": 15,
    "max_green": 50,
    "starvation_red_time": 45,
    "yellow_time": 3,
    "noise_std": 0.0
  }
}
```

---

## 4. Strict Pre-Test Commitment

The parameter configuration above is **completely frozen**. Under NO circumstances may any of the above parameters be modified, tuned, or re-selected after evaluating the blind test suite (seeds 42–46). If performance issues or unexpected failures arise on the test set, they will be reported honestly as findings rather than solved via post-hoc adjustments.
