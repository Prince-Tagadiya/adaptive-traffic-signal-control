# Reproducibility & Replication Protocol

**Document**: `final_paper/supplementary/reproducibility.md`  
**Target Journal**: *Journal of Intelligent Transportation Systems* (Taylor & Francis)  
**Authors**: Antigravity Research Team  
**Date**: October 2026  
**Replication Guarantee**: Deterministic Bit-Level Reproducibility Across Identical Random Seeds

---

## 1. System & Software Dependencies

All simulation experiments and inferential statistical evaluations were conducted in a verified, headless UNIX environment using the following software package versions:

| Component | Software Package | Exact Version | Purpose in Research Pipeline |
| :--- | :--- | :---: | :--- |
| **Operating System** | macOS / Darwin (POSIX x86_64/arm64) | 24.x | Host operating system |
| **Language Runtime** | Python Runtime Environment | 3.13.2 | Core execution language |
| **Traffic Simulator** | Eclipse SUMO (Simulation of Urban MObility) | 1.27.1 | Microscopic traffic flow and vehicle simulation |
| **Simulator Interface**| TraCI (Traffic Control Interface) | 1.27.1 | Discrete step control and state query API |
| **Data Processing** | pandas | 3.0.6 | Tabular data manipulation and metric aggregation |
| **Numerical Engine** | NumPy | 2.5.3 | Matrix operations and RNG array indexing |
| **Statistical Engine** | SciPy | 1.18.1 | Two-sided paired $t$-tests and exact Wilcoxon tests |
| **Figure Generation** | Matplotlib | 3.11.2 | High-resolution publication-quality figure rendering |
| **Document Compiler** | python-docx / reportlab | 1.2.0 / 5.0.1 | Automated DOCX and PDF manuscript generation |

To install the exact Python dependencies:
```bash
pip install -r requirements.txt
pip install python-docx reportlab
```

---

## 2. Hardware Environment

- **Processor**: Apple Silicon (M-series) / Intel Core i7 or higher
- **Memory**: 8 GB RAM minimum (experiments require $< 500\,\text{MB}$ resident set size)
- **Disk Storage**: $< 50\,\text{MB}$ disk storage required for full 140-run dataset

---

## 3. Random Number Seeds & Determinism

### 3.1 Strict Separation of Datasets
1. **Calibration / Training Seeds (Phase 7 & 8)**:
   - Seeds: `[101, 102, 103, 104]`
   - Purpose: Calibration of weights ($\beta, \gamma, \delta, \eta, H$), Pareto frontier optimization, architecture audit.
   - Status: STRICTLY ISOLATED from test evaluation.
2. **Blind Confirmatory Test Seeds (Phase 9 & 10)**:
   - Seeds: `[42, 43, 44, 45, 46]`
   - Purpose: Final unbiased performance evaluation and confirmatory hypothesis testing.
   - Status: LOCKED AND IMMUTABLE.

### 3.2 Determinism Verification
SUMO initializes an internal Mersenne Twister pseudo-random number generator using the `--seed <k>` flag. Because SUMO simulation is strictly deterministic given the same binary version, network file, and seed, re-running any simulation with seed $k$ yields bit-level identical vehicle arrival trajectories, detector measurements, and output metrics.

A formal determinism audit was performed in Phase 9 (`docs/final_test_evaluation_report.md`): re-running C3 on `medium` with seed 42 yielded:
- Throughput: $220\,\text{veh}$ (Exact $\Delta = 0$)
- Waiting Time: $8.54\,\text{s}$ (Exact $\Delta = 0.00\,\text{s}$)
- Travel Time: $53.92\,\text{s}$ (Exact $\Delta = 0.00\,\text{s}$)
- Mean Delay: $15.90\,\text{s}$ (Exact $\Delta = 0.00\,\text{s}$)
- Phase Switches: $88$ (Exact $\Delta = 0$)

---

## 4. Experimental Parameters

