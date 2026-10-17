# Independent re-execution and fresh-seed confirmation

- `rerun_all.py`: re-executes the 140 final-evaluation runs with the repository's own runner and controllers (unmodified) and stores step data, vehicle records and decision logs. All 12 summary metrics matched `results/final_test_results_per_seed.csv` in all 140 runs (1,680 values).
- `analyze_rerun.py`, `diag_decisions.py`: reproduction check, per-direction waiting, vehicles still in the network, decision-log diagnostics (outputs in `results/`).
- `gen_fresh_demand.py`, `run_suite.py`, `analyze_fresh.py`: confirmation on fresh seeds 201 to 205 (frozen controller, three baselines and four single-term variants). Route files are in `fresh_demand/`; summaries in `results/`.

The scripts contain absolute paths from the machine they were run on (`/home/user/...`); edit the path constants at the top of each file before running. Requires eclipse-sumo 1.27.1 and traci 1.27.1.
