# Research Tables: Adaptive Signal Control Experimental Results

**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Project**: Adaptive Traffic Signal Control using SUMO, Python, and TraCI

---

## Table 1: Simulation Network and Traffic Parameters
| Parameter | Value | Description / Unit |
| :--- | :--- | :--- |
| Network Topology | Isolated 4-Arm Intersection | Orthogonal 90° planar junction (Junction ID: `J0`) |
| Approach Arm Length ($L_i$) | 200 m | Approach links: `N_J0_0`, `S_J0_0`, `E_J0_0`, `W_J0_0` |
| Lanes per Approach | 1 lane per arm | Dedicated movement lanes |
| Maximum Allowed Speed | 13.89 m/s (50 km/h) | Urban standard arterial speed limit |
| Vehicle Length | 5.0 m | Default passenger car type |
| Minimum Gap | 2.5 m | Jam spacing gap at standstill |
| Car-Following Model | Krauss | Default SUMO car-following model |
| Max Acceleration / Deceleration | 2.6 m/s² / 4.5 m/s² | Standard passenger vehicle physical limits |
| Driver Imperfection ($\sigma$) | 0.5 | Stochastic driving behavior parameter |
| Simulation Step ($\Delta t$) | 1.0 s | Discrete time step |
| Total Simulation Duration ($T_{\text{sim}}$) | 1,000 s | Total simulated seconds per experiment |
| Warm-up Duration ($T_{\text{warmup}}$) | 200 s | Network loading period before evaluation |
| Evaluation Duration ($T_{\text{eval}}$) | 800 s | Pure post-warmup evaluation window |
| Random Seeds Evaluated | 42, 43, 44, 45, 46 | 5 independent stochastic realisations per condition |

---

## Table 2: Signal Controller Specifications & Parameters
| Parameter / Constant | Symbol | Value | Unit | Definition |
| :--- | :--- | :--- | :--- | :--- |
| Minimum Green Time | $G_{\text{min}}$ | 15 | s | Minimum duration phase is guaranteed to hold |
| Maximum Green Time | $G_{\text{max}}$ | 50 | s | Maximum phase hold before mandatory release |
| Yellow Clearance Time | $Y$ | 3 | s | Safety clearance interval between phases |
| Starvation Threshold | $R_{\text{starve}}$ | 45 | s | Red time ceiling triggering mandatory switch |
| Arrival Window | $W_A$ | 20 | s | Rolling history window for arrival estimation |
| Queue Growth Window | $W_G$ | 10 | s | Finite-difference window for queue derivative |
| Queue Weight | $\alpha$ | 1.0 | — | Weight for normalized queue length $q_p$ |
| Arrival Rate Weight | $\beta$ | 0.5 | — | Weight for normalized arrival rate $a_p$ |
| Queue Growth Weight | $\gamma$ | 0.3 | — | Weight for positive queue growth $g_p$ |
| Waiting Burden Weight | $\delta$ | 0.4 | — | Weight for average waiting burden $w_p$ |
| Continuous Fairness Weight | $\eta$ | 0.4 | — | Weight for continuous red aging $r_p$ |
| Switching Hysteresis Margin | $H$ | 0.25 | — | Dimensionless threshold: switch if $S_{\text{other}} > S_{\text{active}} + H$ |
| Queue Normalization Ref. | $Q_{\text{ref}}$ | 20.0 | veh | Characteristic approach queue capacity |
| Arrival Normalization Ref. | $A_{\text{ref}}$ | 0.40 | veh/s | Characteristic approach inflow rate |
| Growth Normalization Ref. | $G_{\text{ref}}$ | 0.50 | veh/s | Characteristic queue expansion rate |
| Waiting Normalization Ref. | $W_{\text{ref}}$ | 30.0 | s | Characteristic waiting burden threshold |
| Red Age Normalization Ref. | $R_{\text{ref}}$ | 50.0 | s | Characteristic cycle red time |

---

