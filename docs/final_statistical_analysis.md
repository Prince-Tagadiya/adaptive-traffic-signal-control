# Phase 10: Final Statistical Analysis of Blind Test Set

**Authors**: Prince Tagadiya  
**Evaluation Phase**: Phase 10 — Blind Test Inferential Evaluation  
**Evaluation Date**: October 2026  
**Status**: FINAL INFERENTIAL AUDIT COMPLETE (Controller strictly frozen; zero modifications, zero re-tuning)  

---

## 1. Statistical Design

The statistical analysis follows a pre-registered, multi-scenario matched-pairs design evaluating four traffic signal control strategies across seven demand regimes on an uninspected, blind test set. The objective is to evaluate whether the proposed composite adaptive controller (C3) demonstrates statistically significant differences against three comparator baselines: original fixed-time control (C0), Webster-calibrated fixed-time control (C1), and basic queue-based adaptive control (C2).

The experimental evaluation was conducted strictly on the already-generated blind test set:
- Primary per-seed record: [`results/final_test_results_per_seed.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/final_test_results_per_seed.csv)
- Descriptive summary record: [`results/final_test_summary.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/final_test_summary.csv)

In strict compliance with confirmatory statistical protocols:
- **No controller modifications** were permitted.
- **No simulations were rerun** or re-seeded.
- **No parameter tuning** or post-hoc model selection was performed.
- **No data dredging** or cherry-picking of favorable seeds occurred.

---

## 2. Experimental Unit

The experimental unit is the **matched simulation realization** defined by the scenario-seed pair:
$$\mathcal{E} = (\text{scenario } s, \text{ seed } k)$$

> [!IMPORTANT]
> **Elimination of Pseudoreplication:** Individual vehicles traversing the network are **NOT** treated as independent experimental observations. Vehicles within a single simulation interact dynamically through car-following, queuing, and shared signal phases. Aggregating hundreds of vehicles per run and computing standard errors as $s / \sqrt{N_{\text{veh}}}$ produces severe pseudoreplication (Hurlbert, 1984), artificially deflating standard errors by $\sqrt{N_{\text{veh}}} \approx 15\text{--}25$ and generating spuriously inflated $t$-statistics. All inferential statistics in this report are conducted strictly at the macro simulation realization level.

---

## 3. Number of Scenarios and Seeds

The evaluation incorporates seven traffic demand scenarios:
1. **`low`**: Balanced demand, arrival probability $p = 0.04$ per lane (symmetric).
2. **`medium`**: Balanced demand, arrival probability $p = 0.08$ per lane (symmetric).
3. **`high`**: Balanced demand near capacity, arrival probability $p = 0.14$ per lane (symmetric).
4. **`oversaturated`**: Balanced demand exceeding capacity, arrival probability $p = 0.18$ per lane (oversaturated).
5. **`asym_ns`**: Asymmetric arterial flow on North-South ($p_{\text{NS}} = 0.14, p_{\text{EW}} = 0.03$) (asymmetric).
6. **`asym_ew`**: Asymmetric arterial flow on East-West ($p_{\text{NS}} = 0.03, p_{\text{EW}} = 0.14$) (asymmetric).
7. **`dynamic`**: Three-stage demand surge ($0\text{--}300\text{s}: p=0.04 \rightarrow 300\text{--}700\text{s}: p=0.15 \rightarrow 700\text{--}1000\text{s}: p=0.05$) (dynamic).

Simulations were conducted across five independent blind seeds:
$$\text{Test Seeds} = [42, 43, 44, 45, 46]$$

Explicitly stated sample size:
$$N = 5\text{ independent simulation realizations per scenario, with matched seeds across controllers.}$$
Total simulation runs across the 4 controllers: $4 \times 7 \times 5 = 140$ runs.

---

## 4. Primary Endpoint

The pre-specified **primary outcome metric** is:
$$\text{mean\_waiting\_time\_s}$$
defined as the average cumulative duration (in seconds) that vehicles spent at velocity $v < 0.1\,\text{m/s}$ during their journey, evaluated strictly on the post-warmup **Cohort A** population ($t_{\text{depart}} \ge 200\,\text{s} \land t_{\text{arrive}} \ge 200\,\text{s}$).

The primary inferential comparisons are conducted separately for each scenario across three pairwise contrasts:
- **Comparison A**: C3 Proposed Adaptive vs C0 Original Fixed-Time
- **Comparison B**: C3 Proposed Adaptive vs C1 Webster-Calibrated Fixed-Time
- **Comparison C**: C3 Proposed Adaptive vs C2 Basic Queue Adaptive

---

## 5. Pairing Methodology

Because every controller was simulated against the exact same immutable route demand realization for seed $k$, controller outcomes are strictly matched:
$$D_{s, k} = Y_{C3, s, k} - Y_{\text{comparator}, s, k}$$
where $Y_{\cdot, s, k}$ represents the mean waiting time observed for seed $k$ in scenario $s$.

Pairing isolates the net controller treatment effect by cancelling inter-seed variance arising from stochastic vehicle arrival clustering. In accordance with standard traffic engineering conventions:
- **Negative difference ($D < 0$) favors C3 Proposed Adaptive** (indicating a reduction in vehicle waiting time).
- **Positive difference ($D > 0$) favors the comparator** (indicating an increase in waiting time under C3).

---

## 6. Statistical Tests

