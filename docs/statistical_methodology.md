# Rigorous Statistical Methodology & Experimental Unit Audit

**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Document**: Formal Statistical Audit and Protocol Specification (Task 1)

---

## 1. Experimental Unit of Observation: Elimination of Pseudoreplication

In microscopic traffic simulation, a critical methodological error in existing literature is treating **individual vehicles** as independent experimental replications. 

### Why Vehicles are NOT Independent Experimental Units
1. **Dynamic Coupling**: Vehicles traversing the same signalized intersection interact through car-following dynamics, queue spillback, and shockwaves. A delayed vehicle directly causes delays to subsequent vehicles.
2. **Shared Traffic Signal Realization**: Every vehicle within a simulation run experiences the exact same signal timing decisions and phase transitions produced by the controller during that run.
3. **Pseudoreplication**: Pooling 200–500 vehicles within a single simulation run and calculating standard errors as $s / \sqrt{N_{\text{veh}}}$ produces severe pseudoreplication (Hurlbert, 1984), artificially deflating standard errors by a factor of $\sqrt{N_{\text{veh}}} \approx 15\text{--}25$ and yielding spuriously microscopic $p$-values.

### The Correct Experimental Unit
The primary experimental unit is the **complete simulation realization** defined by the tuple:
$$\mathcal{E} = (\text{Scenario } s, \text{ Random Seed } k)$$
where $s \in \{\text{low, medium, high, oversaturated, asym\_ns, asym\_ew, dynamic}\}$ and $k \in \{42, 43, 44, 45, 46\}$.
- **Number of Independent Observations**: $N = 5$ stochastic replications per scenario.
- **Independence**: Each seed initializes an independent Mersenne Twister pseudorandom number generator stream in SUMO, producing independent Poisson arrival realizations.

---

## 2. Matched-Pairs Experimental Design

Because all controllers evaluate the **exact same immutable demand file** for seed $k$, the comparison between controllers is strictly **paired**:

$$D_k = Y_{\text{candidate}, k} - Y_{\text{baseline}, k}$$

where $Y_{\cdot, k}$ denotes the aggregate evaluation metric (e.g., Cohort A average waiting time) for seed $k$.

Pairing eliminates inter-seed traffic variance (e.g., stochastic arrival clustering), isolating the true differential treatment effect of the signal controller.

---

## 3. Statistical Hypothesis Tests

### 3.1 Parametric Test: Paired-Samples Student's $t$-Test
Under the null hypothesis that the mean paired difference is zero:
$$H_0: \mu_D = 0 \quad \text{vs.} \quad H_1: \mu_D \neq 0$$
The test statistic is:
$$t = \frac{\bar{D}}{\text{SE}_D} = \frac{\frac{1}{N} \sum_{k=1}^N D_k}{\frac{s_D}{\sqrt{N}}}$$
where $s_D = \sqrt{\frac{1}{N-1} \sum_{k=1}^N (D_k - \bar{D})^2}$ is the sample standard deviation of paired differences with $\nu = N - 1 = 4$ degrees of freedom.

### 3.2 Non-Parametric Test: Wilcoxon Signed-Rank Test
For ordinal robustness without normality assumptions:
$$W = \sum_{k=1}^N \text{rank}(|D_k|) \cdot \text{sgn}(D_k)$$

> **Important Mathematical Note on Sample Size ($N=5$)**:
> For $N=5$ non-zero paired differences, the total number of signed rank permutations is $2^5 = 32$. The most extreme test statistic occurs when all differences have the identical sign (ranks 1, 2, 3, 4, 5 all positive or all negative). The two-tailed exact $p$-value for this most extreme possible case is:
> $$p_{\text{min}} = \frac{2}{2^5} = \frac{2}{32} = 0.0625$$
> **Therefore, with $N=5$, a two-sided Wilcoxon signed-rank test can NEVER achieve $p < 0.05$, regardless of how overwhelmingly superior the controller is.**
> Hence, exact parametric paired $t$-tests and effect sizes ($d_z$) must be reported alongside Wilcoxon $W$-statistics.

---

## 4. Confidence Intervals

Two-sided 95% confidence intervals for the true mean treatment difference $\mu_D$ are computed using Student's $t$-distribution:

$$\text{CI}_{95\%} = \left[ \bar{D} - t_{0.975, 4} \cdot \frac{s_D}{\sqrt{N}}, \quad \bar{D} + t_{0.975, 4} \cdot \frac{s_D}{\sqrt{N}} \right]$$

For $\nu = 4$, the critical value is $t_{0.975, 4} = 2.7764$.

---

## 5. Standardized Effect Size: Paired Cohen's $d_z$

In paired designs, Cohen's $d_z$ quantifies the standardized mean difference relative to the variability of the difference scores:

$$d_z = \frac{\bar{D}}{s_D}$$

Interpretation (Cohen, 1988):
- $|d_z| \ge 0.2$: Small effect
- $|d_z| \ge 0.5$: Medium effect
- $|d_z| \ge 0.8$: Large effect
- $|d_z| \ge 2.0$: Extremely large effect (typical in signal control where fixed-time delay is massive).

---

## 6. Multiple-Comparison Corrections

When evaluating multiple controllers across 7 scenarios (28 simultaneous hypotheses), uncorrected $p$-values risk Type I inflation. We apply two rigorous corrections:

### 6.1 Holm-Bonferroni Step-Down Procedure (Controls FWER)
Sort raw $p$-values in ascending order: $p_{(1)} \le p_{(2)} \le \dots \le p_{(m)}$.
The adjusted $p$-value at rank $j$ is:
$$p_{\text{adj},(j)} = \min\left(1, \max_{k \le j} (m - k + 1) p_{(k)}\right)$$
Guarantees Family-Wise Error Rate $\le 0.05$.

### 6.2 Benjamini-Hochberg Procedure (Controls False Discovery Rate)
Controls the expected proportion of false discoveries:
$$p_{\text{FDR},(j)} = \min\left(1, \min_{k \ge j} \frac{m \cdot p_{(k)}}{k}\right)$$

Both raw and corrected $p$-values are reported in `results/statistical_tests_verified.csv`.