## Table 3: Experimental Scenario Definitions
| Scenario Name | Description | Flow Probabilities ($p$) | Inflow per Arm | Total Inflow Rate |
| :--- | :--- | :--- | :--- | :--- |
| `low` | Light, uncongested flow | $p = 0.04$ | ~144 veh/h/arm | ~576 veh/h |
| `medium` | Moderate urban demand | $p = 0.08$ | ~288 veh/h/arm | ~1,152 veh/h |
| `high` | Heavy saturated flow | $p = 0.14$ | ~504 veh/h/arm | ~2,016 veh/h |
| `oversaturated` | Congested over-capacity | $p = 0.18$ | ~648 veh/h/arm | ~2,592 veh/h |
| `asym_ns` | Major North-South arterial | $p_{NS}=0.14, p_{EW}=0.03$ | NS: 504, EW: 108 veh/h | ~1,224 veh/h |
| `asym_ew` | Major East-West arterial | $p_{NS}=0.03, p_{EW}=0.14$ | NS: 108, EW: 504 veh/h | ~1,224 veh/h |
| `dynamic` | Temporal surging demand | Step-wise fluctuating $p(t)$ | Time-varying | ~1,300 veh/h avg |

---

## Table 4: Baseline Performance (Fixed-Time vs Basic Queue-Based)
*Metrics reported as Mean ± Standard Deviation over 5 random seeds (Cohort A: Pure Evaluation Cohort).*

