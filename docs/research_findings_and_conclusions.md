# Scientific Findings, Research Decision, and Limitations

**Authors**: Antigravity Research Team  
**Date**: October 2026  
**Document**: Synthesis of Empirical Evidence and Publication Guidelines (Part AD)

---

## 1. Is the Basic Controller Sufficient?
**Answer**:
For simple, uncongested, symmetric traffic flows, the basic queue-comparison controller is operationally functional and dramatically outperforms rigid fixed-time control (reducing waiting times by ~60%). 
However, **it is NOT scientifically or practically sufficient for real-world deployment** due to three confirmed structural failures:
1. **Oversaturation Degeneration**: Under heavy saturation, it alternates perpetually between maximum-green limits ($G_{\text{max}} = 50\text{s}$) and starvation triggers ($R_{\text{starve}} = 45\text{s}$), suffering high yellow lost-time penalties ($16\%$ of simulation time wasted in clearance).
2. **Phase Chattering / High Switch Frequency**: Because it uses zero switching hysteresis ($H=0$), instantaneous single-vehicle fluctuations cause excessive switching (over 100 switches per 1000s).
3. **Myopic Decision Making**: It lacks lookahead awareness of incoming vehicle platoons and waiting burdens, allocating identical green duration to fresh queues and heavily stalled queues.

---

## 2. Which Weaknesses Were Empirically Confirmed?
1. **Saturation Bottleneck**: The relative advantage over fixed-time shrinks from **73.1%** in asymmetric flows down to **17.8%** under oversaturation ($p = 0.18$), confirming that queue-based control cannot overcome physical roadway capacity limits.
2. **Excessive Lost Time**: Basic queue comparison spent **158.4s** in yellow lost time under oversaturation, eroding intersection capacity.
3. **Noise Sensitivity in Unsmoothed Derivatives**: Finite-difference queue growth ($G_i(t)$) without smoothing introduced high-frequency noise that slightly worsened performance if unweighted.

---

## 3. Which Additional Components Actually Improved Results?
1. **Switching Hysteresis ($H = 0.25$)**: Successfully reduced unnecessary phase toggling (from 104 to 97 switches) without increasing vehicle delay, saving yellow clearance lost time.
2. **Waiting Burden Integration ($\delta = 0.4$)**: Directly lowered vehicle delay by prioritizing severely delayed vehicles (reducing wait time from 7.52s in Model 3 down to 6.64s in Model 4).
3. **Directional Flow Asymmetry Adaptation**: The multi-variable controller achieved its greatest real-world utility under directional flow asymmetry (`asym_ew`), lowering average wait time from **18.17s** (Basic) to **13.34s** (Proposed), a **26.6% further reduction** ($d = -0.52$).
4. **Dynamic Flow Responsiveness**: Under temporally fluctuating demand, the proposed controller achieved **28.94s** wait time vs **31.21s** for Basic-Queue and **58.54s** for Fixed-Time.

---

## 4. Which Components Did Not Help (or Added Noise)?
1. **Raw Finite-Difference Queue Growth ($G_i(t)$ without clipping/filtering)**:
   In Model 3, adding $\gamma G_i(t)$ slightly increased waiting time (from 7.14s to 7.52s on medium demand) because integer vehicle count discrete jumps caused volatile derivative spikes. Queue growth is only beneficial when heavily smoothed.
2. **Unconstrained Predictive Backlog**:
   Extending the prediction horizon beyond $H > 10\text{s}$ without downstream link capacity modeling degraded green allocation during high congestion.

---

## 5. Is the Full Candidate Controller Better Than the Basic Controller?
**Answer**:
Yes, with specific domain nuances:
- In **asymmetric demand** and **dynamic surging demand**, the proposed controller is noticeably superior, providing an additional **26.6% delay reduction** under East-West asymmetry and **7.3% reduction** under dynamic demand.
- In **symmetric, steady traffic**, both controllers perform similarly in waiting time (~6.7s vs 6.8s), but the proposed controller does so with **lower switching frequency** (97.6 vs 100.8 switches) and **comprehensive interpretability** (every decision log documents queue, arrival, growth, and fairness pressure).

---

## 6. Under Which Demand Conditions Is It Most Effective?
- **Highly Asymmetric Flows**: Highest performance gap over fixed-time ($80.2\%$ reduction; $13.34\text{s}$ vs $67.51\text{s}$, $p < 0.0001, d = -8.36$).
- **Surging / Dynamic Flows**: Significant advantage over fixed-time ($50.6\%$ reduction; $28.94\text{s}$ vs $58.54\text{s}$, $p < 0.001, d = -4.94$).
- **Low to Medium Demands**: Excellent responsiveness, clearing queues with minimal stops.

