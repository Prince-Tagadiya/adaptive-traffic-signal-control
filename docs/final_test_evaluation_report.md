# Phase 9: Blind Final Test Evaluation Report

**Evaluation Status:** COMPLETE  
**Controller Code Status:** STRICTLY FROZEN (No parameter modifications, tuning, or code changes)  
**Evaluation Set:** Test Seeds 42, 43, 44, 45, 46  
**Execution Timestamp:** 2026-10-04T13:17:00  

---

## A. Test Protocol

The test protocol evaluates four traffic signal controllers across seven demand scenarios and five independent evaluation seeds. All simulation runs were executed using SUMO TraCI in a headless environment with strict separation from prior calibration data. The parameter configuration of the proposed controller was frozen prior to executing this evaluation, and no parameter adjustments were made based on test set outcomes.

---

## B. Controllers Evaluated

Four signal controllers were evaluated under identical simulation conditions:

1. **C0 — Original Fixed-Time Controller (`FixedTimeSignalController`):**
   - Static 90-second cycle: Phase 0 (NS Green, 42s), Phase 1 (NS Yellow, 3s), Phase 2 (EW Green, 42s), Phase 3 (EW Yellow, 3s).
2. **C1 — Webster-Calibrated Minimum-Cycle Fixed-Time Controller (`OptimizedFixedTimeSignalController`):**
   - Static 36-second cycle derived from Webster's formula constrained by $G_{\text{min}} = 15\text{s}$: Phase 0 (NS Green, 15s), Phase 1 (NS Yellow, 3s), Phase 2 (EW Green, 15s), Phase 3 (EW Yellow, 3s).
3. **C2 — Basic Queue-Based Adaptive Controller (`BasicDensityController`):**
   - Real-time queue comparison ($Q_{\text{NS}}$ vs $Q_{\text{EW}}$) with $G_{\text{min}} = 15\text{s}$, $G_{\text{max}} = 50\text{s}$, $Y = 3\text{s}$, and red starvation override at $R_{\text{starve}} = 45\text{s}$.
4. **C3 — Proposed Composite Adaptive Controller (`ProposedAdaptiveSignalController`):**
   - Frozen parameters:
     - Component weights: $\alpha = 1.00$, $\beta = 0.75$, $\gamma = 0.10$, $\delta = 0.25$, $\eta = 0.25$, $H = 0.20$
     - Reference scales: $Q_{\text{ref}} = 20.0\,\text{veh}$, $A_{\text{ref}} = 0.40\,\text{veh/s}$, $W_{\text{ref}} = 30.0\,\text{s}$, $R_{\text{ref}} = 50.0\,\text{s}$, $G_{\text{ref}} = 0.50\,\text{veh/s}$
     - Windows & Constraints: $W_A = 20\,\text{s}$, $W_G = 10\,\text{s}$, $G_{\text{min}} = 15\,\text{s}$, $G_{\text{max}} = 50\,\text{s}$, $Y = 3\,\text{s}$, $R_{\text{starve}} = 45\,\text{s}$.

---

## C. Evaluation Scenarios

Seven test scenarios were evaluated:
1. **Low Demand (`low`):** Balanced demand with arrival probability $p = 0.04$ per approach.
2. **Medium Demand (`medium`):** Balanced demand with arrival probability $p = 0.08$ per approach.
3. **High Demand (`high`):** Balanced demand near saturation with arrival probability $p = 0.14$ per approach.
4. **Oversaturated Demand (`oversaturated`):** Demand exceeding intersection capacity with $p = 0.18$ per approach.
5. **Asymmetric NS Demand (`asym_ns`):** Major arterial flow on North-South ($p_{\text{NS}} = 0.14$, $p_{\text{EW}} = 0.03$).
6. **Asymmetric EW Demand (`asym_ew`):** Major arterial flow on East-West ($p_{\text{NS}} = 0.03$, $p_{\text{EW}} = 0.14$).
7. **Dynamic Surge Demand (`dynamic`):** Three-stage surge: $0\text{--}300\text{s}: p=0.04 \rightarrow 300\text{--}700\text{s}: p=0.15 \rightarrow 700\text{--}1000\text{s}: p=0.05$.

---

## D. Evaluation Seeds

Simulations were conducted across five independent seeds:
$$\text{Seeds} = [42, 43, 44, 45, 46]$$
Total simulation runs:
$$4\text{ controllers} \times 7\text{ scenarios} \times 5\text{ seeds} = 140\text{ runs}$$

---

## E. Cohort Definition

Metrics were collected strictly using the **Cohort A** standard:
$$\text{Cohort A} = \{v \in \mathcal{V} \mid t_{\text{depart}}(v) \ge 200\,\text{s} \land t_{\text{arrive}}(v) \ge 200\,\text{s}\}$$
Vehicles departing during the initial 200-second warm-up window were excluded from primary travel time, waiting time, and delay metrics.

---

## F. Recorded Metrics

