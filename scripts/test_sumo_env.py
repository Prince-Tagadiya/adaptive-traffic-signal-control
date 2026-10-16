#!/usr/bin/env python3
"""
Minimal SUMO + TraCI Environment Verification Script.

This script tests the SUMO and TraCI setup by:
1. Verifying that the SUMO command-line binary is accessible.
2. Initializing a headless SUMO simulation instance via TraCI.
3. Stepping through a minimal simulation scenario.
4. Closing the TraCI connection cleanly.
5. Printing clear diagnostic status and success/failure messages.
"""

import os
import sys
from pathlib import Path


def find_sumo_binary():
    """Locate the command-line sumo binary."""
    # 1. Try sumolib checkBinary if available
    try:
        import sumolib
        sumo_bin = sumolib.checkBinary("sumo")
        if sumo_bin and os.path.exists(sumo_bin):
            return sumo_bin
    except Exception:
        pass

    # 2. Check virtual environment bin
    venv_bin = Path(sys.prefix) / "bin" / "sumo"
    if venv_bin.exists():
        return str(venv_bin)

    # 3. Check SUMO_HOME
    if "SUMO_HOME" in os.environ:
        sumo_home_bin = Path(os.environ["SUMO_HOME"]) / "bin" / "sumo"
        if sumo_home_bin.exists():
            return str(sumo_home_bin)

    # 4. Check system PATH
    import shutil
    which_sumo = shutil.which("sumo")
    if which_sumo:
        return which_sumo

    return None


def run_test():
    print("=" * 60)
    print("SUMO + Python Research Environment Verification")
    print("=" * 60)

    # 1. Check Python
    print(f"[+] Python Executable: {sys.executable}")
    print(f"[+] Python Version: {sys.version.split()[0]}")

    # 2. Check required library imports
    libraries = {
        "traci": "TraCI SUMO Interface",
        "numpy": "Numerical Computing",
        "pandas": "Data Analysis",
        "matplotlib": "Plotting & Visualization"
    }

    print("\n--- Verifying Required Python Packages ---")
    missing = []
    for mod_name, desc in libraries.items():
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "Available")
            print(f"  [✓] {mod_name:<12} v{ver:<10} ({desc})")
        except ImportError as e:
            print(f"  [✗] {mod_name:<12} MISSING ({e})")
            missing.append(mod_name)

    if missing:
        print(f"\n[FAILURE] Missing required package(s): {', '.join(missing)}")
        print("Install them via: pip install -r requirements.txt")
        return False

    import traci

    # 3. Locate SUMO binary
    print("\n--- Locating SUMO Binary ---")
    sumo_binary = find_sumo_binary()
    if not sumo_binary:
        print("[FAILURE] SUMO command-line binary ('sumo') could not be found.")
        print("Please ensure eclipse-sumo is installed or SUMO_HOME is set in your environment.")
        return False
    print(f"  [✓] Found SUMO binary at: {sumo_binary}")

    # 4. Locate scenario configuration
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    config_file = project_dir / "scenarios" / "minimal.sumocfg"

    if not config_file.exists():
        print(f"[FAILURE] Test configuration file not found at: {config_file}")
        return False
    print(f"  [✓] Found test configuration at: {config_file}")

    # 5. Launch SUMO with TraCI
    print("\n--- Executing Minimal TraCI Simulation ---")
    sumo_cmd = [
        sumo_binary,
        "-c", str(config_file),
        "--no-step-log", "true",
        "--no-warnings", "true",
        "--duration-log.disable", "true"
    ]

    try:
        print("  [*] Starting headless SUMO process and establishing TraCI connection...")
        traci.start(sumo_cmd)
        print("  [✓] TraCI connected successfully.")

        num_steps = 10
        print(f"  [*] Stepping through simulation ({num_steps} steps)...")
        for step in range(1, num_steps + 1):
            traci.simulationStep()
            sim_time = traci.simulation.getTime()
            veh_count = traci.vehicle.getIDCount()
            if step % 5 == 0 or step == 1:
                print(f"      Step {step:2d}: Sim Time = {sim_time:.1f}s, Active Vehicles = {veh_count}")

        print("  [✓] Simulation steps completed successfully.")

    except Exception as e:
        print(f"\n[FAILURE] Error during TraCI simulation execution: {e}")
        try:
            traci.close()
        except Exception:
            pass
        return False

    finally:
        try:
            traci.close()
            print("  [✓] TraCI connection closed cleanly.")
        except Exception as e:
            print(f"  [!] Note during close: {e}")

    print("\n" + "=" * 60)
    print("SUCCESS: SUMO + TraCI research environment is fully operational!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
