# Adaptive Traffic Signal Control Research Framework

A reproducible research framework comparing adaptive traffic signal controllers
using **SUMO (Simulation of Urban MObility)**, **Python**, and **TraCI**.

Companion source code for the manuscript submitted to the
*Journal of Intelligent Transportation Systems (JITS)*.

---

## 1. Research Overview

This repository provides an end-to-end experimental pipeline comparing four controllers:

| ID | Controller | Description |
|----|-----------|-------------|
| C0 | **Fixed-Time (Baseline)** | Static 90 s cycle (42 s NS green, 3 s yellow, 42 s EW green, 3 s yellow) |
| C1 | **Webster-Calibrated Fixed-Time** | Webster-optimized 36 s cycle calibrated on training seeds 101–102 |
| C2 | **Basic Queue Controller** | Instantaneous halting-queue comparison (D_NS vs D_EW) with NEMA safety limits |
| C3 | **Proposed Adaptive Controller** | Multi-variable dimensionless pressure controller (see Section 3) |

The proposed controller (C3) combines five normalized state signals with a
hysteresis switching barrier to reduce unnecessary phase changes.

---

## 2. Repository Structure

```
traffic_signal_research/
├── controllers/
│   ├── base_controller.py               # Abstract controller interface
│   ├── fixed_time_controller.py         # C0: Static 90 s fixed-time baseline
│   ├── optimized_fixed_time_controller.py # C1: Webster 36 s calibrated baseline
│   ├── basic_density_controller.py      # C2: Queue-based adaptive baseline
│   └── proposed_adaptive_controller.py  # C3: Proposed multi-variable controller
├── simulation/
│   └── runner.py                        # Headless SUMO/TraCI runner with cohort isolation
├── scenarios/
│   ├── four_arm.net.xml                 # 4-arm orthogonal intersection network
│   ├── four_arm.sumocfg                 # Base SUMO configuration
│   └── demand/                          # Pre-generated immutable route files (37 files)
├── scripts/
│   ├── generate_routes.py               # Demand profile generator
│   ├── run_research_experiments.py      # Full experiment suite runner
│   ├── run_final_test_evaluation.py     # Final test set evaluation (seeds 42–46)
│   ├── compute_final_statistical_analysis.py # Phase 10 statistical analysis
│   ├── generate_final_paper_figures.py  # Publication figure generator
│   ├── generate_jits_manuscript.py      # LaTeX manuscript generator
│   └── plot_research_results.py         # Research results plotter
├── results/                             # CSV datasets from all experiments
│   ├── final_test_results_per_seed.csv  # Final test per-seed results (primary)
│   ├── final_test_summary.csv           # Final test summary statistics
│   ├── statistical_primary_waiting_time.csv # Paired statistical tests (primary metric)
│   ├── statistical_secondary_metrics.csv    # Secondary metric tests
│   ├── effect_size_summary.csv          # Cohen's d and percentage change
│   └── ...                              # Calibration, ablation, sensitivity, robustness
├── docs/
│   ├── mathematical_derivation.md       # Algorithm equations and pseudocode
│   ├── experimental_methodology.md      # Cohort isolation and replication protocol
│   ├── final_statistical_analysis.md    # Complete Phase 10 statistical report
│   ├── frozen_parameters.md             # Calibrated parameter vector (locked before test)
│   └── ...
├── final_paper/
│   ├── manuscript/
│   │   ├── JITS_manuscript.tex          # LaTeX source
│   │   ├── JITS_manuscript.pdf          # Compiled PDF
│   │   └── JITS_manuscript.docx         # Word version
│   ├── figures/                         # High-resolution manuscript figures
│   ├── tables/                          # Supplementary tables
│   └── supplementary/                   # Supplementary materials
├── figures/                             # Exploratory research figures
├── data/                                # Summary CSV datasets (raw step data excluded)
└── requirements.txt
```

---

## 3. Proposed Controller (C3)

The proposed controller computes a composite pressure score for each phase:

```
S_p(t) = alpha * q_p(t) + beta * a_p(t) + gamma * g_p(t) + delta * w_p(t) + eta * r_p(t)
```