| Scenario | Controller | Avg Wait (s) | Avg Delay (s) | Avg Queue (veh) | Throughput (veh) | Switches | Yellow Time (s) | Max Red (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Low** | Fixed-Time | 11.94 ± 0.74 | 18.23 ± 0.76 | 1.55 ± 0.10 | 108.6 ± 7.9 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 4.29 ± 0.28 | 9.77 ± 0.35 | 0.57 ± 0.04 | 108.8 ± 7.9 | 81.2 ± 3.4 | 121.8 ± 5.1 | 64.6 ± 15.6 |
| **Medium** | Fixed-Time | 16.40 ± 2.19 | 25.12 ± 2.45 | 4.09 ± 0.74 | 213.6 ± 12.3 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 6.81 ± 0.76 | 14.15 ± 0.78 | 1.83 ± 0.24 | 215.8 ± 12.7 | 100.8 ± 2.7 | 151.2 ± 4.0 | 68.4 ± 11.0 |
| **High** | Fixed-Time | 75.62 ± 13.91 | 108.95 ± 14.28 | 32.55 ± 5.09 | 363.0 ± 8.8 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 44.91 ± 6.64 | 88.08 ± 7.15 | 23.51 ± 2.65 | 371.8 ± 12.1 | 107.0 ± 2.0 | 160.8 ± 2.9 | 53.0 ± 2.0 |
| **Oversat.** | Fixed-Time | 86.61 ± 13.88 | 118.99 ± 14.17 | 40.54 ± 4.34 | 433.8 ± 12.1 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 71.18 ± 10.45 | 117.84 ± 10.63 | 38.64 ± 3.84 | 443.0 ± 11.8 | 105.8 ± 2.7 | 158.4 ± 4.1 | 55.4 ± 12.7 |
| **Asym-NS** | Fixed-Time | 59.55 ± 4.15 | 73.13 ± 4.25 | 18.00 ± 1.63 | 243.6 ± 11.2 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 16.17 ± 5.37 | 25.56 ± 5.64 | 4.88 ± 1.70 | 250.2 ± 11.7 | 78.4 ± 3.6 | 117.6 ± 5.4 | 119.8 ± 11.5 |
| **Asym-EW** | Fixed-Time | 67.51 ± 6.13 | 82.52 ± 6.18 | 20.67 ± 1.83 | 240.8 ± 13.0 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 18.17 ± 7.08 | 27.67 ± 7.37 | 5.36 ± 2.24 | 246.6 ± 14.1 | 82.6 ± 6.2 | 123.9 ± 9.3 | 113.8 ± 10.1 |
| **Dynamic** | Fixed-Time | 58.54 ± 6.64 | 74.96 ± 6.81 | 18.25 ± 2.45 | 250.6 ± 13.4 | 44.0 ± 0.0 | 66.0 ± 0.0 | 45.0 ± 0.0 |
| | Basic-Queue | 31.21 ± 5.91 | 43.83 ± 6.18 | 9.42 ± 1.95 | 257.4 ± 13.2 | 87.8 ± 5.8 | 131.7 ± 8.8 | 84.4 ± 7.5 |

---

## Table 5: Proposed Controller Performance
*Metrics reported as Mean ± Standard Deviation over 5 random seeds (Cohort A).*

| Scenario | Controller | Avg Wait (s) | Avg Delay (s) | Avg Queue (veh) | Throughput (veh) | Switches | Yellow Time (s) | Max Red (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Low** | Proposed | 4.54 ± 0.31 | 10.02 ± 0.35 | 0.60 ± 0.05 | 108.8 ± 7.9 | 74.8 ± 2.7 | 112.2 ± 4.0 | 66.0 ± 5.1 |
| **Medium** | Proposed | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 215.8 ± 12.7 | 97.6 ± 2.2 | 146.4 ± 3.3 | 68.6 ± 7.6 |
| **High** | Proposed | 45.99 ± 9.39 | 89.11 ± 9.61 | 24.33 ± 4.06 | 371.4 ± 12.1 | 105.0 ± 2.8 | 157.8 ± 4.2 | 53.6 ± 7.3 |
| **Oversat.** | Proposed | 70.84 ± 8.16 | 117.47 ± 8.35 | 38.62 ± 3.03 | 443.0 ± 11.8 | 106.6 ± 2.1 | 160.2 ± 3.1 | 55.4 ± 10.6 |
| **Asym-NS** | Proposed | 15.72 ± 6.42 | 25.10 ± 6.70 | 4.81 ± 2.05 | 250.2 ± 11.7 | 78.4 ± 4.4 | 117.6 ± 6.6 | 119.8 ± 13.7 |
| **Asym-EW** | Proposed | 13.34 ± 5.86 | 22.86 ± 6.13 | 4.14 ± 1.94 | 246.6 ± 14.1 | 82.2 ± 5.1 | 123.3 ± 7.6 | 112.4 ± 13.6 |
| **Dynamic** | Proposed | 28.94 ± 6.11 | 41.52 ± 6.36 | 8.89 ± 2.01 | 257.6 ± 13.3 | 87.2 ± 4.3 | 130.8 ± 6.4 | 86.4 ± 10.6 |

---

## Table 6: Component Ablation Study Results
*Evaluated across 5 random seeds on Medium and High demand scenarios.*

| Scenario | Model ID | Components Included | Avg Wait (s) | Avg Delay (s) | Avg Queue (veh) | Phase Switches | Yellow Lost Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Medium** | Model 0 | Fixed-Time (Plan) | 16.40 ± 2.19 | 25.12 ± 2.45 | 4.09 ± 0.74 | 44.0 ± 0.0 | 66.0 ± 0.0 |
| | Model 1 | Queue Only ($Q$) | 6.72 ± 0.94 | 14.06 ± 0.95 | 1.83 ± 0.31 | 100.8 ± 1.8 | 151.2 ± 2.7 |
| | Model 2 | Queue + Arrival ($Q+A$) | 7.14 ± 1.09 | 14.25 ± 1.13 | 1.95 ± 0.33 | 93.2 ± 2.7 | 139.8 ± 4.0 |
| | Model 3 | $Q+A$ + Growth ($G$) | 7.52 ± 1.12 | 14.99 ± 1.14 | 2.10 ± 0.36 | 96.8 ± 3.3 | 145.2 ± 5.0 |
| | Model 4 | $Q+A+G$ + Waiting ($W$) | 6.64 ± 0.81 | 14.07 ± 0.82 | 1.87 ± 0.28 | 102.0 ± 2.8 | 153.0 ± 4.2 |
| | Model 5 | Above + Fairness ($R$) | 6.95 ± 0.79 | 14.45 ± 0.80 | 1.95 ± 0.27 | 104.0 ± 2.4 | 156.0 ± 3.7 |
| | Model 6 | Full Proposed (+ Hysteresis $H$) | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 | 146.4 ± 3.3 |
| **High** | Model 0 | Fixed-Time (Plan) | 75.62 ± 13.91 | 108.95 ± 14.28 | 32.55 ± 5.09 | 44.0 ± 0.0 | 66.0 ± 0.0 |
| | Model 1 | Queue Only ($Q$) | 45.69 ± 8.01 | 89.32 ± 8.28 | 24.16 ± 3.57 | 107.4 ± 1.3 | 161.1 ± 2.0 |
| | Model 2 | Queue + Arrival ($Q+A$) | 47.91 ± 10.37 | 92.52 ± 10.59 | 25.10 ± 4.38 | 101.4 ± 3.8 | 152.1 ± 5.8 |
| | Model 3 | $Q+A$ + Growth ($G$) | 50.50 ± 12.01 | 97.91 ± 12.18 | 26.66 ± 5.05 | 104.0 ± 5.1 | 156.0 ± 7.7 |
| | Model 4 | $Q+A+G$ + Waiting ($W$) | 46.36 ± 9.38 | 90.80 ± 9.58 | 24.58 ± 4.09 | 107.0 ± 2.8 | 160.5 ± 4.2 |
| | Model 5 | Above + Fairness ($R$) | 45.97 ± 8.35 | 90.89 ± 8.57 | 24.47 ± 3.65 | 108.4 ± 0.9 | 162.6 ± 1.3 |
| | Model 6 | Full Proposed (+ Hysteresis $H$) | 45.99 ± 9.39 | 89.11 ± 9.61 | 24.33 ± 4.06 | 105.0 ± 2.8 | 157.8 ± 4.2 |

---

## Table 7: Parameter Sensitivity Analysis
*Sweeps conducted on Medium demand across 5 random seeds.*

| Parameter Tested | Tested Values | Avg Waiting Time (s) | Avg Delay (s) | Avg Queue (veh) | Switch Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Minimum Green ($G_{\text{min}}$)** | 10 s | 6.37 ± 1.15 | 13.62 ± 1.19 | 1.83 ± 0.38 | 114.4 ± 3.6 |
| | 15 s (Nominal) | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 |
| | 20 s | 9.21 ± 2.74 | 16.92 ± 2.84 | 2.58 ± 0.76 | 76.8 ± 4.0 |
| **Maximum Green ($G_{\text{max}}$)** | 35 s | 6.52 ± 1.03 | 13.93 ± 1.07 | 1.87 ± 0.35 | 98.8 ± 3.3 |
| | 50 s (Nominal) | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 |
| | 70 s | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 |
| **Hysteresis ($H$)** | 0.00 | 6.95 ± 1.19 | 14.18 ± 1.23 | 1.95 ± 0.36 | 103.6 ± 3.0 |
| | 0.15 | 6.89 ± 1.13 | 14.13 ± 1.17 | 1.94 ± 0.34 | 100.8 ± 2.5 |
| | 0.25 (Nominal) | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 |
| | 0.40 | 7.26 ± 1.01 | 14.61 ± 1.05 | 2.06 ± 0.32 | 92.4 ± 2.9 |
| **Arrival Window ($W_A$)** | 10 s | 7.23 ± 1.17 | 14.54 ± 1.20 | 2.04 ± 0.36 | 98.4 ± 3.4 |
| | 20 s (Nominal) | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 97.6 ± 2.2 |
| | 30 s | 6.82 ± 1.26 | 14.09 ± 1.30 | 1.94 ± 0.39 | 97.2 ± 3.8 |

---

## Table 8: Robustness to Sensor Measurement Noise
*Proposed controller evaluated under zero-mean Gaussian noise on approach queue measurements.*

| Scenario | Noise $\sigma$ (veh) | Avg Wait (s) | Avg Delay (s) | Avg Queue (veh) | Throughput (veh) | Switches |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Medium** | $\sigma = 0.0$ | 6.77 ± 0.83 | 14.06 ± 0.84 | 1.93 ± 0.31 | 215.8 ± 12.7 | 97.6 ± 2.2 |
| | $\sigma = 1.0$ | 6.64 ± 0.64 | 14.07 ± 0.67 | 1.89 ± 0.22 | 215.8 ± 12.7 | 98.4 ± 2.3 |
| | $\sigma = 2.0$ | 8.23 ± 3.07 | 15.65 ± 3.09 | 2.31 ± 0.81 | 215.6 ± 12.8 | 98.8 ± 4.3 |
| | $\sigma = 3.0$ | 6.57 ± 0.91 | 14.05 ± 0.94 | 1.92 ± 0.32 | 215.8 ± 12.7 | 98.8 ± 3.9 |
| **High** | $\sigma = 0.0$ | 45.99 ± 9.39 | 89.11 ± 9.61 | 24.33 ± 4.06 | 371.4 ± 12.1 | 105.0 ± 2.8 |
| | $\sigma = 1.0$ | 44.05 ± 8.71 | 86.86 ± 8.87 | 23.22 ± 3.65 | 371.8 ± 12.0 | 105.4 ± 2.5 |
| | $\sigma = 2.0$ | 44.06 ± 12.69 | 86.72 ± 12.83 | 23.17 ± 5.25 | 371.8 ± 12.0 | 104.6 ± 3.0 |
| | $\sigma = 3.0$ | 44.12 ± 10.33 | 86.73 ± 10.45 | 23.54 ± 4.41 | 371.8 ± 12.0 | 105.0 ± 2.8 |

---

## Table 9: Computational Cost & Execution Profiling
*Measured on Apple Silicon ARM64 over 1,000 real-time control steps.*

| Metric | Measured Value | Unit | Research Note |
| :--- | :--- | :--- | :--- |
| Mean Computation Time per Step | 560.74 | $\mu$s (0.56 ms) | Real-time control cycle execution |
| Std Dev Computation Time | 149.06 | $\mu$s (0.15 ms) | Consistent latency profile |
| Minimum Computation Time | 183.96 | $\mu$s (0.18 ms) | Minimum cycle latency |
| Maximum Computation Time | 1,270.79 | $\mu$s (1.27 ms) | Maximum observed cycle latency |
| Decision Throughput | 1,783.4 | decisions/s | Max capacity in single CPU thread |
| Control Step Period ($\Delta t$) | 1,000,000 | $\mu$s (1.0 s) | SUMO TraCI update interval |
| CPU Budget Utilization | 0.0561% | % | Fraction of 1s budget consumed |

---

## Table 10: Matched-Pair Statistical Significance Tests
*Paired differences: $D_k = \text{Metric}_{\text{proposed}, k} - \text{Metric}_{\text{baseline}, k}$ on identical seeds ($N=5, \text{df}=4$).*

| Scenario | Comparison | Mean Diff $\bar{D}$ (s) | Std Diff $s_D$ | 95% Confidence Interval | $t$-statistic | $p$-value ($t$-test) | $p$-value (Wilcoxon) | Cohen's $d$ | Significance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Low** | Proposed vs Fixed-Time | -7.40 | 0.98 | [-8.61, -6.19] | -16.930 | $7.1 \times 10^{-5}$ | 0.0625 | -7.571 | **Statistically Significant ($p < 0.001$)** |
| | Proposed vs Basic-Queue | +0.24 | 0.44 | [-0.31, +0.79] | +1.232 | 0.2855 | 0.3125 | +0.551 | Not Significant |
| **Medium** | Proposed vs Fixed-Time | -9.63 | 1.85 | [-11.93, -7.33] | -11.634 | $3.1 \times 10^{-4}$ | 0.0625 | -5.203 | **Statistically Significant ($p < 0.001$)** |
| | Proposed vs Basic-Queue | -0.03 | 0.64 | [-0.83, +0.76] | -0.112 | 0.9163 | 1.0000 | -0.050 | Not Significant |
| **High** | Proposed vs Fixed-Time | -29.62 | 10.00 | [-42.04, -17.20] | -6.623 | $2.7 \times 10^{-3}$ | 0.0625 | -2.962 | **Statistically Significant ($p < 0.01$)** |
| | Proposed vs Basic-Queue | +1.09 | 5.00 | [-5.11, +7.29] | +0.487 | 0.6517 | 0.6250 | +0.218 | Not Significant |
| **Oversat.** | Proposed vs Fixed-Time | -15.77 | 11.70 | [-30.29, -1.24] | -3.014 | $3.9 \times 10^{-2}$ | 0.1250 | -1.348 | **Statistically Significant ($p < 0.05$)** |
| | Proposed vs Basic-Queue | -0.34 | 6.20 | [-8.03, +7.36] | -0.121 | 0.9093 | 1.0000 | -0.054 | Not Significant |
| **Asym-NS** | Proposed vs Fixed-Time | -43.83 | 5.21 | [-50.30, -37.35] | -18.803 | $4.7 \times 10^{-5}$ | 0.0625 | -8.409 | **Statistically Significant ($p < 0.001$)** |
| | Proposed vs Basic-Queue | -0.45 | 6.50 | [-8.52, +7.61] | -0.156 | 0.8834 | 1.0000 | -0.070 | Not Significant |
| **Asym-EW** | Proposed vs Fixed-Time | -54.17 | 6.48 | [-62.21, -46.13] | -18.700 | $4.8 \times 10^{-5}$ | 0.0625 | -8.363 | **Statistically Significant ($p < 0.001$)** |
| | Proposed vs Basic-Queue | -4.83 | 9.30 | [-16.38, +6.72] | -1.161 | 0.3101 | 0.8125 | -0.519 | Substantial Medium Effect ($d=-0.52$) |
| **Dynamic** | Proposed vs Fixed-Time | -29.60 | 5.99 | [-37.04, -22.16] | -11.044 | $3.8 \times 10^{-4}$ | 0.0625 | -4.939 | **Statistically Significant ($p < 0.001$)** |
| | Proposed vs Basic-Queue | -2.26 | 6.29 | [-10.08, +5.55] | -0.804 | 0.4662 | 0.4375 | -0.360 | Small-to-Medium Effect ($d=-0.36$) |