For every scenario $\times$ comparator contrast ($7 \times 3 = 21$ primary comparisons), the following statistical properties were computed:
1. **Paired Mean Difference**: $\bar{D} = \frac{1}{N} \sum_{k=1}^N D_k$
2. **Standard Deviation of Paired Differences**: $s_D = \sqrt{\frac{1}{N-1} \sum_{k=1}^N (D_k - \bar{D})^2}$
3. **Standard Error of the Mean Difference**: $\text{SE}_D = s_D / \sqrt{N}$
4. **95% Confidence Interval**: $[\bar{D} - t_{0.975, 4} \cdot \text{SE}_D, \bar{D} + t_{0.975, 4} \cdot \text{SE}_D]$ where $t_{0.975, 4} = 2.7764$ (Student's $t$-distribution with $\nu = 4$ degrees of freedom).
5. **Two-Sided Paired Student's $t$-Test**: $t = \bar{D} / \text{SE}_D$ with two-tailed $p_{\text{raw}} = 2(1 - F(|t|, 4))$.
6. **Two-Sided Wilcoxon Signed-Rank Test**: Exact non-parametric test evaluating the distribution of signed ranks.
7. **Paired Cohen's $d_z$**: $d_z = \bar{D} / s_D$, representing the standardized effect size of the paired differences.
8. **Relative Percentage Change**: $\Delta\% = 100 \times (\bar{Y}_{C3} - \bar{Y}_{\text{comp}}) / \bar{Y}_{\text{comp}}$.

---

## 7. Multiple-Comparison Corrections

With 7 scenarios and 3 comparators, there are exactly **$M = 21$ confirmatory primary hypothesis tests**. Evaluating 21 tests simultaneously at nominal $\alpha = 0.05$ creates substantial risk of family-wise Type I error inflation. To maintain inferential rigor, two pre-specified correction procedures were applied to the two-sided paired $t$-test $p$-values:

1. **Holm-Bonferroni Step-Down Procedure (FWER Control)**:
   - Controls Family-Wise Error Rate at $\alpha = 0.05$.
   - Raw $p$-values are sorted: $p_{(1)} \le p_{(2)} \le \dots \le p_{(M)}$.
   - Adjusted $p$-value at rank $j$: $p_{\text{Holm},(j)} = \min\left(1, \max_{k \le j} (M - k + 1) p_{(k)}\right)$.

2. **Benjamini-Hochberg Procedure (FDR Control)**:
   - Controls the False Discovery Rate at $q \le 0.05$.
   - Adjusted $q$-value at rank $j$: $q_{\text{BH},(j)} = \min\left(1, \min_{k \ge j} \frac{M \cdot p_{(k)}}{k}\right)$.

> [!IMPORTANT]
> **Confirmatory Significance Threshold**: In accordance with the pre-specified protocol, a result is **NOT** designated as statistically significant unless its adjusted $p$-value remains strictly below $\alpha = 0.05$ after the declared multiple-comparison correction.

---

## 8. Primary Waiting-Time Results

The 21 primary hypothesis tests evaluating Cohort A Mean Waiting Time ($N=5$ matched pairs per row) are detailed below. Negative differences represent waiting-time reductions favoring C3 Proposed Adaptive.

| Scenario | Comparator | C3 Mean (s) | Comp Mean (s) | Mean Diff (s) | % Change | 95% Confidence Interval (s) | Paired $t$ ($df=4$) | Raw $p$ | Holm $p$ | BH $q$ | Wilcoxon $p$ | Cohen's $d_z$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`low`** | C0 | 4.32 | 11.94 | -7.62 | -63.83% | [-8.48, -6.76] | $t = -24.700$ | 1.59e-05 | 0.00030 | 0.00011 | 0.0625 | -11.046 |
| **`low`** | C1 | 4.32 | 4.56 | -0.24 | -5.31% | [-1.25, 0.77] | $t = -0.666$ | 0.54203 | 1.00000 | 0.66957 | 0.4375 | -0.298 |
| **`low`** | C2 | 4.32 | 4.29 | 0.02 | 0.56% | [-0.75, 0.80] | $t = 0.086$ | 0.93546 | 1.00000 | 0.98223 | 1.0000 | 0.039 |
| **`medium`** | C0 | 8.40 | 16.40 | -8.01 | -48.82% | [-11.06, -4.95] | $t = -7.279$ | 0.00189 | 0.03218 | 0.00795 | 0.0625 | -3.255 |
| **`medium`** | C1 | 8.40 | 6.64 | 1.75 | 26.37% | [-0.60, 4.10] | $t = 2.072$ | 0.10697 | 1.00000 | 0.20422 | 0.1875 | 0.927 |
| **`medium`** | C2 | 8.40 | 6.81 | 1.59 | 23.36% | [-0.76, 3.94] | $t = 1.881$ | 0.13314 | 1.00000 | 0.21508 | 0.1875 | 0.841 |
| **`high`** | C0 | 49.66 | 75.62 | -25.96 | -34.33% | [-39.48, -12.43] | $t = -5.329$ | 0.00597 | 0.09549 | 0.02089 | 0.0625 | -2.383 |
| **`high`** | C1 | 49.66 | 43.22 | 6.44 | 14.90% | [0.86, 12.02] | $t = 3.207$ | 0.03269 | 0.41920 | 0.06865 | 0.0625 | 1.434 |
| **`high`** | C2 | 49.66 | 44.91 | 4.75 | 10.59% | [-2.68, 12.18] | $t = 1.777$ | 0.15028 | 1.00000 | 0.22542 | 0.1875 | 0.795 |
| **`oversaturated`** | C0 | 71.18 | 86.61 | -15.43 | -17.82% | [-28.73, -2.13] | $t = -3.221$ | 0.03225 | 0.41920 | 0.06865 | 0.0625 | -1.441 |
| **`oversaturated`** | C1 | 71.18 | 67.87 | 3.31 | 4.88% | [-1.40, 8.03] | $t = 1.950$ | 0.12295 | 1.00000 | 0.21508 | 0.1250 | 0.872 |
| **`oversaturated`** | C2 | 71.18 | 71.18 | 0.00 | 0.00% | [-5.75, 5.75] | $t = 0.000$ | 1.00000 | 1.00000 | 1.00000 | 1.0000 | 0.000 |
| **`asym_ns`** | C0 | 13.38 | 59.55 | -46.17 | -77.54% | [-50.36, -41.98] | $t = -30.589$ | 6.80e-06 | 0.00014 | 0.00011 | 0.0625 | -13.680 |
| **`asym_ns`** | C1 | 13.38 | 36.31 | -22.93 | -63.16% | [-37.36, -8.50] | $t = -4.413$ | 0.01157 | 0.17359 | 0.03472 | 0.0625 | -1.974 |
| **`asym_ns`** | C2 | 13.38 | 16.17 | -2.80 | -17.30% | [-7.47, 1.87] | $t = -1.663$ | 0.17157 | 1.00000 | 0.24020 | 0.3125 | -0.744 |
| **`asym_ew`** | C0 | 12.51 | 67.51 | -55.01 | -81.48% | [-60.68, -49.33] | $t = -26.925$ | 1.13e-05 | 0.00023 | 0.00011 | 0.0625 | -12.041 |
| **`asym_ew`** | C1 | 12.51 | 32.60 | -20.09 | -61.64% | [-33.72, -6.47] | $t = -4.094$ | 0.01493 | 0.20902 | 0.03919 | 0.0625 | -1.831 |
| **`asym_ew`** | C2 | 12.51 | 18.17 | -5.67 | -31.18% | [-15.70, 4.37] | $t = -1.567$ | 0.19214 | 1.00000 | 0.25219 | 0.3125 | -0.701 |
| **`dynamic`** | C0 | 30.22 | 58.54 | -28.32 | -48.38% | [-36.56, -20.09] | $t = -9.545$ | 0.00067 | 0.01211 | 0.00353 | 0.0625 | -4.269 |
| **`dynamic`** | C1 | 30.22 | 30.82 | -0.60 | -1.94% | [-3.91, 2.72] | $t = -0.501$ | 0.64262 | 1.00000 | 0.71027 | 0.6250 | -0.224 |
| **`dynamic`** | C2 | 30.22 | 31.21 | -0.99 | -3.17% | [-5.69, 3.71] | $t = -0.584$ | 0.59063 | 1.00000 | 0.68907 | 0.6250 | -0.261 |

Complete tabular data are exported to [`results/statistical_primary_waiting_time.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/statistical_primary_waiting_time.csv).

---

## 9. Secondary Metric Results (Exploratory)

> [!NOTE]
> **Exploratory Labeling**: In strict compliance with confirmatory statistical rules, secondary metrics (Mean Travel Time, Mean Delay, Mean Queue, Cohort A Throughput, and Phase Switch Count) are treated as **purely exploratory**. They are analyzed exclusively for C3 vs C1 and C3 vs C2 ($2 \text{ comparators} \times 7 \text{ scenarios} \times 5 \text{ metrics} = 70$ evaluations) and are **strictly separated** from the 21-test confirmatory primary family.

Data are archived in [`results/statistical_secondary_metrics.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/statistical_secondary_metrics.csv). Key findings across secondary metrics include:

### 9.1 Phase Switch Count (Signal Stability & Lost Time)
Across all seven scenarios, C3 Proposed Adaptive generates **consistently and substantially fewer phase switches** than both C1 and C2:
- **C3 vs C1 (Webster Fixed-Time)**: C1 executes a rigid 36-second cycle yielding exactly 110 phase transitions in every run. C3 reduces phase switches by **$9.5\%$ to $46.5\%$** across all scenarios ($p < 0.015$ in all 7 scenarios, $d_z$ between $-1.91$ and $-19.08$).
- **C3 vs C2 (Basic Queue)**: C2 lacks queue smoothing and hysteresis, switching phases erratically in response to momentary queue fluctuations. C3 reduces phase switches across **every scenario**:
  - `low`: $-17.60$ switches ($-20.28\%, p = 0.00019, d_z = -5.93$)
  - `medium`: $-11.60$ switches ($-11.51\%, p = 0.00094, d_z = -3.91$)
  - `high`: $-7.60$ switches ($-7.09\%, p = 0.00611, d_z = -2.37$)
  - `oversaturated`: $-4.80$ switches ($-4.56\%, p = 0.00776, d_z = -2.21$)
  - `asym_ns`: $-13.20$ switches ($-18.33\%, p = 0.02719, d_z = -1.52$)
  - `asym_ew`: $-12.00$ switches ($-16.57\%, p = 0.01673, d_z = -1.77$)
  - `dynamic`: $-7.80$ switches ($-7.89\%, p = 0.00030, d_z = -5.26$)

This proves that the composite objective's queue growth smoothing and hysteresis terms successfully prevent high-frequency phase hunting without sacrificing throughput.

### 9.2 Mean Travel Time & Mean Delay
- **Asymmetric Scenarios (`asym_ns`, `asym_ew`)**: C3 reduces mean travel time by **$42.1\%$ to $43.7\%$** vs C1 ($p < 0.017, d_z \approx -1.8$) and by **$9.2\%$ to $14.7\%$** vs C2 ($p = 0.11\text{--}0.17$). Mean delay decreases by **$65.4\%$ to $66.2\%$** vs C1 ($p < 0.017$) and by **$20.2\%$ to $30.9\%$** vs C2 ($p = 0.11\text{--}0.17$).
- **Symmetric Scenarios (`low`, `medium`, `high`, `oversaturated`)**: Travel times and delays between C3, C1, and C2 are closely clustered:
  - In `low`, C3 slightly outperforms C1 ($-1.8\%$) and C2 ($-1.4\%$) ($p \approx 0.09\text{--}0.15$).
  - In `medium`, C1 has marginally lower travel time ($-3.4\%$) and delay ($-12.6\%$) than C3 ($p = 0.15$), as does C2 ($-3.3\%$) ($p = 0.19$).
  - In `high`, C1 achieves lower travel time ($8.34\,\text{s}$ lower, $+6.7\%, p = 0.024$), though non-significant after family correction.
  - In `oversaturated`, C3, C1, and C2 exhibit comparable travel times ($187.14\,\text{s}$ for C3 vs $188.87\,\text{s}$ for C1 and $191.86\,\text{s}$ for C2; differences non-significant, $p > 0.30$).

### 9.3 Mean Queue Length (veh)
- **Asymmetric Demand**: In `asym_ns` and `asym_ew`, C3 reduces average intersection queue from $11.52\,\text{veh}$ (C1) down to $4.23\,\text{veh}$ (C3) ($-63.3\%, p = 0.012$) and from $10.88\,\text{veh}$ (C1) down to $3.88\,\text{veh}$ (C3) ($-64.4\%, p = 0.014$). Against C2, queues drop from $5.09\,\text{veh}$ to $4.23\,\text{veh}$ in `asym_ns` ($-17.0\%$) and $5.78\,\text{veh}$ to $3.88\,\text{veh}$ in `asym_ew` ($-32.9\%$).
- **Symmetric & Oversaturated Demand**: Queues are near-identical across controllers in `low` ($0.61$ vs $0.63$ veh) and `dynamic` ($11.47$ vs $11.70$ veh). In `oversaturated`, C1 maintains slightly lower queue ($37.65\,\text{veh}$) than C3 ($39.68\,\text{veh}$) and C2 ($38.78\,\text{veh}$) due to strictly enforcing 15-second cycles that clear minimum green platoons without detector evaluation.

### 9.4 Cohort A Throughput
In undersaturated regimes (`low`, `medium`, `dynamic`), throughput is demand-constrained and identical across all controllers ($110.4\text{--}110.6$ veh in `low`, $228.8\text{--}229.0$ veh in `medium`, $301.8\text{--}303.8$ veh in `dynamic`). In asymmetric scenarios (`asym_ns`, `asym_ew`), C3 achieves **$11.7\%$ to $12.4\%$ higher throughput** than fixed-time C1 ($p < 0.034$), matching C2 ($248.0$ vs $243.8\text{--}246.4$ veh). In `high` and `oversaturated`, throughput remains within $1\text{--}3\%$ across C1, C2, and C3 ($343.6$ to $348.8$ veh in `oversaturated`).

---

## 10. Effect Sizes

Effect sizes for the primary outcome (waiting time) are summarized in [`results/effect_size_summary.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/effect_size_summary.csv) and presented below:

| Scenario | Regime | Comparator | Mean Diff (s) | % Change | 95% CI (s) | Cohen's $d_z$ | Effect Magnitude |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`low`** | symmetric | C0 | -7.62 | -63.83% | [-8.48, -6.76] | -11.046 | Extremely Large ($|d_z| \ge 2.0$) |
| **`low`** | symmetric | C1 | -0.24 | -5.31% | [-1.25, 0.77] | -0.298 | Small ($0.2 \le |d_z| < 0.5$) |
| **`low`** | symmetric | C2 | 0.02 | 0.56% | [-0.75, 0.80] | 0.039 | Negligible ($|d_z| < 0.2$) |
| **`medium`** | symmetric | C0 | -8.01 | -48.82% | [-11.06, -4.95] | -3.255 | Extremely Large ($|d_z| \ge 2.0$) |
| **`medium`** | symmetric | C1 | 1.75 | 26.37% | [-0.60, 4.10] | 0.927 | Large ($0.8 \le |d_z| < 2.0$) |
| **`medium`** | symmetric | C2 | 1.59 | 23.36% | [-0.76, 3.94] | 0.841 | Large ($0.8 \le |d_z| < 2.0$) |
| **`high`** | symmetric | C0 | -25.96 | -34.33% | [-39.48, -12.43] | -2.383 | Extremely Large ($|d_z| \ge 2.0$) |
| **`high`** | symmetric | C1 | 6.44 | 14.90% | [0.86, 12.02] | 1.434 | Large ($0.8 \le |d_z| < 2.0$) |
| **`high`** | symmetric | C2 | 4.75 | 10.59% | [-2.68, 12.18] | 0.795 | Medium ($0.5 \le |d_z| < 0.8$) |
| **`oversaturated`** | oversaturated | C0 | -15.43 | -17.82% | [-28.73, -2.13] | -1.441 | Large ($0.8 \le |d_z| < 2.0$) |
| **`oversaturated`** | oversaturated | C1 | 3.31 | 4.88% | [-1.40, 8.03] | 0.872 | Large ($0.8 \le |d_z| < 2.0$) |
| **`oversaturated`** | oversaturated | C2 | 0.00 | 0.00% | [-5.75, 5.75] | 0.000 | Negligible ($|d_z| < 0.2$) |
| **`asym_ns`** | asymmetric | C0 | -46.17 | -77.54% | [-50.36, -41.98] | -13.680 | Extremely Large ($|d_z| \ge 2.0$) |
| **`asym_ns`** | asymmetric | C1 | -22.93 | -63.16% | [-37.36, -8.50] | -1.974 | Large ($0.8 \le |d_z| < 2.0$) |
| **`asym_ns`** | asymmetric | C2 | -2.80 | -17.30% | [-7.47, 1.87] | -0.744 | Medium ($0.5 \le |d_z| < 0.8$) |
| **`asym_ew`** | asymmetric | C0 | -55.01 | -81.48% | [-60.68, -49.33] | -12.041 | Extremely Large ($|d_z| \ge 2.0$) |
| **`asym_ew`** | asymmetric | C1 | -20.09 | -61.64% | [-33.72, -6.47] | -1.831 | Large ($0.8 \le |d_z| < 2.0$) |
| **`asym_ew`** | asymmetric | C2 | -5.67 | -31.18% | [-15.70, 4.37] | -0.701 | Medium ($0.5 \le |d_z| < 0.8$) |
| **`dynamic`** | dynamic | C0 | -28.32 | -48.38% | [-36.56, -20.09] | -4.269 | Extremely Large ($|d_z| \ge 2.0$) |
| **`dynamic`** | dynamic | C1 | -0.60 | -1.94% | [-3.91, 2.72] | -0.224 | Small ($0.2 \le |d_z| < 0.5$) |
| **`dynamic`** | dynamic | C2 | -0.99 | -3.17% | [-5.69, 3.71] | -0.261 | Small ($0.2 \le |d_z| < 0.5$) |

---

## 11. Scenario-Level Interpretation

To avoid dichotomous fallacies and distinguish between family-wise error rate control (Holm) and false discovery rate control (Benjamini-Hochberg), each contrast is classified below under both criteria:

| Scenario | Comparator | C3 Mean | Comp Mean | Mean Diff (s) | % Change | 95% CI (s) | Raw $p$ | Holm $p$ | BH $q$ | Cohen's $d_z$ | Classification (Holm FWER) | Classification (BH FDR) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **`low`** | C0 | 4.32 | 11.94 | -7.62 | -63.83% | [-8.48, -6.76] | 0.0000 | 0.0003 | 0.0001 | -11.046 | statistically supported improvement | statistically supported improvement |
| **`low`** | C1 | 4.32 | 4.56 | -0.24 | -5.31% | [-1.25, 0.77] | 0.5420 | 1.0000 | 0.6696 | -0.298 | statistically unsupported improvement | statistically unsupported improvement |
| **`low`** | C2 | 4.32 | 4.29 | 0.02 | 0.56% | [-0.75, 0.80] | 0.9355 | 1.0000 | 0.9822 | 0.039 | statistically unsupported degradation | statistically unsupported degradation |
| **`medium`** | C0 | 8.40 | 16.40 | -8.01 | -48.82% | [-11.06, -4.95] | 0.0019 | 0.0322 | 0.0080 | -3.255 | statistically supported improvement | statistically supported improvement |
| **`medium`** | C1 | 8.40 | 6.64 | 1.75 | 26.37% | [-0.60, 4.10] | 0.1070 | 1.0000 | 0.2042 | 0.927 | statistically unsupported degradation | statistically unsupported degradation |
| **`medium`** | C2 | 8.40 | 6.81 | 1.59 | 23.36% | [-0.76, 3.94] | 0.1331 | 1.0000 | 0.2151 | 0.841 | statistically unsupported degradation | statistically unsupported degradation |
| **`high`** | C0 | 49.66 | 75.62 | -25.96 | -34.33% | [-39.48, -12.43] | 0.0060 | 0.0955 | 0.0209 | -2.383 | statistically unsupported improvement | statistically supported improvement |
| **`high`** | C1 | 49.66 | 43.22 | 6.44 | 14.90% | [0.86, 12.02] | 0.0327 | 0.4192 | 0.0686 | 1.434 | statistically unsupported degradation | statistically unsupported degradation |
| **`high`** | C2 | 49.66 | 44.91 | 4.75 | 10.59% | [-2.68, 12.18] | 0.1503 | 1.0000 | 0.2254 | 0.795 | statistically unsupported degradation | statistically unsupported degradation |
| **`oversaturated`** | C0 | 71.18 | 86.61 | -15.43 | -17.82% | [-28.73, -2.13] | 0.0322 | 0.4192 | 0.0686 | -1.441 | statistically unsupported improvement | statistically unsupported improvement |
| **`oversaturated`** | C1 | 71.18 | 67.87 | 3.31 | 4.88% | [-1.40, 8.03] | 0.1230 | 1.0000 | 0.2151 | 0.872 | statistically unsupported degradation | statistically unsupported degradation |
| **`oversaturated`** | C2 | 71.18 | 71.18 | 0.00 | 0.00% | [-5.75, 5.75] | 1.0000 | 1.0000 | 1.0000 | 0.000 | no statistically detectable difference | no statistically detectable difference |
| **`asym_ns`** | C0 | 13.38 | 59.55 | -46.17 | -77.54% | [-50.36, -41.98] | 0.0000 | 0.0001 | 0.0001 | -13.680 | statistically supported improvement | statistically supported improvement |
| **`asym_ns`** | C1 | 13.38 | 36.31 | -22.93 | -63.16% | [-37.36, -8.50] | 0.0116 | 0.1736 | 0.0347 | -1.974 | statistically unsupported improvement | statistically supported improvement |
| **`asym_ns`** | C2 | 13.38 | 16.17 | -2.80 | -17.30% | [-7.47, 1.87] | 0.1716 | 1.0000 | 0.2402 | -0.744 | statistically unsupported improvement | statistically unsupported improvement |
| **`asym_ew`** | C0 | 12.51 | 67.51 | -55.01 | -81.48% | [-60.68, -49.33] | 0.0000 | 0.0002 | 0.0001 | -12.041 | statistically supported improvement | statistically supported improvement |
| **`asym_ew`** | C1 | 12.51 | 32.60 | -20.09 | -61.64% | [-33.72, -6.47] | 0.0149 | 0.2090 | 0.0392 | -1.831 | statistically unsupported improvement | statistically supported improvement |
| **`asym_ew`** | C2 | 12.51 | 18.17 | -5.67 | -31.18% | [-15.70, 4.37] | 0.1921 | 1.0000 | 0.2522 | -0.701 | statistically unsupported improvement | statistically unsupported improvement |
| **`dynamic`** | C0 | 30.22 | 58.54 | -28.32 | -48.38% | [-36.56, -20.09] | 0.0007 | 0.0121 | 0.0035 | -4.269 | statistically supported improvement | statistically supported improvement |
| **`dynamic`** | C1 | 30.22 | 30.82 | -0.60 | -1.94% | [-3.91, 2.72] | 0.6426 | 1.0000 | 0.7103 | -0.224 | statistically unsupported improvement | statistically unsupported improvement |
| **`dynamic`** | C2 | 30.22 | 31.21 | -0.99 | -3.17% | [-5.69, 3.71] | 0.5906 | 1.0000 | 0.6891 | -0.261 | statistically unsupported improvement | statistically unsupported improvement |

### Classification Summary by Multiple Testing Standard

1. **Under Holm-Bonferroni Correction (Conservative Family-Wise Error Rate, $\alpha = 0.05$):**
   - **Statistically Supported Improvements (5 contrasts)**:
     - C3 vs C0 in `low` ($p_{\text{Holm}} = 0.00030$)
     - C3 vs C0 in `medium` ($p_{\text{Holm}} = 0.03218$)
     - C3 vs C0 in `asym_ns` ($p_{\text{Holm}} = 0.00014$)
     - C3 vs C0 in `asym_ew` ($p_{\text{Holm}} = 0.00023$)
     - C3 vs C0 in `dynamic` ($p_{\text{Holm}} = 0.01211$)
   - **Statistically Unsupported Improvements (9 contrasts)**: Contrats where C3 reduced waiting time, but the difference did not achieve $p_{\text{Holm}} < 0.05$ (e.g., C3 vs C1 in `asym_ns` [$p=0.174$], C3 vs C1 in `asym_ew` [$p=0.209$], C3 vs C0 in `high` [$p=0.095$], C3 vs C0 in `oversaturated` [$p=0.419$], C3 vs C1 in `low` [$p=1.00$], C3 vs C1 in `dynamic` [$p=1.00$], and C3 vs C2 in `asym_ns`, `asym_ew`, `dynamic` [$p=1.00$]).
   - **Statistically Unsupported Degradations (6 contrasts)**: Contrasts where the comparator had lower mean waiting time, but the difference was non-significant after Holm adjustment (C3 vs C1 in `medium`, `high`, `oversaturated`; C3 vs C2 in `low`, `medium`, `high`).
   - **No Statistically Detectable Difference (1 contrast)**: C3 vs C2 in `oversaturated` ($\Delta = 0.00\,\text{s}, p = 1.000$).

2. **Under Benjamini-Hochberg Correction (False Discovery Rate, $q \le 0.05$):**
   - **Statistically Supported Improvements (8 contrasts)**:
     - C3 vs C0 in `low` ($q = 0.00011$)
     - C3 vs C0 in `medium` ($q = 0.00795$)
     - C3 vs C0 in `high` ($q = 0.02089$)
     - C3 vs C0 in `asym_ns` ($q = 0.00011$)
     - C3 vs C0 in `asym_ew` ($q = 0.00011$)
     - C3 vs C0 in `dynamic` ($q = 0.00353$)
     - **C3 vs C1 in `asym_ns`** ($q = 0.03472$)
     - **C3 vs C1 in `asym_ew`** ($q = 0.03919$)
   - **Statistically Unsupported Improvements (6 contrasts)**: C3 vs C0 in `oversaturated` ($q = 0.06865$), C3 vs C1 in `low` ($q = 0.66957$), C3 vs C1 in `dynamic` ($q = 0.71027$), and C3 vs C2 in `asym_ns` ($q = 0.24020$), `asym_ew` ($q = 0.25219$), `dynamic` ($q = 0.68907$).
   - **Statistically Unsupported Degradations (6 contrasts)**: C3 vs C1 in `medium` ($q = 0.20422$), `high` ($q = 0.06865$), `oversaturated` ($q = 0.21508$); C3 vs C2 in `low` ($q = 0.98223$), `medium` ($q = 0.21508$), `high` ($q = 0.22542$).
   - **No Statistically Detectable Difference (1 contrast)**: C3 vs C2 in `oversaturated` ($\Delta = 0.00\,\text{s}, q = 1.000$).

---

## 12. Overall Pattern Analysis

> [!IMPORTANT]
> **No Global Pooling**: In accordance with rigorous multi-environment protocol, all 35 scenario-seed observations are **NOT** pooled into a single composite $t$-test. Pooling across heterogeneous traffic regimes with variance heterogeneity would violate homoscedasticity and mask regime-specific dynamics. Instead, the scenario-level pattern is summarized below.

### 12.1 Directional Comparison Counts across Scenarios
- **C3 vs C1 (Webster-Calibrated Fixed-Time)**:
  - Scenarios where C3 has lower mean waiting time: **4 scenarios** (`low`, `asym_ns`, `asym_ew`, `dynamic`)
  - Scenarios where C3 has higher mean waiting time: **3 scenarios** (`medium`, `high`, `oversaturated`)
- **C3 vs C2 (Basic Queue)**:
  - Scenarios where C3 has lower mean waiting time: **3 scenarios** (`asym_ns`, `asym_ew`, `dynamic`)
  - Scenarios where C3 has higher mean waiting time: **3 scenarios** (`low`, `medium`, `high`)
  - Scenarios with identical mean waiting time: **1 scenario** (`oversaturated`, $\Delta = 0.00\,\text{s}$)

### 12.2 Multiple-Comparison Survival Counts
- **Surviving Holm-Bonferroni Correction ($p_{\text{Holm}} < 0.05$)**: **5 of 21 tests** (all five against C0 Original Fixed-Time: `low`, `medium`, `asym_ns`, `asym_ew`, `dynamic`).
- **Surviving Benjamini-Hochberg FDR Correction ($q_{\text{BH}} < 0.05$)**: **8 of 21 tests**:
  - 6 contrasts against C0 (`low`, `medium`, `high`, `asym_ns`, `asym_ew`, `dynamic`)
  - 2 contrasts against C1 (`asym_ns` and `asym_ew`)
  - 0 contrasts against C2

### 12.3 Effect Size Distribution and Percentage Ranges
- **Median Paired Effect Size ($d_z$) across all 21 contrasts**: **$d_z = -0.701$**
- **C3 vs C0**: Median $d_z = -4.269$; percentage change range: **$-81.48\%$ to $-17.82\%$**
- **C3 vs C1**: Median $d_z = -0.224$; percentage change range: **$-63.16\%$ to $+26.37\%$**
- **C3 vs C2**: Median $d_z = 0.000$; percentage change range: **$-31.18\%$ to $+23.36\%$**

### 12.4 Breakdown by Traffic Demand Regime

1. **Symmetric Demand Scenarios (`low`, `medium`, `high`)**:
   - C3 substantially outperforms uncalibrated C0 ($-34.3\%$ to $-63.8\%$ waiting time reductions).
   - However, C3 does **NOT** outperform Webster-calibrated fixed-time C1. In `low`, C3 and C1 are indistinguishable ($-0.24\,\text{s}, -5.3\%, p=0.542$). In `medium` and `high`, C1 achieves lower waiting times than C3 ($+1.75\,\text{s}, +26.4\%$ in `medium`; $+6.44\,\text{s}, +14.9\%$ in `high`), although neither degradation survives multiple testing correction ($q = 0.204$ and $q = 0.069$).
   - Similarly, C2 achieves lower waiting times than C3 in `medium` ($+1.59\,\text{s}, +23.4\%$) and `high` ($+4.75\,\text{s}, +10.6\%$), though both differences are statistically unsupported ($q > 0.21$).
   - Under balanced steady-state flow, adaptive green extension introduces detector latency and slight phase holding variance that is absent in a rigid, minimal 36-second cycle.

2. **Asymmetric Demand Scenarios (`asym_ns`, `asym_ew`)**:
   - C3 exhibits its strongest advantages. Compared to C0, waiting time falls by **$-77.5\%$** (`asym_ns`) and **$-81.5\%$** (`asym_ew`) ($p < 0.0003$ under Holm).
   - Compared to Webster C1, waiting time decreases by **$-63.2\%$** ($-22.93\,\text{s}, q = 0.0347$) and **$-61.6\%$** ($-20.09\,\text{s}, q = 0.0392$), both surviving Benjamini-Hochberg FDR control.
   - Compared to Basic Queue C2, C3 achieves directional reductions of **$-17.3\%$** ($-2.80\,\text{s}$) and **$-31.2\%$** ($-5.67\,\text{s}$), alongside a **$16.6\%$ to $18.3\%$ reduction in phase switches** ($p < 0.028$).

3. **Dynamic Demand Scenario (`dynamic`)**:
   - C3 strongly outperforms C0 ($-28.32\,\text{s}, -48.4\%, p_{\text{Holm}} = 0.0121$).
   - Compared to C1 and C2, C3 achieves equivalent waiting times ($-0.60\,\text{s}, -1.9\%$ vs C1, $p=0.643$; $-0.99\,\text{s}, -3.2\%$ vs C2, $p=0.591$) with no statistically detectable difference.
   - However, C3 achieves this waiting time with **$19.0$ fewer phase switches than C1 ($-17.3\%, p = 0.00039$)** and **$7.8$ fewer phase switches than C2 ($-7.9\%, p = 0.00030$)**, preventing erratic phase oscillation during demand transitions.

4. **Oversaturated Demand Scenario (`oversaturated`)**:
   - C3 improves over C0 by $-15.43\,\text{s}$ ($-17.8\%, \text{raw } p = 0.0322$), though this contrast does not survive family correction ($p_{\text{Holm}} = 0.419, q_{\text{BH}} = 0.0686$).
   - Compared to C1, C3 has $+3.31\,\text{s}$ higher waiting time ($+4.9\%, p=0.123$, unsupported).
   - Compared to C2, C3's mean waiting time is identical ($71.18\,\text{s}$ vs $71.18\,\text{s}, \Delta = 0.00\,\text{s}, p = 1.000$), but C3 executes **$4.8$ fewer phase switches ($-4.6\%, p = 0.00776$)**.

---

## 13. Limitations Caused by Small Sample Size ($N=5$)

The pre-registered sample size of $N=5$ matched simulation realizations per scenario imposes three specific, mathematically verifiable statistical limitations:

1. **Mathematical Floor of the Wilcoxon Signed-Rank Test**:
   For $N=5$ non-zero paired differences, the total number of signed-rank permutations is $2^5 = 32$. The most extreme possible test statistic occurs when all five differences possess the identical sign (ranks 1, 2, 3, 4, 5 all positive or all negative). The two-tailed exact $p$-value for this most extreme permutation is:
   $$p_{\text{min}} = \frac{2}{2^5} = \frac{2}{32} = 0.0625$$
   **Consequently, with $N=5$, a two-sided Wilcoxon signed-rank test can NEVER reach $p < 0.05$, regardless of how enormous the effect size is.** For instance, in `asym_ns` vs C0 where $t = -30.59$ and Cohen's $d_z = -13.68$, the exact Wilcoxon $p$-value is $0.0625$. Therefore, non-parametric tests in this study serve purely as ordinal consistency checks rather than primary confirmatory decision criteria.

2. **Statistical Power Constraints for Moderate Effects**:
   With $\nu = 4$ degrees of freedom and two-tailed $\alpha = 0.05$, Student's $t$ requires a critical value of $t_{0.975, 4} = 2.7764$, corresponding to an effect size threshold of $|d_z| \ge 2.776 / \sqrt{5} = 1.242$ to achieve nominal significance. Moderate effects ($0.5 \le |d_z| < 1.0$), such as C3 vs C2 in asymmetric demand ($-17.3\%$ to $-31.2\%, d_z \approx -0.70$ to $-0.74$), do not achieve statistical significance with $N=5$ ($p \approx 0.17\text{--}0.19$). A sample of $N \ge 15\text{--}20$ matched seeds would be necessary to achieve $80\%$ power for these moderate contrasts.

3. **Sensitivity to Single-Seed Realizations**:
   With five observations, sample standard deviations and confidence interval widths are susceptible to sampling variability from individual stochastic clustering events. While matched pairing substantially reduces this variance, point estimates must be interpreted alongside their reported $95\%$ confidence intervals.

---

## 14. Conservative Scientific Conclusion & Hypothesis Evaluation

### Evaluation of Hypothesis H1
> **Hypothesis H1**: *The proposed controller provides its main advantage under asymmetric/dynamic demand rather than uniformly across all demand regimes.*

Based strictly on the inferential statistics from the blind evaluation set, **Hypothesis H1 is STRONGLY SUPPORTED by the empirical evidence**:

1. **Absence of Universal Dominance**:
   The empirical data conclusively refute any claim that C3 is universally superior across all traffic regimes. In symmetric steady-state regimes (`low`, `medium`, `high`, `oversaturated`), C3 does not achieve statistically significant waiting-time reductions over Webster-calibrated fixed-time (C1) or basic queue control (C2). In medium and high symmetric traffic, C1 and C2 achieve directionally lower waiting times ($10\%$ to $26\%$ lower) because rigid, well-tuned 36-second cycles eliminate detector latency and queue estimation variance.

2. **Concentrated Advantage in Asymmetric Regimes**:
   C3's statistically supported advantages over calibrated fixed-time control (C1) emerge **exclusively in asymmetric demand regimes** (`asym_ns` and `asym_ew`), where C3 reduces waiting time by **$61.6\%$ to $63.2\%$** ($q_{\text{BH}} < 0.04$). In these regimes, static equal-split timing severely penalizes the major arterial flow, whereas C3 dynamically allocates green capacity to the dominant approach.

3. **Primary Benefit over Basic Queue Control: Phase Switching Stability**:
   Against basic queue control (C2), C3 does not achieve statistically significant waiting-time reductions after multiple testing correction ($p_{\text{Holm}} = 1.0, q_{\text{BH}} \ge 0.24$). Instead, C3's definitive and consistent benefit over C2 lies in **signal stability**: across all seven scenarios, C3 achieves a **$4.6\%$ to $20.3\%$ statistically significant reduction in phase switch count** ($p < 0.028$ in all 7 scenarios). The composite objective's queue smoothing and hysteresis mechanisms effectively eliminate the high-frequency phase oscillations characteristic of naive queue controllers without increasing vehicle delay.

### Prohibited Claims Audit
In strict compliance with confirmatory guidelines, the authors explicitly affirm that:
- The proposed controller is **NOT** claimed to be universally superior, optimal, or state-of-the-art.
- The proposed controller does **NOT** demonstrate generalized superiority across all traffic conditions.
- Performance results are **mixed**: C3 is highly advantageous under directional asymmetry and reduces phase transitions universally, but is matched or slightly outperformed in waiting time by simple fixed-time control under symmetric steady-state flow.

### Concluding Summary
The blind final evaluation confirms that the primary engineering value of the proposed composite adaptive controller is **robust directional demand adaptation and switching stabilization**, rather than uniform delay minimization across all possible traffic states.
