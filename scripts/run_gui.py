#!/usr/bin/env python3
"""
Visual Simulation Runner with Real-Time Lane & Signal Telemetry.

Launches SUMO-GUI and displays a live, human-readable terminal dashboard explaining:
- Exactly how many vehicles are arriving, queued, and moving on EACH lane.
- Exactly which direction is open, how many seconds it has been green, and how much time remains.
- Directional demand comparisons (D_NS vs D_EW) and signal decision rationale.

Usage:
    python scripts/run_gui.py                # Run with Fixed-Time baseline
    python scripts/run_gui.py --mode density # Run with Basic Density adaptive controller
"""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path
import traci

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from controllers.fixed_time_controller import FixedTimeSignalController
from controllers.basic_density_controller import BasicDensityController


def find_sumo_gui():
    """Locate the sumo-gui binary."""
    venv_gui = Path(sys.prefix) / "bin" / "sumo-gui"
    if venv_gui.exists() and os.access(venv_gui, os.X_OK):
        return str(venv_gui)

    try:
        import sumolib
        gui_bin = sumolib.checkBinary("sumo-gui")
        if gui_bin and os.path.exists(gui_bin):
            return gui_bin
    except Exception:
        pass

    if "SUMO_HOME" in os.environ:
        sh_gui = Path(os.environ["SUMO_HOME"]) / "bin" / "sumo-gui"
        if sh_gui.exists():
            return str(sh_gui)

    which_gui = shutil.which("sumo-gui")
    if which_gui:
        return which_gui

    return None


def configure_display_env():
    """Ensure X11/XQuartz display and fontconfig are active on macOS."""
    if sys.platform != "darwin":
        return

    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    font_conf_paths = [
        Path("/opt/X11/etc/X11/fontconfig"),
        Path("/opt/X11/lib/X11/fontconfig"),
        Path("/opt/homebrew/etc/fonts"),
        Path("/etc/fonts"),
    ]
    for p in font_conf_paths:
        if p.exists() and (p / "fonts.conf").exists():
            os.environ["FONTCONFIG_PATH"] = str(p)
            break


