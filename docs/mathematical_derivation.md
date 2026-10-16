# Mathematical Derivation and Specification of Candidate Adaptive Signal Controller

This document presents the complete, rigorous mathematical formulation for the proposed candidate adaptive traffic signal controller. Every variable, unit, normalization constant, and control rule is explicitly defined.

---

## 1. Intersection State and Approach Variables

Consider an isolated four-arm intersection with index $i \in \mathcal{I} = \{N, S, E, W\}$, where each approach arm has length $L_i = 250\text{ m}$ and speed limit $v_{\text{max}} = 13.89\text{ m/s}$ (50 km/h).

Traffic phases are defined as:
- $\phi_{NS}$: North–South Green (serving approaches $N$ and $S$)
- $\phi_{EW}$: East–West Green (serving approaches $E$ and $W$)

At each discrete simulation step $t \in \mathbb{N}$ (step length $\Delta t = 1.0\text{ s}$), the controller observes the following state variables for each approach $i$:

### 1.1 Queue Length $Q_i(t)$
The number of halting vehicles on the incoming lane of approach $i$:
$$Q_i(t) = \sum_{v \in \mathcal{V}_i(t)} \mathbb{I}(v_{\text{speed}}(v, t) < v_{\text{queue\_thresh}})$$
where $v_{\text{queue\_thresh}} = 0.1\text{ m/s}$, $\mathcal{V}_i(t)$ is the set of vehicles on the approach lane, and $\mathbb{I}(\cdot)$ is the indicator function.
- **Units**: Vehicles ($\text{veh}$)

### 1.2 Rolling Arrival Rate $A_i(t)$
The rate of newly arriving vehicles entering approach $i$ measured over a backward rolling window $W_A$:
$$A_i(t) = \frac{N_{\text{inflow}, i}(t - W_A, t)}{W_A}$$
where $N_{\text{inflow}, i}(t - W_A, t)$ is the count of vehicles injected onto approach $i$ in $[t - W_A, t]$, and $W_A = 20\text{ s}$.
- **Units**: Vehicles per second ($\text{veh/s}$)

### 1.3 Queue Growth Rate $G_i(t)$
The discrete time-derivative of queue accumulation over a backward finite-difference window $W_G$:
$$G_i(t) = \frac{Q_i(t) - Q_i(t - W_G)}{W_G}$$
where $W_G = 10\text{ s}$.
- $G_i(t) > 0$ indicates queue accumulation (arrival exceeds discharge).
- $G_i(t) < 0$ indicates queue dissipation.
- **Units**: Vehicles per second ($\text{veh/s}$)

### 1.4 Waiting Burden $W_i(t)$ and Average Queue Wait $AW_i(t)$
The total accumulated waiting time across all vehicles currently halted in the queue on approach $i$:
$$W_i(t) = \sum_{v \in \mathcal{Q}_i(t)} w_{\text{accum}}(v, t)$$
where $\mathcal{Q}_i(t)$ is the set of halting vehicles on approach $i$, and $w_{\text{accum}}(v, t)$ is the total duration vehicle $v$ has spent halted since its departure.
The average waiting burden per queued vehicle is:
$$AW_i(t) = \frac{W_i(t)}{\max(Q_i(t), 1)}$$
- **Units**: Seconds ($\text{s}$)

### 1.5 Red Elapsed Time $R_i(t)$
The continuous elapsed duration during which approach $i$ has experienced a red indication while demand is present:
$$R_i(t) = \begin{cases} R_i(t-1) + 1 & \text{if phase of approach } i \text{ is RED and } Q_i(t) > 0 \\ 0 & \text{if phase of approach } i \text{ is GREEN or } Q_i(t) = 0 \end{cases}$$
- **Units**: Seconds ($\text{s}$)

### 1.6 Saturation Discharge Rate $C_i(t)$
The estimated vehicle service capacity of approach $i$ during a green indication. Under single-lane saturation with headway $h_{\text{sat}} \approx 2.0\text{ s/veh}$, the nominal saturation flow is:
$$C_{\text{sat}, i} = 0.5\text{ veh/s} \quad (1,800\text{ veh/hr})$$
When the phase is active and discharging, $C_i(t) = C_{\text{sat}, i}$; when red, $C_i(t) = 0$.
- **Units**: Vehicles per second ($\text{veh/s}$)

### 1.7 Downstream Occupancy $O_i(t)$
In an isolated four-arm intersection, departure links lead to unrestricted network exit sinks ($250\text{ m}$ length with free-flow boundary). Consequently, downstream spillback does not occur in this single-intersection topology:
$$O_i(t) = 0$$
*Limitation Documented*: In multi-intersection arterial networks, $O_i(t)$ would capture downstream queue spillback to penalize green extensions.

