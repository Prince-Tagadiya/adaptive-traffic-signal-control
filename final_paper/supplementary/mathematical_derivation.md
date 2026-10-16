# Mathematical Derivation of the Composite Adaptive Traffic Signal Controller

**Document**: `final_paper/supplementary/mathematical_derivation.md`  
**Target Journal**: *Journal of Intelligent Transportation Systems: Technology, Planning, and Operations* (Taylor & Francis)  
**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Implementation Verification**: Exact 1-to-1 correspondence with `controllers/proposed_adaptive_controller.py`

---

## 1. Problem Formulation & Intersection Topology

Consider an isolated four-arm orthogonal signalized intersection denoted $\mathcal{J}_0$. The intersection regulates two conflicting traffic movements:
- North-South direction ($d = \text{NS}$), encompassing incoming approaches $i \in \{N, S\}$.
- East-West direction ($d = \text{EW}$), encompassing incoming approaches $i \in \{E, W\}$.

Each approach link $i$ possesses a physical length of $L_{\text{link}} = 250\,\text{m}$, a single dedicated travel lane ($N_{\text{lane}} = 1$), and a regulatory free-flow speed limit of $v_{\text{max}} = 13.89\,\text{m/s}$ ($50\,\text{km/h}$).

The signal timing alternates between two primary green stages:
- **Phase 0**: Green for NS movements ($\text{state} = \texttt{GGgrrrGGgrrr}$).
- **Phase 1**: Yellow clearance for NS movements ($\text{state} = \texttt{yyyrrryyyrrr}$, duration $Y = 3\,\text{s}$).
- **Phase 2**: Green for EW movements ($\text{state} = \texttt{rrrGGgrrrGGg}$).
- **Phase 3**: Yellow clearance for EW movements ($\text{state} = \texttt{rrryyyrrryyy}$, duration $Y = 3\,\text{s}$).

The controller operates as a discrete-time feedback control system evaluated at uniform control time steps $\Delta t = 1.0\,\text{s}$.

---

## 2. Derivation Sequence

The decision-making architecture progresses through an explicit fourteen-stage mathematical derivation pipeline:

```
[1. Traffic State Observation]
         ↓
[2. Per-Approach Queue State Q_i(t)]
         ↓
[3. Rolling Arrival Estimation A_i(t)]
         ↓
[4. Queue-Growth Finite Difference g_i(t)]
         ↓
[5. Accumulated Waiting Burden W_i(t)]
         ↓
[6. Continuous Red-Age State R_d(t)]
         ↓
[7. Dimensionless Feature Normalization]
         ↓
[8. Composite Directional Priority S_d(t)]
         ↓
[9. Current Phase Comparison]
         ↓
[10. Hysteresis Condition S_opp > S_curr + H]
         ↓
[11. Minimum-Green Safety Constraint (G_min)]
         ↓
[12. Maximum-Green Hold Constraint (G_max)]
         ↓
[13. Starvation Override Constraint (R_starve)]
         ↓
[14. Yellow Clearance & Phase Transition (Y)]
```

---

## 3. Comprehensive Symbol and Variable Specification