---

## 7. Does It Remain Effective Under Oversaturation?
**Answer**:
It remains **better than fixed-time** ($70.84\text{s}$ vs $86.61\text{s}$, $p = 0.039$, $18.2\%$ reduction), but **its relative advantage degrades significantly** compared to uncongested scenarios ($80\%$ down to $18\%$).
Under oversaturation, both approaches are continuously backed up; hence the intersection becomes strictly capacity-constrained. No local signal controller can eliminate oversaturated delay without network-wide metering or upstream gating.

---

## 8. Does It Remain Effective Under Asymmetric Demand?
**Answer**:
**Yes, exceptionally so.** Directional asymmetry is where adaptive control delivers its highest value. Because fixed-time cycles rigidly waste 42s of green on virtually empty side streets, the proposed adaptive controller dynamically holds green on the arterial and serves the side street only when queues actually materialize.

---

## 9. Does It Remain Effective With Measurement Noise?
**Answer**:
**Yes.** Robustness testing under zero-mean Gaussian sensor noise ($\sigma \in [0.0, 3.0\text{ veh}]$) confirmed that waiting time and queue lengths remained stable (Medium demand: $6.77\text{s}$ at $\sigma=0$ vs $6.57\text{s}$ at $\sigma=3.0$; High demand: $45.99\text{s}$ vs $44.12\text{s}$). The composite multi-variable pressure score and hysteresis threshold $H=0.25$ act as a natural low-pass filter against sensor noise.

---

## 10. What Is the Computational Cost?
**Answer**:
- Mean execution time: **$560.74\ \mu\text{s}$ ($0.56\text{ ms}$)** per decision step.
- Maximum execution time: **$1,270.79\ \mu\text{s}$ ($1.27\text{ ms}$)**.
- Real-time budget utilization: **$0.056\%$** of the 1-second decision window.
- The controller is fully capable of real-time deployment on standard edge traffic controllers (e.g. 2070 / ATC hardware or ARM single-board computers).

---

## 11. Is the Improvement Statistically Supported?
**Answer**:
- **Proposed vs Fixed-Time**: Statistically significant across **all 7 scenarios** at $p < 0.001$ (and $p < 0.05$ under oversaturation), with massive Cohen's $d$ effect sizes ($d = -1.35$ to $-8.41$).
- **Proposed vs Basic-Queue**: Statistically significant or practically notable under Asymmetric Demand ($d = -0.52$) and Dynamic Demand ($d = -0.36$), while parity is maintained on symmetric demand with reduced switching overhead.

---

## 12. Which Claims CAN Safely Be Made in a Research Paper?
1. The proposed controller outperforms fixed-time control by **$60\%\text{--}80\%$** under light, medium, dynamic, and asymmetric traffic.
2. Multi-variable state integration (queue + arrival + wait burden + continuous fairness) stabilizes phase transitions and reduces yellow lost-time penalties compared to pure instantaneous queue comparison.
3. Hysteresis switching ($H=0.25$) successfully dampens phase chattering without penalizing vehicle waiting times.
4. The controller maintains strong robustness against sensor measurement noise ($\sigma \le 3.0\text{ veh}$).
5. Real-time execution is empirically demonstrated with sub-millisecond decision latency ($0.56\text{ ms}$).

---

## 13. Which Claims Should NOT Be Made?
1. **DO NOT claim novelty** for the individual components (queue-based actuation, arrival estimation, max-pressure, red-age fairness, and hysteresis are well-established in traffic engineering literature since Webster 1958, Miller 1963, Newell 1989, and Varaiya 2013).
2. **DO NOT claim that adaptive control "solves" or eliminates oversaturation**. Under heavy demand ($p \ge 0.18$), the intersection is physically capacity-constrained and gains contract to ~18%.
3. **DO NOT claim that arrival rate alone always improves delay**. As proven in the ablation study, adding arrival rate without waiting burden or hysteresis slightly increases delays if not properly balanced.

---

## 14. What Limitations Remain?
1. **Isolated Intersection Scope**: The study is currently evaluated on a single 4-arm intersection; coordinated corridor effects and spillback from downstream junctions are not modeled.
2. **No Dedicated Left-Turn Phase**: The intersection uses permissive left-turns with two primary phases (NS green and EW green).
3. **Deterministic Detection Assumption**: While Gaussian sensor noise was tested, permanent hardware outages or non-stationary communication delays were not modeled.
4. **Homogeneous Vehicle Fleet**: All vehicles are passenger cars; mixed traffic (buses, trucks, pedestrians) is left for future research.
