# Experimental Methodology & Evaluation Protocol

**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Document**: Methodological Specification for Adaptive Traffic Signal Research

---

## 1. Core Research Principle: One Realization $\rightarrow$ Multiple Controllers

To ensure rigorous, scientifically defensible comparative evaluation, the evaluation pipeline strictly enforces:

$$\text{Traffic Demand Realization } \omega \longrightarrow \{\text{Fixed-Time Controller}, \text{Basic Queue Controller}, \text{Proposed Adaptive Controller}\}$$

Controllers **never** generate routes dynamically during simulation execution. Instead, every simulation run binds to an immutable, pre-generated SUMO route file ($\text{rou.xml}$) specifying the exact vehicle insertion times, vehicle IDs, and origin-destination routes.

All 37 static route files are stored in `scenarios/demand/`:
- Calibration Scenarios: `calib_medium_seed101.rou.xml`, `calib_high_seed102.rou.xml`
- Test Demand Profiles:
  - Low Demand ($p=0.04$, approx. 576 veh/h) across Seeds 42–46
  - Medium Demand ($p=0.08$, approx. 1,152 veh/h) across Seeds 42–46
  - High Demand ($p=0.14$, approx. 2,016 veh/h) across Seeds 42–46
  - Oversaturated Demand ($p=0.18$, approx. 2,592 veh/h) across Seeds 42–46
  - Asymmetric North-South ($p_{NS}=0.14, p_{EW}=0.03$) across Seeds 42–46
  - Asymmetric East-West ($p_{NS}=0.03, p_{EW}=0.14$) across Seeds 42–46
  - Temporally Dynamic Demand across Seeds 42–46

---

## 2. Strict Warm-Up Boundary and Cohort Isolation

In microscopic traffic simulation, a network starting empty requires a transient warm-up phase to populate links to steady-state density. For our 200m approach arms, free-flow travel time is approx. $15\text{s}$, making a $T_{\text{warmup}} = 200\text{s}$ warm-up period sufficient.

To prevent boundary contamination, completed vehicles are strictly categorized into disjoint cohorts:

### Cohort A: Pure Post-Warmup Evaluation Cohort (Primary Paper Metric)
$$\text{Cohort A} = \{v \in \mathcal{V} \mid t_{\text{depart}}(v) \ge T_{\text{warmup}} \land t_{\text{arrival}}(v) \ge T_{\text{warmup}}\}$$
- **Characteristics**: Inserted after network has reached dynamic equilibrium; completes entirely within the evaluation window ($t \in [200\text{s}, 1000\text{s}]$).
- **Integrity**: Zero boundary bleed. No pre-warmup delays or initialization artifacts are included in average waiting time, average delay, or travel time.

### Cohort B: Boundary-Crossing Cohort
$$\text{Cohort B} = \{v \in \mathcal{V} \mid t_{\text{depart}}(v) < T_{\text{warmup}} \land t_{\text{arrival}}(v) \ge T_{\text{warmup}}\}$$
- **Characteristics**: Departed during network loading; clears the intersection after warm-up.
- **Reporting**: Tracked separately for full accounting, but excluded from primary Cohort A statistics to maintain strict comparability.

### Cohort C: Pure Warm-Up Cohort
$$\text{Cohort C} = \{v \in \mathcal{V} \mid t_{\text{depart}}(v) < T_{\text{warmup}} \land t_{\text{arrival}}(v) < T_{\text{warmup}}\}$$
- Discarded from evaluation metrics.

---

## 3. Mathematical Metric Definitions

### 3.1 Average Waiting Time ($W_{\text{avg}}$)
For each vehicle $v$, waiting time is the total cumulative time spent with speed $u_v(t) < 0.1\text{ m/s}$:
$$W_v = \sum_{t=t_{\text{dep}}}^{t_{\text{arr}}} \mathbb{I}(u_v(t) < 0.1) \cdot \Delta t$$
$$W_{\text{avg}} = \frac{1}{|\text{Cohort A}|} \sum_{v \in \text{Cohort A}} W_v \quad [\text{s/veh}]$$

### 3.2 Average Delay / Time Loss ($d_{\text{avg}}$)
Delay is defined as the difference between actual travel time and ideal free-flow travel time:
$$d_v = (t_{\text{arrival}} - t_{\text{depart}}) - \frac{L_v}{u_{\text{free}}}$$
$$d_{\text{avg}} = \frac{1}{|\text{Cohort A}|} \sum_{v \in \text{Cohort A}} d_v \quad [\text{s/veh}]$$

### 3.3 Average Queue Length ($Q_{\text{avg}}$)
Calculated every second over the evaluation duration ($t \in [200\text{s}, 1000\text{s}]$):
$$Q(t) = \sum_{i \in \{N, S, E, W\}} Q_i(t) = \sum_{i} \sum_{v \in \mathcal{L}_i(t)} \mathbb{I}(u_v(t) < 0.1)$$
$$Q_{\text{avg}} = \frac{1}{T_{\text{eval}}} \sum_{t=T_{\text{warmup}}}^{T_{\text{sim}}} Q(t) \quad [\text{vehicles}]$$

### 3.4 Phase Switching Overhead ($N_{\text{switch}}$) & Yellow Lost Time ($Y_{\text{lost}}$)
$$N_{\text{switch}} = \sum_{t=1}^{T_{\text{sim}}} \mathbb{I}(\phi(t) \neq \phi(t-1))$$
$$Y_{\text{lost}} = \sum_{t=1}^{T_{\text{sim}}} \mathbb{I}(\phi(t) \in \{\text{Phase 1 (NS Yellow)}, \text{Phase 3 (EW Yellow)}\}) \quad [\text{s}]$$

---

## 4. Controlled Statistical Testing Protocol

To avoid reporting selective or anecdotal improvements:
1. **Matched-Pair Design**: Differences $D_k = \text{Metric}_{\text{proposed},k} - \text{Metric}_{\text{baseline},k}$ are computed on identical seeds $k \in \{42, 43, 44, 45, 46\}$.
2. **Confidence Intervals**: 95% two-sided confidence intervals using Student's $t$-distribution with $\nu = N - 1 = 4$ degrees of freedom:
   $$\text{CI}_{95\%} = \bar{D} \pm t_{0.975, 4} \cdot \frac{s_D}{\sqrt{N}}$$
3. **Statistical Significance**: Both parametric (paired Student's $t$-test) and non-parametric (Wilcoxon signed-rank test) p-values are reported.
4. **Effect Size**: Cohen's $d = \bar{D} / s_D$ quantifies practical significance.