---

## 2. Dimensionless Normalization

Because the state variables have distinct physical units ($\text{veh}$, $\text{veh/s}$, $\text{s}$), they must be normalized by calibrated reference values prior to linear combination:

| Variable | Raw Unit | Reference Constant | Meaning of Reference Constant |
| :--- | :--- | :--- | :--- |
| $Q_i$ | $\text{veh}$ | $Q_{\text{ref}} = 20.0\text{ veh}$ | Approximate storage capacity of a $250\text{ m}$ lane ($\approx 33\text{ veh}$; $20\text{ veh}$ represents high congestion) |
| $A_i$ | $\text{veh/s}$ | $A_{\text{ref}} = 0.4\text{ veh/s}$ | Heavy inflow rate ($1,440\text{ veh/hr/arm}$) |
| $G_i$ | $\text{veh/s}$ | $G_{\text{ref}} = 0.5\text{ veh/s}$ | Maximum queue accumulation rate equal to nominal saturation capacity |
| $AW_i$ | $\text{s}$ | $W_{\text{ref}} = 30.0\text{ s}$ | Tolerable average delay threshold per vehicle |
| $R_i$ | $\text{s}$ | $R_{\text{ref}} = 50.0\text{ s}$ | Maximum acceptable continuous red wait |

The normalized dimensionless components are:
$$q_i(t) = \min\left(\frac{Q_i(t)}{Q_{\text{ref}}}, 2.0\right)$$
$$a_i(t) = \min\left(\frac{A_i(t)}{A_{\text{ref}}}, 2.0\right)$$
$$g_i(t) = \text{clip}\left(\frac{G_i(t)}{G_{\text{ref}}}, -1.0, 1.0\right)$$
$$w_i(t) = \min\left(\frac{AW_i(t)}{W_{\text{ref}}}, 2.0\right)$$
$$r_i(t) = \min\left(\frac{R_i(t)}{R_{\text{ref}}}, 1.0\right)$$

---

## 3. Phase Aggregation and Composite Phase Score

For each candidate green phase $p \in \{NS, EW\}$, we aggregate the normalized terms across the approach arms served by phase $p$:

$$Q_p(t) = q_{p, 1}(t) + q_{p, 2}(t)$$
$$A_p(t) = a_{p, 1}(t) + a_{p, 2}(t)$$
$$G_p(t) = \max(0, g_{p, 1}(t)) + \max(0, g_{p, 2}(t))$$
$$W_p(t) = w_{p, 1}(t) + w_{p, 2}(t)$$
$$R_p(t) = \max\left(r_{p, 1}(t), r_{p, 2}(t)\right)$$

### 3.1 Composite Phase Pressure Score $S_p(t)$
The dimensionless composite priority score for phase $p$ is defined as:
$$S_p(t) = \alpha Q_p(t) + \beta A_p(t) + \gamma G_p(t) + \delta W_p(t) + \eta R_p(t)$$
where:
- $\alpha$: Weight on instantaneous queue backlog ($1.0$)
- $\beta$: Weight on short-term arrival momentum ($0.5$)
- $\gamma$: Weight on positive queue growth rate ($0.3$)
- $\delta$: Weight on accumulated waiting penalty ($0.4$)
- $\eta$: Weight on continuous fairness/red-aging ($0.4$)

---

## 4. Control Decision Logic and Safety Constraints

### 4.1 Safety Constraints
1. **Minimum Green Duration ($G_{\text{min}} = 15\text{ s}$)**:
   A green phase must remain active for at least $G_{\text{min}}$ seconds before any termination can be considered:
   $$\text{If } t_{\text{green}} < G_{\text{min}} \implies \text{MAINTAIN CURRENT GREEN}$$
2. **Maximum Green Duration ($G_{\text{max}} = 50\text{ s}$)**:
   If competing demand exists and current green reaches $G_{\text{max}}$, a phase transition is forced:
   $$\text{If } t_{\text{green}} \ge G_{\text{max}} \text{ and } Q_{\text{other}}(t) > 0 \implies \text{FORCE SWITCH}$$
3. **Yellow Clearance Interval ($Y = 3.0\text{ s}$)**:
   Direct green-to-green transitions are prohibited. Every phase switch incurs a mandatory $3.0\text{ s}$ yellow phase (`yyyrrryyyrrr` or `rrryyyrrryyy`).

### 4.2 Hysteresis Margin $H$
To prevent chattering and wasteful yellow phase transitions under noisy score fluctuations, phase switching requires the competing score to exceed the active score by a positive hysteresis margin $H$:
$$S_{\text{competing}}(t) > S_{\text{active}}(t) + H$$
where $H = 0.25$ (dimensionless).