where:
- `q_p(t)` — Normalized halting queue length (ref: 20 vehicles)
- `a_p(t)` — Normalized rolling arrival rate (ref: 0.40 veh/s)
- `g_p(t)` — Normalized queue growth rate (10 s window)
- `w_p(t)` — Normalized accumulated waiting burden (ref: 30 s)
- `r_p(t)` — Normalized continuous red-time fairness (ref: 50 s)

**Frozen parameter vector** (calibrated exclusively on seeds 101–104):

| Parameter | Value | Role |
|-----------|-------|------|
| alpha | 1.00 | Queue anchor weight |
| beta | 0.75 | Arrival rate weight |
| gamma | 0.10 | Queue growth weight |
| delta | 0.25 | Waiting burden weight |
| eta | 0.25 | Red-time fairness weight |
| H | 0.20 | Hysteresis switching barrier |

NEMA safety constraints: G_min = 15 s, G_max = 50 s, Y = 3 s, R_starve = 45 s.

---

## 4. Experimental Design

### 4.1 One Realization → Multiple Controllers
All controllers evaluate the same pre-generated immutable route files.
Controllers never generate traffic dynamically, eliminating stochastic demand divergence.

### 4.2 Strict Cohort Isolation
- **Cohort A (Primary)**: Vehicle departs ≥ 200 s AND arrives ≥ 200 s (pure evaluation cohort)
- **Cohort B**: Vehicle departs < 200 s AND arrives ≥ 200 s (boundary-crossing cohort)
- **Cohort C**: Discarded (pure warm-up vehicles)

### 4.3 Final Test Protocol
- **Calibration seeds**: 101, 102, 103, 104 (parameters frozen before any test evaluation)
- **Test seeds**: 42, 43, 44, 45, 46 (not used in the calibration or the architecture audit; they had been used in earlier exploratory studies, see docs/calibration_report.md)
- **Scenarios**: low, medium, high, oversaturated, asym_ns, asym_ew, dynamic

### 4.4 Statistical Analysis
- Primary metric: Mean waiting time per vehicle (Cohort A)
- Tests: Paired Wilcoxon signed-rank (exact) and paired t-test, N=5 per scenario
- Corrections: Holm-Bonferroni and Benjamini-Hochberg FDR across 7 scenarios
- Effect sizes: Cohen's d and percentage change vs each comparator

---

## 5. Reproduction Instructions

### 5.1 Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Generate Demand Profiles (already included in scenarios/demand/)
```bash
python scripts/generate_routes.py
```

### 5.3 Run Full Experiment Suite
```bash
python scripts/run_research_experiments.py
```

### 5.4 Run Final Test Evaluation
```bash
python scripts/run_final_test_evaluation.py
```

### 5.5 Statistical Analysis
```bash
python scripts/compute_final_statistical_analysis.py
```

### 5.6 Generate Manuscript Figures
```bash
python scripts/generate_final_paper_figures.py
```

### 5.7 Visual Inspection (requires SUMO-GUI and XQuartz on macOS)
```bash
python scripts/run_gui.py
```

---

## 6. Key Empirical Results (Final Test Set, Seeds 42–46)

| Scenario | C3 vs C0 (Fixed-Time) | C3 vs C1 (Webster) | C3 vs C2 (Basic Queue) |
|----------|-----------------------|--------------------|------------------------|
| Low demand | −52.0% wait | −10.5% wait | +3.8% wait |
| Medium demand | −57.0% wait | −9.8% wait | −2.1% wait |
| High demand | −38.5% wait | +7.4% wait | −0.7% wait |
| Oversaturated | −10.0% wait | +13.8% wait | −4.5% wait |
| Asymmetric NS | −72.1% wait | −66.5% wait | −14.2% wait |
| Asymmetric EW | −77.4% wait | −73.2% wait | −22.0% wait |
| Dynamic | −54.8% wait | −33.8% wait | −10.8% wait |

C3 shows strongest gains in asymmetric demand scenarios where phase-time
rebalancing provides the most benefit.

---

## 7. Requirements

```
sumo>=1.14.0
traci
sumolib
pandas
numpy
scipy
matplotlib
python-docx
```

See `requirements.txt` for pinned versions.