For each run, the following metrics were recorded:
- `throughput_cohort_a`: Count of Cohort A vehicles successfully completing their trips.
- `mean_waiting_time_s`: Average accumulated waiting time ($v < 0.1\,\text{m/s}$) per vehicle in seconds.
- `mean_travel_time_s`: Average total travel time per vehicle in seconds.
- `mean_delay_s`: Average time-loss delay per vehicle in seconds.
- `total_delay_s`: Sum of time-loss delay across all Cohort A vehicles in seconds.
- `mean_stops_per_veh`: Average number of complete halts per vehicle.
- `mean_speed_mps`: Average vehicle trip speed in meters per second.
- `mean_queue_veh`: Time-average total queue length across all four incoming lanes during the evaluation period.
- `max_queue_veh`: Maximum observed aggregate queue length.
- `phase_switch_count`: Total number of signal phase changes during the simulation.
- `total_yellow_lost_time_s`: Total duration of yellow clearance intervals in seconds.
- `max_red_duration_s`: Maximum observed continuous red phase experienced by any approach with active queue.

---

## G. Execution Summary & Run Integrity

- **Total Scheduled Runs:** 140
- **Total Completed Runs:** 140
- **Successful Runs:** 140 (100.0%)
- **Failed Runs:** 0
- **Missing Runs:** 0
- **Runtime Errors:** 0

All 140 runs were logged to [`results/final_test_results_per_seed.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/final_test_results_per_seed.csv).

---

## H. Performance Summary Table (Mean ± Standard Deviation across Seeds 42–46)

The table below presents the descriptive statistics (Mean ± SD) across the five evaluation seeds ($N = 5$ matched replications per cell). Data are exported to [`results/final_test_summary.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/final_test_summary.csv).

