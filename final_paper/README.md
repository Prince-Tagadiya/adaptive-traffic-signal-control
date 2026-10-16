# JITS Research Paper Package: Multi-Factor Adaptive Traffic Signal Control

**Paper Title**: Multi-Factor Adaptive Traffic Signal Control Under Directional Demand Asymmetry and Dynamic Flow: Formulation, Stability Constraints, and Confirmatory Simulation Evaluation  
**Target Journal**: *Journal of Intelligent Transportation Systems: Technology, Planning, and Operations* (Taylor & Francis)  
**Journal URL**: [https://www.tandfonline.com/journals/gits18](https://www.tandfonline.com/journals/gits18)  
**Authors**: Prince Tagadiya  
**Date**: October 2026  
**Status**: SUBMISSION-READY PACKAGE

---

## 1. Controller & Parameter Version Specification

- **Controller Implementation**: `controllers/proposed_adaptive_controller.py` (`ProposedAdaptiveSignalController`)
- **Controller Version**: Version 3.0 (Clean-Calibrated & Architecture-Audited)
- **Status**: **STRICTLY FROZEN** (No tuning, re-seeding, or modification following test evaluation)
- **Frozen Parameter Vector**:
  - Queue weight ($\alpha$): $1.00$ (Anchor)
  - Arrival weight ($\beta$): $0.75$ (Calibrated)
  - Queue growth weight ($\gamma$): $0.10$ (Audit verified)
  - Waiting burden weight ($\delta$): $0.25$ (Calibrated)
  - Red-age fairness weight ($\eta$): $0.25$ (Calibrated)
  - Switching hysteresis ($H$): $0.20$ (Dimensionless barrier)
  - Normalization scales: $Q_{\text{ref}} = 20.0\,\text{veh}$, $A_{\text{ref}} = 0.40\,\text{veh/s}$, $W_{\text{ref}} = 30.0\,\text{s}$, $R_{\text{ref}} = 50.0\,\text{s}$, $G_{\text{ref}} = 0.50\,\text{veh/s}$
  - Windows & Safety Limits: $W_A = 20\,\text{s}$, $W_G = 10\,\text{s}$, $G_{\text{min}} = 15\,\text{s}$, $G_{\text{max}} = 50\,\text{s}$, $Y = 3\,\text{s}$, $R_{\text{starve}} = 45\,\text{s}$

---

## 2. Final Test Dataset

- **Evaluation Dataset**: Blind test set evaluated across Seeds $42, 43, 44, 45, 46$
- **Total Simulation Runs**: $140$ ($4\text{ controllers} \times 7\text{ scenarios} \times 5\text{ seeds}$)
- **Source Files**:
  - Per-seed run records: [`data/final_test_results_per_seed.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/final_paper/data/final_test_results_per_seed.csv)
  - Scenario descriptive summary: [`data/final_test_summary.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/final_paper/data/final_test_summary.csv)
  - Confirmatory inferential statistics: [`results/statistical_primary_waiting_time.csv`](file:///Applications/PRINCE/Traffic%20light/traffic_signal_research/results/statistical_primary_waiting_time.csv)

---

## 3. Directory Structure & File Inventory

```
final_paper/
├── manuscript/
│   ├── JITS_manuscript.docx        # Word document format (Times New Roman, 1.5 line spacing, tables embedded)
│   ├── JITS_manuscript.pdf         # Standalone PDF compilation with figures and tables
│   └── JITS_manuscript.tex         # LaTeX source document with IEEEtran/Taylor & Francis standard formatting
├── figures/
│   ├── Fig01_system_architecture.png           # Closed-loop simulation architecture diagram
│   ├── Fig02_algorithm_flowchart.png           # Decision flowchart showing safety gates & hysteresis
│   ├── Fig03_intersection_and_signal_phases.png# 4-Arm intersection geometry & signal phase sequence
│   ├── Fig04_controller_decision_process.png   # Multi-factor priority weighting & hysteresis barrier
│   ├── Fig05_queue_demand_behavior.png         # Queue accumulation & controller response over time
│   ├── Fig06_waiting_time_comparison.png       # Primary waiting time comparison (Mean ± SD)
│   ├── Fig07_queue_length_comparison.png       # Queue length comparison across scenarios
│   ├── Fig08_travel_time_comparison.png        # Travel time comparison across scenarios
│   ├── Fig09_delay_comparison.png              # Time-loss delay comparison across scenarios
│   ├── Fig10_throughput_comparison.png         # Completed vehicle throughput comparison
│   ├── Fig11_phase_switching_comparison.png    # Phase transition counts showing switching stabilization
│   └── Fig12_scenario_summary.png              # Relative difference (%) and standardized Cohen's dz
├── tables/
│   ├── Table01_parameters.csv                  # Complete controller parameters and reference scales
│   ├── Table02_scenarios.csv                   # Scenario definitions, demand regimes, and inflow rates
│   ├── Table03_baseline_results.csv            # Baseline controllers (C0, C1, C2) descriptive statistics
│   ├── Table04_final_results.csv               # Complete performance statistics across all 4 controllers
│   └── Table05_controller_comparison.csv       # Paired hypothesis tests, FDR q-values, and effect sizes
├── supplementary/
│   ├── project_audit.md                        # Forensic implementation verification audit report
│   ├── algorithm_pseudocode.txt                # Formal algorithmic pseudocode
│   ├── mathematical_derivation.md              # 14-step mathematical derivation pipeline
│   ├── reproducibility.md                      # Step-by-step replication instructions and software versions
│   └── experiment_protocol.md                  # Experimental unit, cohort definitions, and testing standards
├── data/
│   ├── final_test_results_per_seed.csv         # Locked per-seed simulation output dataset
│   └── final_test_summary.csv                  # Locked descriptive performance summary dataset
└── README.md                                   # Package master overview and checklist
```

---

## 4. Replication Commands

To reproduce the study from the project root:

```bash
# 1. Execute the 140-run blind evaluation
python3 scripts/run_final_test_evaluation.py

# 2. Compute confirmatory inferential statistics (Holm & Benjamini-Hochberg)
python3 scripts/compute_final_statistical_analysis.py

# 3. Generate the 12 publication figures at 300 DPI
python3 scripts/generate_final_paper_figures.py

# 4. Generate the manuscript files (DOCX, PDF, TEX)
python3 scripts/generate_jits_manuscript.py
```

---

## 5. Summary of Empirical Findings

1. **Directional Asymmetry Superiority**:
   C3 reduces waiting time by **$61.6\%$ to $63.2\%$** relative to Webster-calibrated fixed-time timing (C1) in directional asymmetry (`asym_ns` and `asym_ew`), surviving Benjamini-Hochberg False Discovery Rate control ($q < 0.04$).
2. **Universal Phase-Switching Stabilization**:
   Across all seven evaluated scenarios, C3 achieves a statistically significant **$4.6\%$ to $20.3\%$ reduction in phase switch transitions** compared to naive queue control C2 ($p < 0.028$ everywhere), demonstrating that queue smoothing and hysteresis prevent phase hunting without compromising throughput.
3. **No Universal Dominance**:
   In symmetric balanced regimes (`medium` and `high`), Webster-calibrated fixed-time control (C1) is competitive or slightly superior in waiting time ($14.9\%$ to $26.4\%$ lower) because rigid, zero-detector 36-second cycles eliminate detector latency.
4. **Computational Feasibility**:
   Average per-step decision compute time is under $0.5\,\text{ms}$, well within the 1000 ms real-time control budget.

---

## 6. Known Limitations

- **Simulation-Only Scope**: Evaluated in Eclipse SUMO via TraCI; physical hardware sensor noise and communication delays were not experimentally deployed.
- **Topology**: Isolated 4-arm intersection with single-lane approaches; arterial progression and pedestrian actuations remain future work.
- **Sample Size ($N=5$)**: The pre-registered sample of 5 realizations per scenario limits statistical power for moderate effect sizes ($|d_z| < 1.0$) and imposes a mathematical floor on two-sided Wilcoxon tests ($p_{\text{min}} = 0.0625$).

---

## 7. Submission Checklist for JITS (Taylor & Francis)

- [x] **Word & Page Limits**: Structured abstract $\approx 250$ words; manuscript $\approx 6,500$ words (compliant with JITS research article standards).
- [x] **File Formats**: DOCX and PDF manuscripts provided; LaTeX source file with BibTeX bibliography provided.
- [x] **Figures**: High-resolution PNGs provided at 300 DPI with vector-clean typography and color-blind accessible palettes.
- [x] **Tables**: Fully editable CSV files and embedded Word/LaTeX tables provided.
- [x] **Non-Overclaiming Language**: All hyperbolic superlatives audited and replaced with rigorous empirical statements.
- [x] **Ethics & Declarations**: Funding, Conflict of Interest, Data Availability, and Author Contribution statements included.
- [x] **Reproducibility**: Complete software versions, seeds, and execution commands documented.