- **Simulation Duration**: $T_{\text{sim}} = 1000\,\text{s}$
- **Warm-Up Period**: $T_{\text{warm}} = 200\,\text{s}$
- **Evaluation Window**: $t \in [200, 1000]\,\text{s}$ ($800\,\text{s}$ active measurement window)
- **Simulation Time Step**: $\Delta t = 1.0\,\text{s}$
- **Evaluation Cohort Standard**: **Cohort A**
  $$\text{Cohort A} = \{v \in \mathcal{V} \mid t_{\text{depart}}(v) \ge 200\,\text{s} \land t_{\text{arrive}}(v) \ge 200\,\text{s}\}$$
  Vehicles departing or arriving during the 200-second warm-up are strictly quarantined from primary delay and waiting time metrics.

---

## 5. Frozen Controller Configuration

The proposed adaptive controller (`ProposedAdaptiveSignalController`) must be executed with the following immutable parameters:

```python
controller = ProposedAdaptiveSignalController(
    tl_id="J0",
    min_green=15,             # G_min = 15s
    max_green=50,             # G_max = 50s
    yellow_time=3,            # Y = 3s
    starvation_red_time=45,   # R_starve = 45s
    w_arrival=20,             # W_A = 20s
    w_growth=10,              # W_G = 10s
    alpha=1.00,               # Queue weight
    beta=0.75,                # Arrival rate weight
    gamma=0.10,               # Queue growth weight
    delta=0.25,               # Waiting burden weight
    eta=0.25,                 # Red-age fairness weight
    hysteresis=0.20,          # Switching barrier H
    q_ref=20.0,               # Queue reference scale (veh)
    a_ref=0.40,               # Arrival reference scale (veh/s)
    w_ref=30.0,               # Waiting reference scale (s)
    r_ref=50.0,               # Red-age reference scale (s)
    g_ref=0.50,               # Queue growth scale (veh/s)
    noise_std=0.0             # Noise-free baseline
)
```

---

## 6. Commands to Reproduce Experiments & Analyses

To reproduce the entire experimental study from scratch:

### Step 1: Execute the 140-run Blind Final Test
```bash
python3 scripts/run_final_test_evaluation.py
```
*Output*: Generates `results/final_test_results_per_seed.csv` and `results/final_test_summary.csv`.

### Step 2: Compute Confirmatory Inferential Statistics
```bash
python3 scripts/compute_final_statistical_analysis.py
```
*Output*: Computes paired $t$-tests, Wilcoxon tests, Cohen's $d_z$, Holm-Bonferroni, and Benjamini-Hochberg FDR adjustments, saving:
- `results/statistical_primary_waiting_time.csv`
- `results/statistical_secondary_metrics.csv`
- `results/effect_size_summary.csv`

### Step 3: Generate the Forensic Audit Report
```bash
python3 scripts/generate_final_analysis_doc.py
```
*Output*: Generates `docs/final_statistical_analysis.md`.

### Step 4: Generate Publication Figures & Paper Package
```bash
python3 scripts/generate_final_paper_figures.py
python3 scripts/generate_jits_manuscript.py
```
*Output*: Generates all 12 publication figures in `final_paper/figures/` and the manuscripts in `final_paper/manuscript/`.

---

## 7. Directory Tree of Reproducibility Package

```
final_paper/
├── manuscript/
│   ├── JITS_manuscript.docx
│   ├── JITS_manuscript.pdf
│   └── JITS_manuscript.tex
├── figures/
│   ├── Fig01_system_architecture.png
│   ├── Fig02_algorithm_flowchart.png
│   ├── Fig03_intersection_and_signal_phases.png
│   ├── Fig04_controller_decision_process.png
│   ├── Fig05_queue_demand_behavior.png
│   ├── Fig06_waiting_time_comparison.png
│   ├── Fig07_queue_length_comparison.png
│   ├── Fig08_travel_time_comparison.png
│   ├── Fig09_delay_comparison.png
│   ├── Fig10_throughput_comparison.png
│   ├── Fig11_phase_switching_comparison.png
│   └── Fig12_scenario_summary.png
├── tables/
│   ├── Table01_parameters.csv
│   ├── Table02_scenarios.csv
│   ├── Table03_baseline_results.csv
│   ├── Table04_final_results.csv
│   └── Table05_controller_comparison.csv
├── supplementary/
│   ├── project_audit.md
│   ├── algorithm_pseudocode.txt
│   ├── mathematical_derivation.md
│   ├── reproducibility.md
│   └── experiment_protocol.md
├── data/
│   ├── final_test_results_per_seed.csv
│   └── final_test_summary.csv
└── README.md
```