| Symbol | Mathematical Definition | Physical Meaning | Unit | Observation Window | Normalization Scale | Role in Control Law |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| $Q_i(t)$ | $\sum_{v \in \mathcal{L}_i} \mathbb{I}(v(t) < 0.1)$ | Halting queue length on approach $i$ | veh | Instantaneous ($\Delta t = 1\,\text{s}$) | $Q_{\text{ref}} = 20.0\,\text{veh}$ | Primary congestion anchor ($\alpha = 1.00$) |
| $A_i(t)$ | $\frac{1}{10 W_A} \sum_{\tau=t-W_A}^t N_{\text{inflow}, i}(\tau)$ | Upstream vehicle arrival rate | veh/s | $W_A = 20\,\text{s}$ | $A_{\text{ref}} = 0.40\,\text{veh/s}$ | Anticipatory arrival pressure ($\beta = 0.75$) |
| $g_i(t)$ | $\frac{Q_i(t) - Q_i(t - W_G)}{W_G}$ | Queue growth rate (finite difference) | veh/s | $W_G = 10\,\text{s}$ | $G_{\text{ref}} = 0.50\,\text{veh/s}$ | Trend dampening / growth penalty ($\gamma = 0.10$) |
| $W_i(t)$ | $\frac{\sum_{v \in \text{halt}_i} w_v(t)}{\max(|\text{halt}_i|, 1)}$ | Average accumulated waiting time | s | Instantaneous | $W_{\text{ref}} = 30.0\,\text{s}$ | Delay burden weighting ($\delta = 0.25$) |
| $R_d(t)$ | $\int_0^t \mathbb{I}(\text{red}_d(\tau) \land Q_d(\tau) > 0) d\tau$ | Active unserviced red phase duration | s | Continuous since red | $R_{\text{ref}} = 50.0\,\text{s}$ | Continuous starvation prevention ($\eta = 0.25$) |
| $q_i(t)$ | $\min(Q_i(t) / Q_{\text{ref}}, 2.0)$ | Normalized approach queue | — | Instantaneous | Capped at $2.0$ | Dimensionless queue score |
| $a_i(t)$ | $\min(A_i(t) / A_{\text{ref}}, 2.0)$ | Normalized approach arrival rate | — | $W_A = 20\,\text{s}$ | Capped at $2.0$ | Dimensionless arrival score |
| $g_d(t)$ | $\sum_{i \in d} \max(0, \frac{g_i(t)}{G_{\text{ref}}})$ | Normalized positive queue growth | — | $W_G = 10\,\text{s}$ | Capped in $[-1.0, 1.0]$ | Dimensionless growth penalty |
| $w_i(t)$ | $\min(W_i(t) / W_{\text{ref}}, 2.0)$ | Normalized approach waiting burden | — | Instantaneous | Capped at $2.0$ | Dimensionless delay score |
| $r_d(t)$ | $\min(R_d(t) / R_{\text{ref}}, 1.0)$ | Normalized directional red age | — | Continuous | Capped at $1.0$ | Dimensionless fairness score |
| $S_d(t)$ | $\alpha \mathbf{q}_d + \beta \mathbf{a}_d + \gamma g_d + \delta \mathbf{w}_d + \eta r_d$ | Composite directional priority score | — | Control step | Linear combination | Deciding phase allocation |
| $H$ | $0.20$ | Switching hysteresis barrier | — | Constant | Calibrated | Prevents phase hunting |
| $G_{\text{min}}$| $15$ | Minimum green interval | s | Parameter | NEMA standard | Driver expectation / safety |
| $G_{\text{max}}$| $50$ | Maximum green interval | s | Parameter | NEMA standard | Upper green hold limit |
| $Y$ | $3$ | Yellow change clearance interval | s | Parameter | MUTCD / ITE | Intersection clearing |
| $R_{\text{starve}}$| $45$ | Mandatory starvation ceiling | s | Parameter | Operational safety | Hard override for waiting traffic |

---

## 4. Mathematical Derivation of Individual Terms

### 4.1 Halting Queue State $Q_i(t)$
For each incoming approach $i \in \{N, S, E, W\}$, the instantaneous halting queue is defined as the count of vehicles within link $\mathcal{L}_i$ whose speed has dropped below $v_{\text{halt}} = 0.1\,\text{m/s}$:
$$Q_i(t) = \sum_{v \in \mathcal{V}_i(t)} \mathbb{I}(v_v(t) < 0.1\,\text{m/s})$$
where $\mathcal{V}_i(t)$ is the set of all active vehicles on lane $i$.

**Normalization**:
Link length is $L = 250\,\text{m}$. With standard average vehicle length $4.5\,\text{m}$ and bumper-to-bumper queue gap $2.5\,\text{m}$ (effective headway $7.0\,\text{m}$), the jam storage capacity is approximately $35\,\text{veh}$. We set the nominal reference queue scale to:
$$Q_{\text{ref}} = 20.0\,\text{veh}$$
representing an extensive queue occupying $56\%$ of the physical approach link. The normalized queue term is:
$$q_i(t) = \min\left( \frac{Q_i(t)}{Q_{\text{ref}}}, 2.0 \right)$$
where the upper bound of $2.0$ prevents extreme queue outliers from saturating the objective function.

---

### 4.2 Upstream Arrival Rate $A_i(t)$
While $Q_i(t)$ captures currently halted vehicles, it fails to anticipate incoming platoons. To measure approaching pressure prior to queue impact, we observe vehicles within the advance entry zone:
$$\mathcal{V}_{\text{inflow}, i}(t) = \{v \in \mathcal{V}_i(t) \mid x_v(t) < 100.0\,\text{m}\}$$
where $x_v(t)$ is the longitudinal lane coordinate measured from the link entry.