def main():
    parser = argparse.ArgumentParser(description="Run SUMO-GUI with real-time lane telemetry")
    parser.add_argument(
        "--mode",
        choices=["fixed", "density"],
        default="fixed",
        help="Signal control mode: 'fixed' (Baseline) or 'density' (Adaptive)",
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=80,
        help="Step delay in milliseconds (default: 80ms for clear visual observation)",
    )
    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=2,
        help="Print dashboard update every N simulation seconds (default: 2s)",
    )
    args = parser.parse_args()

    configure_display_env()

    gui_bin = find_sumo_gui()
    if not gui_bin:
        print("[Error] 'sumo-gui' binary could not be found.")
        sys.exit(1)

    cfg_file = PROJECT_ROOT / "scenarios" / "four_arm.sumocfg"

    # Setup controller
    if args.mode == "density":
        controller = BasicDensityController(tl_id="J0", min_green=15, max_green=50, yellow_time=3, starvation_red_time=45)
        mode_title = "ADAPTIVE DENSITY CONTROLLER"
    else:
        controller = FixedTimeSignalController(tl_id="J0")
        mode_title = "FIXED-TIME BASELINE CONTROLLER"

    sumo_cmd = [
        gui_bin,
        "-c", str(cfg_file),
        "--start",
        "--delay", str(args.delay),
        "--quit-on-end", "false",
        "--no-warnings", "true",
        "--waiting-time-memory", "1000",
    ]

    print("=" * 82)
    print(f"SUMO-GUI REAL-TIME VISUAL SIMULATION | MODE: {mode_title}")
    print("=" * 82)
    print(f"[+] SUMO-GUI Binary: {gui_bin}")
    print(f"[+] Scenario: {cfg_file}")
    print(f"[+] Playback Delay: {args.delay}ms per step")
    print(f"[+] Display Target: {os.environ.get('DISPLAY')}")
    print("\n[*] Starting GUI window... Look at your desktop for the SUMO-GUI window!")
    print("[*] Live lane status and signal timing are printed below:\n")

    traci.start(sumo_cmd)

    incoming_lanes = {
        "North (N_J0)": "N_J0_0",
        "South (S_J0)": "S_J0_0",
        "East  (E_J0)": "E_J0_0",
        "West  (W_J0)": "W_J0_0",
    }

    phase_names = {
        0: ("NORTH-SOUTH GREEN", "🟢 GREEN (NS Open)", "🔴 RED (EW Waiting)"),
        1: ("NORTH-SOUTH YELLOW", "🟡 YELLOW (NS Stopping)", "🔴 RED (EW Waiting)"),
        2: ("EAST-WEST GREEN", "🔴 RED (NS Waiting)", "🟢 GREEN (EW Open)"),
        3: ("EAST-WEST YELLOW", "🔴 RED (NS Waiting)", "🟡 YELLOW (EW Stopping)"),
    }

    try:
        step = 0
        while True:
            # Let controller step
            controller_diag = controller.step(float(step), traci)
            traci.simulationStep()
            sim_time = traci.simulation.getTime()
            step += 1

            # Query lane queues and densities
            q_n = traci.lane.getLastStepHaltingNumber(incoming_lanes["North (N_J0)"])
            q_s = traci.lane.getLastStepHaltingNumber(incoming_lanes["South (S_J0)"])
            q_e = traci.lane.getLastStepHaltingNumber(incoming_lanes["East  (E_J0)"])
            q_w = traci.lane.getLastStepHaltingNumber(incoming_lanes["West  (W_J0)"])

            d_n = traci.lane.getLastStepVehicleNumber(incoming_lanes["North (N_J0)"])
            d_s = traci.lane.getLastStepVehicleNumber(incoming_lanes["South (S_J0)"])
            d_e = traci.lane.getLastStepVehicleNumber(incoming_lanes["East  (E_J0)"])
            d_w = traci.lane.getLastStepVehicleNumber(incoming_lanes["West  (W_J0)"])

            spd_n = traci.lane.getLastStepMeanSpeed(incoming_lanes["North (N_J0)"])
            spd_s = traci.lane.getLastStepMeanSpeed(incoming_lanes["South (S_J0)"])
            spd_e = traci.lane.getLastStepMeanSpeed(incoming_lanes["East  (E_J0)"])
            spd_w = traci.lane.getLastStepMeanSpeed(incoming_lanes["West  (W_J0)"])

            current_phase = traci.trafficlight.getPhase("J0")
            phase_info = phase_names.get(current_phase, ("UNKNOWN", "UNKNOWN", "UNKNOWN"))

            # Determine lane light states
            if current_phase == 0:
                st_n = st_s = "🟢 GREEN "
                st_e = st_w = "🔴 RED   "
                phase_label = "NORTH-SOUTH GREEN"
                if args.mode == "fixed":
                    elapsed = controller.time_in_phase
                    remaining = max(0, 42 - elapsed)
                    timing_str = f"Open for {elapsed}s (Remaining: {remaining}s / 42s)"
                else:
                    elapsed = controller.elapsed_green_time
                    timing_str = f"Open for {elapsed}s (Min: 15s | Max: 50s) | Reason: {controller_diag.get('decision_reason', '')}"
            elif current_phase == 1:
                st_n = st_s = "🟡 YELLOW"
                st_e = st_w = "🔴 RED   "
                phase_label = "NORTH-SOUTH YELLOW CLEARANCE"
                timing_str = "Yellow clearance (3s) before East-West opens"
            elif current_phase == 2:
                st_n = st_s = "🔴 RED   "
                st_e = st_w = "🟢 GREEN "
                phase_label = "EAST-WEST GREEN"
                if args.mode == "fixed":
                    elapsed = controller.time_in_phase
                    remaining = max(0, 42 - elapsed)
                    timing_str = f"Open for {elapsed}s (Remaining: {remaining}s / 42s)"
                else:
                    elapsed = controller.elapsed_green_time
                    timing_str = f"Open for {elapsed}s (Min: 15s | Max: 50s) | Reason: {controller_diag.get('decision_reason', '')}"
            else:
                st_n = st_s = "🔴 RED   "
                st_e = st_w = "🟡 YELLOW"
                phase_label = "EAST-WEST YELLOW CLEARANCE"
                timing_str = "Yellow clearance (3s) before North-South opens"

            d_ns = q_n + q_s
            d_ew = q_e + q_w
            active_vehs = traci.vehicle.getIDCount()
            arrived_vehs = traci.simulation.getArrivedNumber()

            if step % args.refresh_rate == 0:
                print(f"\n┌{'─'*80}┐")
                print(f"│ ⏱️  SIMULATION TIME: {sim_time:5.1f}s  |  MODE: {mode_title:<39}│")
                print(f"│ 🚦 ACTIVE SIGNAL:   {phase_label:<32} {timing_str:<26}│")
                print(f"├{'─'*80}┤")
                print(f"│ {'APPROACH LANE':<16} │ {'LIGHT':<9} │ {'WAITING (QUEUED)':<18} │ {'TOTAL ON LANE':<15} │ {'AVG SPEED':<10} │")
                print(f"├{'─'*80}┤")
                print(f"│ {'North (N_J0)':<16} │ {st_n:<9} │ {q_n:2d} vehicles waiting   │ {d_n:2d} vehicles     │ {spd_n:5.1f} m/s   │")
                print(f"│ {'South (S_J0)':<16} │ {st_s:<9} │ {q_s:2d} vehicles waiting   │ {d_s:2d} vehicles     │ {spd_s:5.1f} m/s   │")
                print(f"│ {'East  (E_J0)':<16} │ {st_e:<9} │ {q_e:2d} vehicles waiting   │ {d_e:2d} vehicles     │ {spd_e:5.1f} m/s   │")
                print(f"│ {'West  (W_J0)':<16} │ {st_w:<9} │ {q_w:2d} vehicles waiting   │ {d_w:2d} vehicles     │ {spd_w:5.1f} m/s   │")
                print(f"├{'─'*80}┤")
                print(f"│ 📊 DEMAND STATUS: North-South Demand = {d_ns:2d} queued  vs  East-West Demand = {d_ew:2d} queued      │")
                print(f"│ 🚗 NETWORK STATS: Active Vehicles: {active_vehs:2d}   |   Completed Vehicles: {arrived_vehs:2d}            │")
                print(f"└{'─'*80}┘")

    except KeyboardInterrupt:
        print("\n[*] Stopped simulation.")
    except Exception as e:
        print(f"\n[!] Note: {e}")
    finally:
        try:
            traci.close()
        except Exception:
            pass
        print("[*] TraCI connection closed.")


if __name__ == "__main__":
    main()
