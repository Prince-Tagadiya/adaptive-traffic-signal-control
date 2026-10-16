# Novelty Audit and Prior Literature Mapping

## 1. Established Concepts in Traffic Signal Literature

A rigorous review of signal control literature confirms that the following mechanisms are already well-established:

| Mechanism | Foundational Literature / Prior Art | What It Does | Why It Cannot Be Claimed as Novel |
| :--- | :--- | :--- | :--- |
| **Queue-Based Control** | Webster (1958), Miller (1963), Newell (1989) | Allocates green time based on measured queue lengths. | Foundational concept in traffic control for over 60 years. |
| **Actuated Signal Control** | NEMA TS-2 Standard, FHWA Signal Timing Manual | Extends green time based on vehicle presence/gap-out. | Industry standard in civil engineering since the 1970s. |
| **Max-Pressure Control** | Tassiulas & Ephremides (1990), Varaiya (2013) | Selects phases based on queue differential between upstream and downstream links. | Extensively published and established mathematical framework. |
| **Delay / Waiting-Time Burden** | Smith (1979), Hunt et al. (SCOOT, 1981), Gartner (OPAC, 1983) | Factors accumulated delay of waiting vehicles into phase priority. | Core principle of modern urban traffic control systems. |
| **Arrival-Rate Estimation** | Robertson (TRANSYT, 1969), Lowrie (SCATS, 1990) | Uses detector actuation to estimate upstream vehicle arrival rates. | Standard traffic surveillance technique. |
| **Queue Growth Rate** | Helbing (2005), Lämmer & Helbing (2008) | Monitors the derivative of queue accumulation ($\frac{dQ}{dt}$) to anticipate spillback. | Published in self-organizing traffic signal literature. |
| **Hysteresis in Phase Switching** | Lämmer & Helbing (2008), Cools et al. (2010) | Requires competing phase score to exceed current score by a margin $H$ before switching. | Well-known control theory technique to avoid chattering. |
| **Starvation Prevention** | NEMA standards (Max green timer, force-off timers) | Guarantees service to minor approaches after a maximum waiting duration. | Standard safety and fairness constraint in all commercial controllers. |
| **Predictive Queue Modeling** | Mirchandani & Head (RHODES, 2001), Gartner (OPAC) | Short-horizon forward projection of queue lengths using arrival and saturation flow rates. | Standard dynamic programming / model predictive control concept. |

---

## 2. What Our Research Controller Borrows

Our candidate controller synthesizes elements from these established traditions into an explicit, transparent, and modular state-space framework:
1. **Queue measurement** $Q_i(t)$: Instantaneous halting vehicle count (Webster / Miller).
2. **Short-horizon arrival rate** $A_i(t)$: Rolling window actuation rate (NEMA / OPAC).
3. **Queue accumulation derivative** $G_i(t)$: Finite-difference queue growth estimation (Lämmer & Helbing).
4. **Waiting burden** $W_i(t)$: Total accumulated waiting penalty of queued vehicles (Smith / SCATS).
5. **Hysteresis margin** $H$: Score-threshold switching buffer to eliminate rapid phase oscillation.
6. **Dual-tier fairness**: Continuous red-time aging combined with an absolute maximum red ceiling.

---

## 3. What Combination / Hypothesis Is Being Investigated

Our research investigates **transparent multi-variable phase pressure scoring** under isolated four-arm geometry across varying traffic regimes:
- **Core Hypothesis**: While simple instantaneous queue comparison degrades under saturation (alternating at max green), a composite score integrating **arrival momentum**, **queue growth rate**, and **accumulated waiting burden** with **hysteresis** can stabilize queue dissipation and reduce total vehicle delay without requiring black-box neural networks or complex online optimization.
- **Specific Research Questions**:
  1. Does adding arrival rate ($A_i$) or queue growth ($G_i$) actually provide statistically significant benefits over pure queue length ($Q_i$)?
  2. Does a hysteresis margin ($H$) measurably reduce yellow lost time without increasing average delay?
  3. Does the composite controller maintain its advantage under extreme oversaturation ($p = 0.18$) and heavy directional asymmetry?

---

## 4. What Cannot Be Claimed as Novel

To maintain strict scientific integrity, the following claims **MUST NOT** be made in the paper:
1. **Do NOT claim** that queue-based or arrival-rate-based control is "novel", "new", or "first".
2. **Do NOT claim** that combining queue and delay is a "novel paradigm" (it has existed in OPAC, RHODES, and max-pressure extensions).
3. **Do NOT claim** that the controller is "state of the art" or "optimal" (it is a heuristic scoring formulation, not an optimal control solver).
4. **Do NOT claim** that simple density control solves traffic congestion (it has fundamental saturation limits).

---

## 5. Permissible Scientific Contributions

The defensible contributions of this research are:
1. An **open, fully reproducible benchmark framework** in SUMO with strict cohort-based metric isolation.
2. A **rigorous component-by-component ablation study** isolating the empirical impact of queue, arrival rate, queue growth, waiting burden, and hysteresis.
3. An **objective sensitivity and robustness audit** analyzing how the controller behaves under sensor noise and demand shocks.
