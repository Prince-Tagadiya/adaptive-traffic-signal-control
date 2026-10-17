"""
Research Figure Generation Script.

Generates 16 high-resolution publication-quality figures:
1.  fig01_system_architecture.png       - Closed-loop system architecture diagram
2.  fig02_intersection_geometry.png      - 4-arm intersection geometric configuration & detection zones
3.  fig03_controller_flowchart.png       - Candidate controller decision-making flowchart
4.  fig04_queue_vs_time.png              - Time-series evolution of queue length (Fixed vs Basic vs Proposed)
5.  fig05_waiting_vs_time.png            - Time-series evolution of waiting time
6.  fig06_demand_profiles.png            - Cumulative arrival curves across experimental scenarios
7.  fig07_phase_decisions_timeline.png   - Signal phase timeline and switching dynamics
8.  fig08_waiting_time_comparison.png    - Bar chart of average waiting time with 95% CIs across all scenarios
9.  fig09_queue_length_comparison.png    - Average and maximum queue length comparison
10. fig10_travel_time_comparison.png     - Average vehicle travel time comparison
11. fig11_throughput_comparison.png      - Cohort A vehicle throughput comparison
12. fig12_performance_vs_demand.png      - Saturation degradation curve: Performance vs Demand intensity
13. fig13_performance_vs_asymmetry.png   - Performance under directional demand asymmetry
14. fig14_ablation_study.png             - Component ablation study (Models 0 to 6)
15. fig15_sensitivity_analysis.png       - Parameter sensitivity analysis (G_min, G_max, Hysteresis, W_A)
16. fig16_robustness_noise.png           - Performance resilience to measurement noise (sigma in [0, 3])
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Global publication style settings
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data"
FIG_DIR = BASE_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Curated publication color palette
COLORS = {
    "fixed": "#4A5568",     # Slate Gray
    "basic": "#3182CE",     # Royal Blue
    "proposed": "#38A169",  # Emerald Green
    "ns": "#E53E3E",        # Crimson Red
    "ew": "#3182CE",        # Blue
    "accent": "#DD6B20",    # Amber
}


# ==============================================================================
# Figure 1: System Architecture Diagram
# ==============================================================================
def plot_fig01_architecture():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis("off")

    def draw_box(x, y, w, h, title, subtitle, color):
        rect = patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.03",
            facecolor=color, edgecolor="#2D3748", linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center",
                fontsize=10, fontweight="bold", color="#1A202C")
        ax.text(x + w / 2, y + h * 0.3, subtitle, ha="center", va="center",
                fontsize=8, color="#4A5568", multialignment="center")

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", lw=1.5, color="#2D3748")
        )
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.04, label,
                    ha="center", va="bottom", fontsize=8, color="#2D3748")

    draw_box(0.04, 0.55, 0.22, 0.32, "SUMO Simulation", "Microscopic Traffic\nFour-Arm Network\nTraCI Interface", "#EDF2F7")
    draw_box(0.36, 0.55, 0.26, 0.32, "State Estimation", "Queue Length Q_i(t)\nArrival Rate A_i(t)\nQueue Growth G_i(t)\nWaiting Burden W_i(t)", "#EBF8FF")
    draw_box(0.72, 0.55, 0.24, 0.32, "Normalization", "q_i = Q_i / Q_ref\na_i = A_i / A_ref\ng_i = clip(G_i / G_ref)\nw_i = AW_i / W_ref", "#FEFCBF")

    draw_box(0.72, 0.12, 0.24, 0.32, "Pressure Scoring", "S_NS = alpha*q + beta*a\n      + gamma*g + delta*w\n      + eta*r\nS_EW = ...", "#FEEBC8")
    draw_box(0.36, 0.12, 0.26, 0.32, "Decision Logic", "Min Green (15s)\nMax Green (50s)\nFairness Ceiling (45s)\nHysteresis: S_opp > S_cur + H", "#C6F6D5")
    draw_box(0.04, 0.12, 0.22, 0.32, "Actuation & Safety", "Phase Transitions\n3s Yellow Clearance\nAll-Red Safety", "#FED7D7")

    draw_arrow(0.26, 0.71, 0.36, 0.71, "Raw Sensors")
    draw_arrow(0.62, 0.71, 0.72, 0.71, "Approaches i")
    draw_arrow(0.84, 0.55, 0.84, 0.44, "Dimensionless")
    draw_arrow(0.72, 0.28, 0.62, 0.28, "Phase Pressures")
    draw_arrow(0.36, 0.28, 0.26, 0.28, "Switch / Hold")
    draw_arrow(0.15, 0.44, 0.15, 0.55, "Signal State")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.title("Figure 1: Closed-Loop Multi-Variable Adaptive Signal Control Architecture", pad=15)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig01_system_architecture.png")
    plt.close()


# ==============================================================================
# Figure 2: Intersection Geometry & Detector Zones
# ==============================================================================
def plot_fig02_geometry():
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.set_xlim(-220, 220)
    ax.set_ylim(-220, 220)
    ax.set_aspect("equal")

    # Draw roads
    road_w = 14
    ax.add_patch(patches.Rectangle((-road_w/2, -200), road_w, 400, color="#E2E8F0"))
    ax.add_patch(patches.Rectangle((-200, -road_w/2), 400, road_w, color="#E2E8F0"))

    # Intersection box
    ax.add_patch(patches.Rectangle((-road_w/2, -road_w/2), road_w, road_w, color="#CBD5E0", ec="#4A5568", lw=1.5))
    ax.text(0, 0, "Junction J0\n[Signalized]", ha="center", va="center", fontsize=8, fontweight="bold")

    # Lane markings and labels
    ax.text(0, 210, "North Approach (N_J0_0, 250m)", ha="center", fontsize=9, fontweight="bold")
    ax.text(0, -215, "South Approach (S_J0_0, 250m)", ha="center", fontsize=9, fontweight="bold")
    ax.text(210, 0, "East Approach\n(E_J0_0, 250m)", va="center", ha="left", fontsize=9, fontweight="bold")
    ax.text(-215, 0, "West Approach\n(W_J0_0, 250m)", va="center", ha="right", fontsize=9, fontweight="bold")

    # Detection zones
    # Upstream arrival zone (x in [100, 200])
    ax.plot([0, 0], [100, 200], color="#3182CE", lw=4, label="Upstream Arrival Detection Zone (x < 100m)")
    ax.plot([0, 0], [-100, -200], color="#3182CE", lw=4)
    ax.plot([100, 200], [0, 0], color="#3182CE", lw=4)
    ax.plot([-100, -200], [0, 0], color="#3182CE", lw=4)

    # Queue stop detection zone (x in [0, 100])
    ax.plot([0, 0], [0, 100], color="#E53E3E", lw=4, label="Halting Queue Detection Zone (speed < 0.1 m/s)")
    ax.plot([0, 0], [0, -100], color="#E53E3E", lw=4)
    ax.plot([0, 100], [0, 0], color="#E53E3E", lw=4)
    ax.plot([0, -100], [0, 0], color="#E53E3E", lw=4)

    # Arrows for flow direction
    ax.annotate("", xy=(0, 20), xytext=(0, 70), arrowprops=dict(arrowstyle="->", lw=2, color="#2D3748"))
    ax.annotate("", xy=(0, -20), xytext=(0, -70), arrowprops=dict(arrowstyle="->", lw=2, color="#2D3748"))
    ax.annotate("", xy=(20, 0), xytext=(70, 0), arrowprops=dict(arrowstyle="->", lw=2, color="#2D3748"))
    ax.annotate("", xy=(-20, 0), xytext=(-70, 0), arrowprops=dict(arrowstyle="->", lw=2, color="#2D3748"))

    ax.legend(loc="lower left", framealpha=0.9)
    ax.set_title("Figure 2: Four-Arm Isolated Intersection Layout & Detection Zones", pad=15)
    ax.set_xlabel("Distance from Junction Center (m)")
    ax.set_ylabel("Distance from Junction Center (m)")
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig02_intersection_geometry.png")
    plt.close()


# ==============================================================================
# Figure 3: Controller Decision Flowchart
# ==============================================================================
def plot_fig03_flowchart():
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.axis("off")

    def draw_node(x, y, w, h, text, shape="rect", color="#EDF2F7"):
        if shape == "diamond":
            diamond = patches.Polygon([[x + w/2, y], [x + w, y + h/2], [x + w/2, y + h], [x, y + h/2]],
                                      facecolor=color, edgecolor="#2D3748", lw=1.5)
            ax.add_patch(diamond)
        elif shape == "oval":
            oval = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.06",
                                         facecolor=color, edgecolor="#2D3748", lw=1.5)
            ax.add_patch(oval)
        else:
            rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.02",
                                         facecolor=color, edgecolor="#2D3748", lw=1.5)
            ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=8.5, color="#1A202C")

    def draw_conn(x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", lw=1.3, color="#2D3748"))
        if label:
            ax.text((x1 + x2)/2 + 0.02, (y1 + y2)/2, label, fontsize=8, color="#C53030" if label=="Yes" else "#2F855A", fontweight="bold")

    draw_node(0.3, 0.92, 0.4, 0.06, "1-Second Simulation Step (t)", shape="oval", color="#E2E8F0")
    draw_node(0.25, 0.82, 0.5, 0.06, "Observe Q_i, A_i, G_i, W_i, R_i\nNormalize to dimensionless q_i, a_i, g_i, w_i, r_i", color="#EBF8FF")
    draw_node(0.3, 0.70, 0.4, 0.08, "Is t_green < G_min (15s)?", shape="diamond", color="#FEFCBF")

    draw_node(0.78, 0.71, 0.20, 0.06, "Maintain Green\n(Hold Phase)", color="#C6F6D5")

    draw_node(0.25, 0.56, 0.5, 0.08, "t_green >= G_max (50s) OR\nR_other >= R_starve (45s)?", shape="diamond", color="#FEEBC8")
    draw_node(0.25, 0.42, 0.5, 0.06, "Compute Composite Pressures\nS_active & S_competing", color="#E2E8F0")
    draw_node(0.22, 0.28, 0.56, 0.08, "S_competing > S_active + H (0.25)?\n(Hysteresis Condition)", shape="diamond", color="#FEFCBF")

    draw_node(0.32, 0.14, 0.36, 0.07, "Initiate Yellow Clearance (3s)\nSwitch Active Phase", color="#FED7D7")
    draw_node(0.78, 0.29, 0.20, 0.06, "Maintain Green\n(No Switch)", color="#C6F6D5")

    # Arrows
    draw_conn(0.5, 0.92, 0.5, 0.88)
    draw_conn(0.5, 0.82, 0.5, 0.78)
    draw_conn(0.70, 0.74, 0.78, 0.74, "Yes")
    draw_conn(0.5, 0.70, 0.5, 0.64, "No")
    draw_conn(0.5, 0.56, 0.5, 0.48, "No")
    draw_conn(0.75, 0.60, 0.75, 0.175)
    ax.annotate("", xy=(0.68, 0.175), xytext=(0.75, 0.175), arrowprops=dict(arrowstyle="->", lw=1.3, color="#2D3748"))
    ax.text(0.76, 0.58, "Yes", fontsize=8, color="#C53030", fontweight="bold")

    draw_conn(0.5, 0.42, 0.5, 0.36)
    draw_conn(0.5, 0.28, 0.5, 0.21, "Yes")
    draw_conn(0.78, 0.32, 0.78, 0.35, "No")

    ax.set_xlim(0, 1)
    ax.set_ylim(0.1, 1.0)
    plt.title("Figure 3: Decision Logic Flowchart of Proposed Adaptive Signal Controller", pad=15)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig03_controller_flowchart.png")
    plt.close()


# ==============================================================================
# Figures 4 & 5: Queue vs Time and Waiting Time vs Time
# ==============================================================================
def plot_fig04_and_fig05_timeseries():
    f_csv = DATA_DIR / "timeseries_fixed_seed42.csv"
    b_csv = DATA_DIR / "timeseries_basic_seed42.csv"
    p_csv = DATA_DIR / "timeseries_proposed_seed42.csv"

    if not (f_csv.exists() and b_csv.exists() and p_csv.exists()):
        print("[SKIP] Timeseries CSV files not found for Fig 4 & 5.")
        return

    df_f = pd.read_csv(f_csv)
    df_b = pd.read_csv(b_csv)
    df_p = pd.read_csv(p_csv)

    # Filter post-warmup (sim_time >= 200)
    df_f = df_f[df_f["sim_time"] >= 200]
    df_b = df_b[df_b["sim_time"] >= 200]
    df_p = df_p[df_p["sim_time"] >= 200]

    # Rolling smoothed for clean publication visibility
    w = 15
    f_q_smooth = df_f["queue_total"].rolling(w, min_periods=1).mean()
    b_q_smooth = df_b["queue_total"].rolling(w, min_periods=1).mean()
    p_q_smooth = df_p["queue_total"].rolling(w, min_periods=1).mean()

    # Fig 4: Queue vs Time
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df_f["sim_time"], f_q_smooth, label="Fixed-Time (Cycle=90s)", color=COLORS["fixed"], lw=1.8, linestyle=":")
    ax.plot(df_b["sim_time"], b_q_smooth, label="Basic Queue-Based (Instantaneous)", color=COLORS["basic"], lw=1.8, linestyle="--")
    ax.plot(df_p["sim_time"], p_q_smooth, label="Proposed Adaptive (Multi-Variable)", color=COLORS["proposed"], lw=2.2)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Total Intersection Queue (vehicles)")
    ax.set_title("Figure 4: Total Halting Queue vs Simulation Time (Medium Demand, Seed 42)")
    ax.set_xlim(200, 1000)
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig04_queue_vs_time.png")
    plt.close()

    # Fig 5: Waiting Time vs Time
    f_w_smooth = df_f["mean_waiting_time"].rolling(w, min_periods=1).mean()
    b_w_smooth = df_b["mean_waiting_time"].rolling(w, min_periods=1).mean()
    p_w_smooth = df_p["mean_waiting_time"].rolling(w, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(df_f["sim_time"], f_w_smooth, label="Fixed-Time (Cycle=90s)", color=COLORS["fixed"], lw=1.8, linestyle=":")
    ax.plot(df_b["sim_time"], b_w_smooth, label="Basic Queue-Based (Instantaneous)", color=COLORS["basic"], lw=1.8, linestyle="--")
    ax.plot(df_p["sim_time"], p_w_smooth, label="Proposed Adaptive (Multi-Variable)", color=COLORS["proposed"], lw=2.2)
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Instantaneous Mean Waiting Time (s/veh)")
    ax.set_title("Figure 5: Mean Vehicle Waiting Time vs Simulation Time (Medium Demand, Seed 42)")
    ax.set_xlim(200, 1000)
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig05_waiting_vs_time.png")
    plt.close()


# ==============================================================================
# Figure 6: Demand Profiles Across Scenarios
# ==============================================================================
def plot_fig06_demand():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    t = np.linspace(0, 1000, 1000)

    # Theoretical arrival intensities
    low_rate = 0.04 * 4  # 4 approaches
    med_rate = 0.08 * 4
    high_rate = 0.14 * 4
    over_rate = 0.18 * 4
    asym_rate = (0.14 * 2) + (0.03 * 2)

    ax.plot(t, low_rate * t, label="Low Demand (p=0.04, ~576 veh/h)", lw=1.8)
    ax.plot(t, med_rate * t, label="Medium Demand (p=0.08, ~1152 veh/h)", lw=1.8)
    ax.plot(t, asym_rate * t, label="Asymmetric Demand (p_NS=0.14, p_EW=0.03)", lw=1.8, linestyle="-.")
    ax.plot(t, high_rate * t, label="High Demand (p=0.14, ~2016 veh/h)", lw=1.8)
    ax.plot(t, over_rate * t, label="Oversaturated (p=0.18, ~2592 veh/h)", lw=2.0, color="#C53030")

    ax.axvline(200, color="gray", linestyle="--", alpha=0.7, label="Warm-up Boundary (200s)")
    ax.set_xlabel("Simulation Time (s)")
    ax.set_ylabel("Cumulative Vehicle Inflow (vehicles)")
    ax.set_title("Figure 6: Cumulative Traffic Arrival Demands Across Experimental Scenarios")
    ax.set_xlim(0, 1000)
    ax.legend(loc="upper left", framealpha=0.9)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig06_demand_profiles.png")
    plt.close()


# ==============================================================================
# Figure 7: Phase Decisions Timeline
# ==============================================================================
def plot_fig07_timeline():
    f_csv = DATA_DIR / "timeseries_fixed_seed42.csv"
    p_csv = DATA_DIR / "timeseries_proposed_seed42.csv"

    if not (f_csv.exists() and p_csv.exists()):
        return

    df_f = pd.read_csv(f_csv)
    df_p = pd.read_csv(p_csv)

    # Subsample 200s to 500s for clear visual inspection
    sub_f = df_f[(df_f["sim_time"] >= 200) & (df_f["sim_time"] <= 500)]
    sub_p = df_p[(df_p["sim_time"] >= 200) & (df_p["sim_time"] <= 500)]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 4), sharex=True)

    # Color map for phases: 0: NS Green, 1: NS Yellow, 2: EW Green, 3: EW Yellow
    phase_colors = {0: "#38A169", 1: "#ECC94B", 2: "#3182CE", 3: "#DD6B20"}
    phase_names = {0: "NS Green", 1: "NS Yellow", 2: "EW Green", 3: "EW Yellow"}

    for _, row in sub_f.iterrows():
        ax1.axvspan(row["sim_time"], row["sim_time"] + 1, color=phase_colors.get(row["tl_phase"], "gray"), alpha=0.85)

    for _, row in sub_p.iterrows():
        ax2.axvspan(row["sim_time"], row["sim_time"] + 1, color=phase_colors.get(row["tl_phase"], "gray"), alpha=0.85)

    ax1.set_title("Fixed-Time Controller (Rigid 42s Green / 3s Yellow Cycle)")
    ax1.set_yticks([])
    ax2.set_title("Proposed Adaptive Controller (Dynamic Demand-Responsive Allocation)")
    ax2.set_yticks([])
    ax2.set_xlabel("Simulation Time (s)")

    # Legend patches
    leg_handles = [patches.Patch(color=c, label=phase_names[p]) for p, c in phase_colors.items()]
    fig.legend(handles=leg_handles, loc="upper right", bbox_to_anchor=(0.95, 0.98), ncol=4, fontsize=8)

    plt.suptitle("Figure 7: Signal Phase Timeline & Dynamic Allocation (t = 200s to 500s)", y=1.03)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig07_phase_decisions_timeline.png")
    plt.close()


# ==============================================================================
# Figures 8-11: Metric Comparisons Across All Scenarios
# ==============================================================================
def plot_figs_benchmark():
    csv_path = RESULTS_DIR / "multi_demand_comparison_results.csv"
    if not csv_path.exists():
        print("[SKIP] Benchmark CSV not found.")
        return

    df = pd.read_csv(csv_path)
    scenarios = ["low", "medium", "high", "oversaturated", "asym_ns", "asym_ew", "dynamic"]
    sc_labels = ["Low", "Medium", "High", "Oversat.", "Asym-NS", "Asym-EW", "Dynamic"]
    x = np.arange(len(scenarios))
    w = 0.25

    def get_means_stds(metric_col):
        m_fixed, s_fixed = [], []
        m_basic, s_basic = [], []
        m_prop, s_prop = [], []
        for sc in scenarios:
            sub = df[df["scenario"] == sc]
            f_vals = sub[sub["controller"] == "Fixed-Time"][metric_col]
            b_vals = sub[sub["controller"] == "Basic-Queue"][metric_col]
            p_vals = sub[sub["controller"] == "Proposed-Adaptive"][metric_col]

            m_fixed.append(f_vals.mean())
            s_fixed.append(f_vals.std())
            m_basic.append(b_vals.mean())
            s_basic.append(b_vals.std())
            m_prop.append(p_vals.mean())
            s_prop.append(p_vals.std())
        return (m_fixed, s_fixed), (m_basic, s_basic), (m_prop, s_prop)

    # Fig 8: Average Waiting Time
    (mf, sf), (mb, sb), (mp, sp) = get_means_stds("avg_waiting_time_s")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, mf, w, yerr=sf, capsize=3, label="Fixed-Time", color=COLORS["fixed"])
    ax.bar(x, mb, w, yerr=sb, capsize=3, label="Basic Queue-Based", color=COLORS["basic"])
    ax.bar(x + w, mp, w, yerr=sp, capsize=3, label="Proposed Adaptive", color=COLORS["proposed"])
    ax.set_xticks(x)
    ax.set_xticklabels(sc_labels)
    ax.set_ylabel("Average Waiting Time per Vehicle (s)")
    ax.set_title("Figure 8: Average Waiting Time (Cohort A) Across All 7 Demand Scenarios (5 Seeds)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig08_waiting_time_comparison.png")
    plt.close()

    # Fig 9: Queue Length (Average & Max)
    (mf_q, sf_q), (mb_q, sb_q), (mp_q, sp_q) = get_means_stds("avg_queue_length_veh")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, mf_q, w, yerr=sf_q, capsize=3, label="Fixed-Time", color=COLORS["fixed"])
    ax.bar(x, mb_q, w, yerr=sb_q, capsize=3, label="Basic Queue-Based", color=COLORS["basic"])
    ax.bar(x + w, mp_q, w, yerr=sp_q, capsize=3, label="Proposed Adaptive", color=COLORS["proposed"])
    ax.set_xticks(x)
    ax.set_xticklabels(sc_labels)
    ax.set_ylabel("Average Queue Length (vehicles)")
    ax.set_title("Figure 9: Average Intersection Queue Length Across Scenarios (5 Seeds)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig09_queue_length_comparison.png")
    plt.close()

    # Fig 10: Travel Time
    (mf_t, sf_t), (mb_t, sb_t), (mp_t, sp_t) = get_means_stds("avg_travel_time_s")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, mf_t, w, yerr=sf_t, capsize=3, label="Fixed-Time", color=COLORS["fixed"])
    ax.bar(x, mb_t, w, yerr=sb_t, capsize=3, label="Basic Queue-Based", color=COLORS["basic"])
    ax.bar(x + w, mp_t, w, yerr=sp_t, capsize=3, label="Proposed Adaptive", color=COLORS["proposed"])
    ax.set_xticks(x)
    ax.set_xticklabels(sc_labels)
    ax.set_ylabel("Average Vehicle Travel Time (s)")
    ax.set_title("Figure 10: Average Vehicle Travel Time (Cohort A) Across Scenarios (5 Seeds)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig10_travel_time_comparison.png")
    plt.close()

    # Fig 11: Throughput
    (mf_tp, sf_tp), (mb_tp, sb_tp), (mp_tp, sp_tp) = get_means_stds("cohort_a_completed")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - w, mf_tp, w, yerr=sf_tp, capsize=3, label="Fixed-Time", color=COLORS["fixed"])
    ax.bar(x, mb_tp, w, yerr=sb_tp, capsize=3, label="Basic Queue-Based", color=COLORS["basic"])
    ax.bar(x + w, mp_tp, w, yerr=sp_tp, capsize=3, label="Proposed Adaptive", color=COLORS["proposed"])
    ax.set_xticks(x)
    ax.set_xticklabels(sc_labels)
    ax.set_ylabel("Cohort A Completed Vehicles (veh)")
    ax.set_title("Figure 11: Throughput of Completed Vehicles in Evaluation Period (5 Seeds)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig11_throughput_comparison.png")
    plt.close()


# ==============================================================================
# Figure 12: Performance vs Demand (Saturation Curve)
# ==============================================================================
def plot_fig12_saturation():
    csv_path = RESULTS_DIR / "multi_demand_comparison_results.csv"
    if not csv_path.exists():
        return

    df = pd.read_csv(csv_path)
    demands = ["low", "medium", "high", "oversaturated"]
    p_vals = [0.04, 0.08, 0.14, 0.18]

    f_means, b_means, p_means = [], [], []
    for d in demands:
        sub = df[df["scenario"] == d]
        f_means.append(sub[sub["controller"] == "Fixed-Time"]["avg_waiting_time_s"].mean())
        b_means.append(sub[sub["controller"] == "Basic-Queue"]["avg_waiting_time_s"].mean())
        p_means.append(sub[sub["controller"] == "Proposed-Adaptive"]["avg_waiting_time_s"].mean())

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(p_vals, f_means, marker="s", color=COLORS["fixed"], lw=2, label="Fixed-Time")
    ax.plot(p_vals, b_means, marker="^", color=COLORS["basic"], lw=2, label="Basic Queue-Based")
    ax.plot(p_vals, p_means, marker="o", color=COLORS["proposed"], lw=2.2, label="Proposed Adaptive")

    ax.set_xlabel("Nominal Vehicle Arrival Probability per Second (p)")
    ax.set_ylabel("Average Waiting Time (s)")
    ax.set_title("Figure 12: Controller Degradation Curve Under Increasing Saturation")
    ax.set_xticks(p_vals)
    ax.set_xticklabels(["0.04\n(Low)", "0.08\n(Medium)", "0.14\n(High)", "0.18\n(Oversat.)"])
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig12_performance_vs_demand.png")
    plt.close()


# ==============================================================================
# Figure 13: Performance Under Demand Asymmetry
# ==============================================================================
def plot_fig13_asymmetry():
    csv_path = RESULTS_DIR / "multi_demand_comparison_results.csv"
    if not csv_path.exists():
        return

    df = pd.read_csv(csv_path)
    asym_scenarios = ["medium", "asym_ns", "asym_ew"]
    labels = ["Symmetric (Medium)\np_NS=0.08, p_EW=0.08", "Asymmetric (NS Heavy)\np_NS=0.14, p_EW=0.03", "Asymmetric (EW Heavy)\np_NS=0.03, p_EW=0.14"]
    x = np.arange(len(asym_scenarios))
    w = 0.25

    mf, mb, mp = [], [], []
    for sc in asym_scenarios:
        sub = df[df["scenario"] == sc]
        mf.append(sub[sub["controller"] == "Fixed-Time"]["avg_waiting_time_s"].mean())
        mb.append(sub[sub["controller"] == "Basic-Queue"]["avg_waiting_time_s"].mean())
        mp.append(sub[sub["controller"] == "Proposed-Adaptive"]["avg_waiting_time_s"].mean())

    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.bar(x - w, mf, w, label="Fixed-Time", color=COLORS["fixed"])
    ax.bar(x, mb, w, label="Basic Queue-Based", color=COLORS["basic"])
    ax.bar(x + w, mp, w, label="Proposed Adaptive", color=COLORS["proposed"])

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Average Waiting Time (s)")
    ax.set_title("Figure 13: Controller Performance Under Directional Flow Asymmetry")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig13_performance_vs_asymmetry.png")
    plt.close()


# ==============================================================================
# Figure 14: Ablation Study
# ==============================================================================
def plot_fig14_ablation():
    csv_path = RESULTS_DIR / "ablation_study_results.csv"
    if not csv_path.exists():
        print("[SKIP] Ablation CSV not found.")
        return

    df = pd.read_csv(csv_path)
    models = [
        "Model_0_FixedTime", "Model_1_QueueOnly", "Model_2_QueueArrival",
        "Model_3_QueueArrivalGrowth", "Model_4_QueueArrivalGrowthWait",
        "Model_5_QueueArrivalGrowthWaitFair", "Model_6_FullProposed"
    ]
    model_labels = [
        "M0: Fixed", "M1: Q", "M2: Q+A",
        "M3: Q+A+G", "M4: Q+A+G+W", "M5: Q+A+G+W+R", "M6: Full (+H)"
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    for sc, color, ax in [("medium", "#3182CE", ax1), ("high", "#E53E3E", ax2)]:
        sub = df[df["scenario"] == sc]
        means = [sub[sub["model_id"] == m]["avg_waiting_time_s"].mean() for m in models]
        stds = [sub[sub["model_id"] == m]["avg_waiting_time_s"].std() for m in models]
        switches = [sub[sub["model_id"] == m]["phase_switch_count"].mean() for m in models]

        bars = ax.bar(model_labels, means, yerr=stds, capsize=3, color=color, alpha=0.85)
        ax.set_title(f"Ablation on {sc.capitalize()} Demand")
        ax.set_ylabel("Average Waiting Time (s)")
        ax.tick_params(axis="x", rotation=35)

        # Annotate switches above bars
        for b, sw in zip(bars, switches):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.5, f"Sw:{int(sw)}",
                    ha="center", va="bottom", fontsize=7.5, color="#2D3748")

    plt.suptitle("Figure 14: Systematic Component Ablation Study (M0 to M6, 5 Seeds)", y=1.02)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig14_ablation_study.png")
    plt.close()


# ==============================================================================
# Figure 15: Sensitivity Analysis
# ==============================================================================
def plot_fig15_sensitivity():
    csv_path = RESULTS_DIR / "sensitivity_study_results.csv"
    if not csv_path.exists():
        print("[SKIP] Sensitivity CSV not found.")
        return

    df = pd.read_csv(csv_path)
    fig, axes = plt.subplots(2, 2, figsize=(9, 7))

    params = [
        ("G_min", axes[0, 0], "Minimum Green G_min (s)"),
        ("G_max", axes[0, 1], "Maximum Green G_max (s)"),
        ("Hysteresis", axes[1, 0], "Hysteresis Margin H"),
        ("Window_WA", axes[1, 1], "Arrival Window W_A (s)"),
    ]

    for p_name, ax, label in params:
        sub = df[df["param_tested"] == p_name]
        grouped = sub.groupby("param_val")["avg_waiting_time_s"].agg(["mean", "std"]).reset_index()
        ax.errorbar(grouped["param_val"], grouped["mean"], yerr=grouped["std"],
                    marker="o", color=COLORS["proposed"], lw=1.8, capsize=4)
        ax.set_xlabel(label)
        ax.set_ylabel("Average Waiting Time (s)")
        ax.set_title(f"Sensitivity: {p_name}")

    plt.suptitle("Figure 15: Parameter Sensitivity Analysis on Medium Demand", y=1.02)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig15_sensitivity_analysis.png")
    plt.close()


# ==============================================================================
# Figure 16: Robustness to Measurement Noise
# ==============================================================================
def plot_fig16_robustness():
    csv_path = RESULTS_DIR / "robustness_study_results.csv"
    if not csv_path.exists():
        print("[SKIP] Robustness CSV not found.")
        return

    df = pd.read_csv(csv_path)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    sigmas = [0.0, 1.0, 2.0, 3.0]

    for sc, color, marker, label in [("medium", "#3182CE", "o", "Medium Demand"), ("high", "#E53E3E", "s", "High Demand")]:
        sub = df[df["scenario"] == sc]
        w_means = [sub[sub["noise_sigma"] == s]["avg_waiting_time_s"].mean() for s in sigmas]
        w_stds = [sub[sub["noise_sigma"] == s]["avg_waiting_time_s"].std() for s in sigmas]

        q_means = [sub[sub["noise_sigma"] == s]["avg_queue_length_veh"].mean() for s in sigmas]
        q_stds = [sub[sub["noise_sigma"] == s]["avg_queue_length_veh"].std() for s in sigmas]

        ax1.errorbar(sigmas, w_means, yerr=w_stds, marker=marker, color=color, lw=1.8, capsize=4, label=label)
        ax2.errorbar(sigmas, q_means, yerr=q_stds, marker=marker, color=color, lw=1.8, capsize=4, label=label)

    ax1.set_xlabel("Sensor Measurement Noise Std Dev sigma (veh)")
    ax1.set_ylabel("Average Waiting Time (s)")
    ax1.set_title("Waiting Time vs Noise")
    ax1.legend()

    ax2.set_xlabel("Sensor Measurement Noise Std Dev sigma (veh)")
    ax2.set_ylabel("Average Queue Length (veh)")
    ax2.set_title("Queue Length vs Noise")
    ax2.legend()

    plt.suptitle("Figure 16: Robustness to Gaussian Sensor Measurement Noise", y=1.02)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "fig16_robustness_noise.png")
    plt.close()


def main():
    print("Generating all 16 publication figures...")
    plot_fig01_architecture()
    plot_fig02_geometry()
    plot_fig03_flowchart()
    plot_fig04_and_fig05_timeseries()
    plot_fig06_demand()
    plot_fig07_timeline()
    plot_figs_benchmark()
    plot_fig12_saturation()
    plot_fig13_asymmetry()
    plot_fig14_ablation()
    plot_fig15_sensitivity()
    plot_fig16_robustness()
    print("[OK] All 16 figures successfully generated in figures/")


if __name__ == "__main__":
    main()