| Scenario | Controller | Throughput (veh) | Waiting Time (s) | Delay (s) | Queue (veh) | Phase Switches | Max Red (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`low`** | **C0: Original Fixed-Time** | $109.40 \pm 10.53$ | $11.94 \pm 0.72$ | $18.11 \pm 0.88$ | $1.72 \pm 0.21$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $110.60 \pm 9.84$ | $4.56 \pm 0.67$ | $10.20 \pm 1.00$ | $0.63 \pm 0.09$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $110.60 \pm 9.84$ | $4.29 \pm 0.30$ | $9.97 \pm 0.50$ | $0.59 \pm 0.07$ | $86.80 \pm 4.38$ | $58.20 \pm 15.61$ |
| | **C3: Proposed Adaptive** | $110.40 \pm 9.84$ | $4.32 \pm 0.53$ | $9.31 \pm 0.73$ | $0.61 \pm 0.11$ | $69.20 \pm 4.15$ | $60.20 \pm 10.26$ |
| **`medium`** | **C0: Original Fixed-Time** | $224.00 \pm 15.05$ | $16.40 \pm 2.27$ | $25.12 \pm 3.01$ | $4.98 \pm 0.46$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $229.00 \pm 16.48$ | $6.64 \pm 1.19$ | $14.09 \pm 1.92$ | $1.90 \pm 0.45$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $228.80 \pm 16.21$ | $6.81 \pm 0.79$ | $14.17 \pm 1.01$ | $1.94 \pm 0.27$ | $100.80 \pm 1.79$ | $45.20 \pm 11.03$ |
| | **C3: Proposed Adaptive** | $228.80 \pm 16.21$ | $8.40 \pm 2.46$ | $15.86 \pm 3.06$ | $2.36 \pm 0.75$ | $89.20 \pm 3.90$ | $44.00 \pm 4.00$ |
| **`high`** | **C0: Original Fixed-Time** | $313.00 \pm 9.82$ | $75.62 \pm 7.31$ | $108.95 \pm 8.09$ | $40.31 \pm 2.99$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $357.80 \pm 11.48$ | $43.22 \pm 9.13$ | $86.10 \pm 20.65$ | $22.74 \pm 5.04$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $355.00 \pm 12.43$ | $44.91 \pm 10.92$ | $88.05 \pm 24.26$ | $23.72 \pm 6.02$ | $107.20 \pm 1.30$ | $26.60 \pm 1.95$ |
| | **C3: Proposed Adaptive** | $347.80 \pm 15.53$ | $49.66 \pm 12.07$ | $94.45 \pm 23.29$ | $26.07 \pm 6.61$ | $99.60 \pm 3.85$ | $42.40 \pm 6.02$ |
| **`oversaturated`** | **C0: Original Fixed-Time** | $303.20 \pm 13.46$ | $86.61 \pm 12.35$ | $123.43 \pm 17.41$ | $55.33 \pm 4.95$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $348.80 \pm 7.89$ | $67.87 \pm 4.96$ | $151.01 \pm 11.82$ | $37.65 \pm 1.66$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $340.60 \pm 15.63$ | $71.18 \pm 7.04$ | $154.01 \pm 19.27$ | $38.78 \pm 2.32$ | $105.20 \pm 3.35$ | $34.60 \pm 12.74$ |
| | **C3: Proposed Adaptive** | $343.60 \pm 13.94$ | $71.18 \pm 8.13$ | $149.28 \pm 22.58$ | $39.68 \pm 2.08$ | $100.40 \pm 5.03$ | $44.00 \pm 6.04$ |
| **`asym_ns`** | **C0: Original Fixed-Time** | $199.00 \pm 10.25$ | $59.55 \pm 7.69$ | $86.52 \pm 11.26$ | $20.90 \pm 4.76$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $219.60 \pm 5.27$ | $36.31 \pm 16.20$ | $73.85 \pm 34.86$ | $11.52 \pm 5.40$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $246.40 \pm 20.91$ | $16.17 \pm 6.94$ | $31.34 \pm 13.07$ | $5.09 \pm 2.37$ | $72.00 \pm 8.49$ | $66.20 \pm 11.45$ |
| | **C3: Proposed Adaptive** | $246.80 \pm 18.38$ | $13.38 \pm 4.87$ | $24.99 \pm 8.47$ | $4.23 \pm 1.73$ | $58.80 \pm 2.68$ | $73.00 \pm 15.78$ |
| **`asym_ew`** | **C0: Original Fixed-Time** | $201.20 \pm 7.29$ | $67.51 \pm 5.37$ | $96.69 \pm 9.44$ | $22.64 \pm 3.66$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $222.00 \pm 7.65$ | $32.60 \pm 14.74$ | $68.47 \pm 31.92$ | $10.88 \pm 4.99$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $243.80 \pm 17.60$ | $18.17 \pm 10.65$ | $34.32 \pm 18.50$ | $5.78 \pm 3.57$ | $72.40 \pm 6.69$ | $64.40 \pm 10.14$ |
| | **C3: Proposed Adaptive** | $248.00 \pm 21.35$ | $12.51 \pm 4.97$ | $23.71 \pm 7.75$ | $3.88 \pm 1.56$ | $60.40 \pm 3.29$ | $71.80 \pm 13.48$ |
| **`dynamic`** | **C0: Original Fixed-Time** | $289.40 \pm 8.68$ | $58.54 \pm 13.80$ | $84.97 \pm 18.57$ | $22.47 \pm 6.68$ | $44.00 \pm 0.00$ | $45.00 \pm 0.00$ |
| | **C1: Webster Fixed-Time** | $301.80 \pm 15.53$ | $30.82 \pm 9.95$ | $61.30 \pm 22.38$ | $11.70 \pm 4.53$ | $110.00 \pm 0.00$ | $18.00 \pm 0.00$ |
| | **C2: Basic Queue** | $303.80 \pm 17.88$ | $31.21 \pm 11.55$ | $61.99 \pm 24.32$ | $11.83 \pm 4.96$ | $98.80 \pm 3.63$ | $46.00 \pm 7.45$ |
| | **C3: Proposed Adaptive** | $303.40 \pm 17.74$ | $30.22 \pm 9.66$ | $58.90 \pm 20.77$ | $11.47 \pm 4.35$ | $91.00 \pm 3.87$ | $53.40 \pm 6.11$ |

---

## I. Failed and Repeated Runs

- **Failed Runs:** None (0 runs failed).
- **Repeated Runs during Batch:** None. All 140 planned runs succeeded on their initial execution.

---

## J. Determinism Verification

Following the completion of the 140 evaluation runs, a determinism check was conducted by re-running the C3 Proposed Controller on the `medium` scenario with seed 42 and comparing the output against the original run record:

| Metric | Original Run Value | Repeated Run Value | Difference ($\Delta$) | Exact Match |
| :--- | :---: | :---: | :---: | :---: |
| **Cohort A Throughput** | 220 veh | 220 veh | 0 | **True** |
| **Mean Waiting Time** | 8.54 s | 8.54 s | 0.00 s | **True** |
| **Mean Travel Time** | 53.92 s | 53.92 s | 0.00 s | **True** |
| **Mean Delay** | 15.90 s | 15.90 s | 0.00 s | **True** |
| **Mean Queue Length** | 2.21 veh | 2.21 veh | 0.00 veh | **True** |
| **Phase Switch Count** | 88 switches | 88 switches | 0 | **True** |

**Determinism Status:** **PASSED (Bit-level Identical Across All Metrics)**.

---

## K. Data Separation and Pre-Test Integrity Certification

1. **Blind Evaluation Certification:** The evaluation seeds 42, 43, 44, 45, and 46 were treated as strictly blind data.
2. **Invariance of Frozen Parameters:** The controller parameters and architecture ($\alpha=1.00, \beta=0.75, \gamma=0.10, \delta=0.25, \eta=0.25, H=0.20$) were frozen prior to this evaluation and remained completely unchanged during and after the runs.
3. **No Post-Hoc Selection:** No parameters were selected, tuned, or re-calibrated using test set observations.
4. **No Statistical Claims:** No hypothesis tests, multiple-comparison corrections, effect size interpretations, or superiority claims have been made in this phase.