The arrival rate is estimated over a rolling historical buffer of duration $W_A = 20\,\text{s}$:
$$A_i(t) = \frac{1}{10 \cdot |\mathcal{B}_i(t)|} \sum_{\tau \in \mathcal{B}_i(t)} |\mathcal{V}_{\text{inflow}, i}(\tau)|$$
where $\mathcal{B}_i(t) = \{t - W_A, \dots, t\}$ and the division by $10$ converts entry zone density into equivalent flow rate in $\text{veh/s}$.

**Normalization**:
Under ideal conditions, single-lane saturation flow is $s \approx 1800\,\text{veh/h} = 0.50\,\text{veh/s}$. The reference arrival scale is defined at $80\%$ of saturation capacity:
$$A_{\text{ref}} = 0.40\,\text{veh/s} \quad (1440\,\text{veh/h})$$
The normalized arrival term is:
$$a_i(t) = \min\left( \frac{A_i(t)}{A_{\text{ref}}}, 2.0 \right)$$

---

### 4.3 Queue Growth Finite Difference $g_i(t)$
Traffic queues do not remain static; rapidly forming queues require proactive green extension before severe spillback occurs. The discrete queue growth rate is computed via a backward finite difference over observation window $W_G = 10\,\text{s}$:
$$\dot{Q}_i(t) \approx \frac{Q_i(t) - Q_i(t - W_G)}{W_G}$$

**Normalization**:
At saturation inflow ($0.50\,\text{veh/s}$) with zero discharge (red phase), queues accumulate at a maximum theoretical rate of $0.50\,\text{veh/s}$. Setting $G_{\text{ref}} = 0.50\,\text{veh/s}$:
$$g_i(t) = \max\left( -1.0, \min\left( 1.0, \frac{Q_i(t) - Q_i(t - W_G)}{W_G \cdot G_{\text{ref}}} \right) \right)$$
When aggregating to directional movement $d \in \{\text{NS}, \text{EW}\}$, only positive queue expansion is penalized:
$$g_d(t) = \sum_{i \in d} \max(0.0, g_i(t))$$

---

### 4.4 Accumulated Waiting Burden $W_i(t)$
Queue length treats all queued vehicles equally, regardless of how long they have been stopped. To incorporate user delay equity, each vehicle's cumulative waiting duration $w_v(t)$ (seconds spent at $v < 0.1\,\text{m/s}$) is aggregated:
$$W_i(t) = \frac{\sum_{v \in \mathcal{V}_i(t), v_v < 0.1} w_v(t)}{\max(Q_i(t), 1)}$$

**Normalization**:
According to the Highway Capacity Manual (HCM 2010), the threshold between Level of Service (LOS) C and LOS D for signalized intersections is $35.0\,\text{s}$. We adopt a reference waiting burden scale of:
$$W_{\text{ref}} = 30.0\,\text{s}$$
The normalized waiting burden term is:
$$w_i(t) = \min\left( \frac{W_i(t)}{W_{\text{ref}}}, 2.0 \right)$$

---

### 4.5 Continuous Red-Age & Fairness Tracking $r_d(t)$
To prevent traffic on minor approaches from experiencing unacceptably long red intervals when opposing demand is continuously high, the controller tracks continuous unserviced red duration $R_d(t)$:
$$R_d(t) = \begin{cases} R_d(t-1) + \Delta t & \text{if phase } d \text{ is RED and } \sum_{i \in d} Q_i(t) > 0 \\ 0 & \text{if phase } d \text{ is GREEN or } \sum_{i \in d} Q_i(t) = 0 \end{cases}$$

**Normalization**:
The reference red duration is aligned with the maximum allowable green hold duration:
$$R_{\text{ref}} = G_{\text{max}} = 50.0\,\text{s}$$
The normalized continuous fairness term is:
$$r_d(t) = \min\left( \frac{R_d(t)}{R_{\text{ref}}}, 1.0 \right)$$

---

## 5. Composite Directional Priority Equation

The composite directional priority score $S_d(t)$ integrates all five normalized terms into a single scalar value:

$$S_{\text{NS}}(t) = \alpha \left( q_N(t) + q_S(t) \right) + \beta \left( a_N(t) + a_S(t) \right) + \gamma g_{\text{NS}}(t) + \delta \left( w_N(t) + w_S(t) \right) + \eta r_{\text{NS}}(t)$$