### 4.3 Starvation Prevention
In addition to the continuous fairness score $\eta R_p$, an absolute ceiling is enforced: if $R_{\text{competing}}(t) \ge 45\text{ s}$ and $Q_{\text{competing}} > 0$, the controller triggers a switch once $G_{\text{min}}$ has elapsed.

---

## 5. Formal Pseudocode

```text
Algorithm: Proposed Adaptive Traffic Signal Controller

Input:
  Traffic state from TraCI (halting counts, vehicle inflows, speeds, wait times)
  Current phase state: phase_state ∈ {NS_GREEN, NS_YELLOW, EW_GREEN, EW_YELLOW}
  Elapsed phase duration: t_green, t_yellow
  Historical queues: Q_i(t - W_G)
  Historical inflows: N_in,i(t - W_A, t)

Output:
  Updated traffic light phase command to SUMO

Parameters:
  G_min = 15, G_max = 50, Y = 3, H = 0.25
  W_A = 20, W_G = 10, R_starve = 45
  Weights: α = 1.0, β = 0.5, γ = 0.3, δ = 0.4, η = 0.4

Step 1: Measure Approach States
  For each approach i ∈ {N, S, E, W}:
    Q_i(t) ← halting vehicle count (v < 0.1 m/s)
    A_i(t) ← arrivals in last W_A seconds / W_A
    G_i(t) ← [Q_i(t) - Q_i(t - W_G)] / W_G
    W_i(t) ← accumulated wait of queued vehicles on approach i
    AW_i(t) ← W_i(t) / max(Q_i(t), 1)
    If approach i is RED and Q_i(t) > 0: R_i(t) ← R_i(t-1) + 1 else R_i(t) ← 0

Step 2: Normalize Variables
  For each approach i:
    q_i ← min(Q_i / 20.0, 2.0)
    a_i ← min(A_i / 0.4, 2.0)
    g_i ← clip(G_i / 0.5, -1.0, 1.0)
    w_i ← min(AW_i / 30.0, 2.0)
    r_i ← min(R_i / 50.0, 1.0)

Step 3: Aggregate Phase Metrics
  For each phase p ∈ {NS, EW}:
    Q_p ← q_p1 + q_p2
    A_p ← a_p1 + a_p2
    G_p ← max(0, g_p1) + max(0, g_p2)
    W_p ← w_p1 + w_p2
    R_p ← max(r_p1, r_p2)
    S_p ← α*Q_p + β*A_p + γ*G_p + δ*W_p + η*R_p

Step 4: Execute State Transitions
  If phase_state == NS_GREEN:
    t_green ← t_green + 1
    If t_green < G_min:
      Action ← MAINTAIN (Reason: MIN_GREEN_HOLD)
    Else If t_green >= G_max and Q_EW > 0:
      Action ← SWITCH (Reason: MAX_GREEN_EXCEEDED)
    Else If R_EW >= R_starve and Q_EW > 0:
      Action ← SWITCH (Reason: STARVATION_CEILING)
    Else If S_EW > S_NS + H:
      Action ← SWITCH (Reason: PRESSURE_SWITCH_EW_HIGHER)
    Else:
      Action ← MAINTAIN (Reason: PRESSURE_MAINTAIN_NS)

    If Action == SWITCH:
      phase_state ← NS_YELLOW, t_yellow ← 0, setPhase(1)

  Else If phase_state == NS_YELLOW:
    t_yellow ← t_yellow + 1
    If t_yellow >= Y:
      phase_state ← EW_GREEN, t_green ← 0, setPhase(2)

  Else If phase_state == EW_GREEN:
    t_green ← t_green + 1
    If t_green < G_min:
      Action ← MAINTAIN (Reason: MIN_GREEN_HOLD)
    Else If t_green >= G_max and Q_NS > 0:
      Action ← SWITCH (Reason: MAX_GREEN_EXCEEDED)
    Else If R_NS >= R_starve and Q_NS > 0:
      Action ← SWITCH (Reason: STARVATION_CEILING)
    Else If S_NS > S_EW + H:
      Action ← SWITCH (Reason: PRESSURE_SWITCH_NS_HIGHER)
    Else:
      Action ← MAINTAIN (Reason: PRESSURE_MAINTAIN_EW)

    If Action == SWITCH:
      phase_state ← EW_YELLOW, t_yellow ← 0, setPhase(3)

  Else If phase_state == EW_YELLOW:
    t_yellow ← t_yellow + 1
    If t_yellow >= Y:
      phase_state ← NS_GREEN, t_green ← 0, setPhase(0)

Step 5: Log Decision
  Record all raw, normalized, and composite terms with timestamp and decision rationale.
```