$$S_{\text{EW}}(t) = \alpha \left( q_E(t) + q_W(t) \right) + \beta \left( a_E(t) + a_W(t) \right) + \gamma g_{\text{EW}}(t) + \delta \left( w_E(t) + w_W(t) \right) + \eta r_{\text{EW}}(t)$$

**Physical Weight Interpretation**:
- $\alpha = 1.00$: Congestion anchor representing existing standing queues.
- $\beta = 0.75$: Strong forward-looking sensitivity to incoming vehicle platoons.
- $\gamma = 0.10$: Damped acceleration sensitivity penalizing rapid queue growth.
- $\delta = 0.25$: Proportional equity weight penalizing persistent vehicle delays.
- $\eta = 0.25$: Continuous aging pressure ensuring monotonic priority ramp for red approaches.

---

## 6. Constrained Decision Logic & Switching Law

Let $d_{\text{curr}} \in \{\text{NS}, \text{EW}\}$ denote the active green direction, $d_{\text{opp}}$ the competing red direction, and $t_{\text{green}}$ the elapsed duration in $d_{\text{curr}}$. The controller evaluates four sequential decision gates at every step $t$:

### Gate 1: Minimum Green Constraint (NEMA Safety)
$$\text{IF } t_{\text{green}} < G_{\text{min}} \quad (15\,\text{s}): \quad \text{Action} = \text{MAINTAIN GREEN}$$
Guarantees driver expectancy and pedestrian/vehicle clearance without premature cut-off.

### Gate 2: Maximum Green Constraint (Anti-Monopoly)
$$\text{IF } t_{\text{green}} \ge G_{\text{max}} \quad (50\,\text{s}) \land Q_{d_{\text{opp}}}(t) > 0: \quad \text{Action} = \text{INITIATE YELLOW CLEARANCE}$$
Forces stage termination if competing demand is present.

### Gate 3: Absolute Starvation Override
$$\text{IF } R_{d_{\text{opp}}}(t) \ge R_{\text{starve}} \quad (45\,\text{s}) \land Q_{d_{\text{opp}}}(t) > 0: \quad \text{Action} = \text{INITIATE YELLOW CLEARANCE}$$
Provides an absolute hard ceiling preventing minor approaches from being locked out.

### Gate 4: Hysteresis-Gated Pressure Comparison
If none of Gates 1–3 trigger, the controller compares composite scores under a hysteresis barrier $H = 0.20$:
$$\text{Decision}(t) = \begin{cases} \text{INITIATE YELLOW CLEARANCE} & \text{if } S_{d_{\text{opp}}}(t) > S_{d_{\text{curr}}}(t) + H \\ \text{MAINTAIN GREEN} & \text{otherwise} \end{cases}$$

**Role of Hysteresis**:
If $S_{d_{\text{opp}}} \approx S_{d_{\text{curr}}}$, a naive controller toggles green back and forth, losing $Y = 3\,\text{s}$ of intersection capacity to clearance yellow every cycle. The hysteresis margin $H = 0.20$ requires the competing approach to demonstrate a substantially greater traffic burden before justifying a phase transition, directly suppressing phase hunting.

---

## 7. Mathematical Consistency Proof with Codebase

A static audit confirms that the equations above map line-for-line to `controllers/proposed_adaptive_controller.py`:
- Lines 147–153: $Q_i(t)$ and FIFO queue buffer.
- Lines 156–160: Inflow filtering ($x < 100\,\text{m}$) and $A_i(t)$ averaging.
- Lines 163–170: $W_i(t)$ accumulated wait averaging.
- Lines 174–176: Normalization against $Q_{\text{ref}}, A_{\text{ref}}, W_{\text{ref}}$.
- Lines 179–186: Backward finite difference $g_i(t)$ over $W_G = 10\,\text{s}$.
- Lines 194–208: Consecutive red tracking $R_d(t)$ and $r_d(t)$.
- Lines 214–228: Exact linear combination for $S_{\text{NS}}(t)$ and $S_{\text{EW}}(t)$.
- Lines 240–262: Sequential evaluation of $G_{\text{min}}, G_{\text{max}}, R_{\text{starve}}$, and $S_{\text{opp}} > S_{\text{curr}} + H$.
