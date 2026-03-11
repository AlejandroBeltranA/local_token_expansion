"""
Generate figures for the LTE whitepaper.

Outputs to docs/figures/:
  figure1_pipeline.png        — Intervention pipeline diagram
  figure2_trigger_heatmap.png — Trigger × model heatmap  (reading order: appears first in results)
  figure3_stress_timeline.png — Latency stress timeline   (reading order: appears second in results)
  figure4_failure_breakdown.png — Recoverable vs unrecoverable probe failures per model
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT_DIR = Path(__file__).parent.parent / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_ROOT = Path(__file__).parent.parent / "results" / "weekend_sweep_full" / "runs"

# ── Palette ─────────────────────────────────────────────────────────────────
ESCALATE_COLOR  = "#E8A838"
ABORT_COLOR     = "#C94040"
NEUTRAL_COLOR   = "#4A7FC1"
LIGHT_GRAY      = "#F2F2F2"
MID_GRAY        = "#CCCCCC"
TEXT_DARK       = "#1A1A1A"
TEXT_MID        = "#555555"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


# ────────────────────────────────────────────────────────────────────────────
# Figure 1 — Intervention pipeline
# ────────────────────────────────────────────────────────────────────────────

def make_figure1():
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    stages = [
        (1.1,  "Model Output",       "raw generation",                          NEUTRAL_COLOR),
        (3.3,  "Metrics",            "ER · LORR · RCS · Latency",               NEUTRAL_COLOR),
        (5.5,  "Trigger Evaluation", "6 failure families",                      NEUTRAL_COLOR),
        (7.7,  "Intervention State", "continue / retry / repair\nescalate / abort", NEUTRAL_COLOR),
        (9.9,  "Action",             "automated response\n+ audit log",         "#5A9E6F"),
    ]

    box_w, box_h = 1.65, 1.4
    arrow_y = 1.6

    for x, label, sublabel, color in stages:
        rect = mpatches.FancyBboxPatch(
            (x - box_w / 2, arrow_y - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.08", linewidth=1.2,
            edgecolor=color, facecolor=color + "18",
        )
        ax.add_patch(rect)
        ax.text(x, arrow_y + 0.22, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color=color)
        ax.text(x, arrow_y - 0.28, sublabel, ha="center", va="center",
                fontsize=8.5, color=TEXT_MID, linespacing=1.4)

    for i in range(len(stages) - 1):
        x0 = stages[i][0] + box_w / 2 + 0.02
        x1 = stages[i + 1][0] - box_w / 2 - 0.02
        ax.annotate("", xy=(x1, arrow_y), xytext=(x0, arrow_y),
                    arrowprops=dict(arrowstyle="-|>", color=MID_GRAY, lw=1.4))

    # Title lives in the markdown, not the figure
    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure1_pipeline.png", bbox_inches="tight")
    plt.close(fig)
    print("  Saved figure1_pipeline.png")


# ────────────────────────────────────────────────────────────────────────────
# Figure 2 — Trigger × model heatmap  (appears first in results section)
# ────────────────────────────────────────────────────────────────────────────

def make_figure2():
    models = [
        "Phi-4-mini\n8bit",
        "Meta-Llama-3.1\n8B-3bit",
        "Mistral-7B\nv0.3",
        "Phi-3-mini\n4k-4bit",
        "SmolLM\n1.7B-4bit",
    ]
    regimes = ["escalate", "escalate", "abort", "abort", "abort"]

    trigger_labels = [
        "Over-expansion",
        "Near-cap pressure",
        "Context decay",
        "Latency cliff",
        "Persistent failure",
    ]

    # 1 = fired in all 6/6 baseline runs
    #            Phi-4  Llama  Mistral  Phi-3  SmolLM
    fired_T = np.array([
        [1,      1,     1,       1,     1],   # over_expansion
        [0,      0,     0,       1,     1],   # near_cap_pressure
        [1,      1,     0,       1,     1],   # context_decay
        [0,      0,     1,       0,     0],   # latency_cliff
        [0,      0,     1,       1,     1],   # persistent_failure
    ])
    fired = fired_T.T  # rows=models, cols=triggers

    fig, ax = plt.subplots(figsize=(9, 4.2))
    regime_colors = [ESCALATE_COLOR if r == "escalate" else ABORT_COLOR for r in regimes]

    for mi, (model, regime_color) in enumerate(zip(models, regime_colors)):
        for ti in range(len(trigger_labels)):
            val = fired[mi, ti]
            face = regime_color if val else LIGHT_GRAY
            edge = regime_color if val else MID_GRAY
            rect = mpatches.FancyBboxPatch(
                (ti + 0.1, mi + 0.1), 0.8, 0.8,
                boxstyle="round,pad=0.05",
                facecolor=face + ("CC" if val else ""),
                edgecolor=edge, linewidth=1.2,
            )
            ax.add_patch(rect)
            if val:
                ax.text(ti + 0.5, mi + 0.5, "✓", ha="center", va="center",
                        fontsize=13, color="white", fontweight="bold")

    for mi, (model, regime, color) in enumerate(zip(models, regimes, regime_colors)):
        ax.text(-0.15, mi + 0.5, model, ha="right", va="center",
                fontsize=9, color=TEXT_DARK)
        ax.text(-1.6, mi + 0.5, f"→ {regime}", ha="left", va="center",
                fontsize=8.5, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.25", fc=color + "20", ec=color, lw=0.9))

    for ti, label in enumerate(trigger_labels):
        ax.text(ti + 0.5, len(models) + 0.15, label, ha="center", va="bottom",
                fontsize=9, color=TEXT_MID, rotation=20)

    ax.set_xlim(-1.85, len(trigger_labels))
    ax.set_ylim(-0.2, len(models) + 0.7)
    ax.axis("off")

    legend_elements = [
        mpatches.Patch(facecolor=ESCALATE_COLOR + "CC", edgecolor=ESCALATE_COLOR, label="escalate regime"),
        mpatches.Patch(facecolor=ABORT_COLOR    + "CC", edgecolor=ABORT_COLOR,    label="abort regime"),
        mpatches.Patch(facecolor=LIGHT_GRAY,             edgecolor=MID_GRAY,       label="trigger did not fire"),
    ]
    ax.legend(handles=legend_elements, loc="upper center",
              bbox_to_anchor=(0.5, -0.04), ncol=3, fontsize=8.5,
              frameon=True, framealpha=0.9)
    # Title lives in the markdown

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure2_trigger_heatmap.png", bbox_inches="tight")
    plt.close(fig)
    print("  Saved figure2_trigger_heatmap.png")


# ────────────────────────────────────────────────────────────────────────────
# Figure 3 — Stress latency timeline  (appears second in results section)
# ────────────────────────────────────────────────────────────────────────────

def load_stress(run_dir: Path):
    with open(run_dir / "stress.jsonl") as f:
        return [json.loads(l) for l in f]


def make_figure3():
    mistral_run = RESULTS_ROOT / "unified_weekend_baseline_mistral-7b-instruct-v03_t0p0_m192_s0"
    phi4_run    = RESULTS_ROOT / "unified_weekend_baseline_phi-4-mini-instruct-8bit_t0p0_m192_s0"

    mistral = load_stress(mistral_run)
    phi4    = load_stress(phi4_run)

    LATENCY_THRESHOLD_MS = 7500

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=False)

    def plot_model(ax, data, label, color, regime, threshold=None):
        steps   = [d["step"] for d in data]
        latency = [d["latency_ms"] / 1000 for d in data]
        failures = [d["failure_reasons"] for d in data]

        ax.plot(steps, latency, color=color, lw=2, zorder=3)
        ax.fill_between(steps, latency, alpha=0.10, color=color)

        for s, l, fr in zip(steps, latency, failures):
            if fr:
                ax.scatter(s, l, s=60, color=ABORT_COLOR, zorder=5)

        if threshold is not None:
            thresh_s = threshold / 1000
            ax.axhline(thresh_s, color=ABORT_COLOR, lw=1.2, ls="--", alpha=0.7)
            ax.text(0.01, thresh_s + 0.12, "latency threshold",
                    color=ABORT_COLOR, fontsize=8.5, va="bottom",
                    transform=ax.get_yaxis_transform())

        regime_color = ABORT_COLOR if regime == "abort" else ESCALATE_COLOR
        ax.set_title(label, fontsize=11, fontweight="bold", color=TEXT_DARK, pad=6)
        ax.text(0.98, 0.08, f"→ {regime}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=10, fontweight="bold",
                color=regime_color,
                bbox=dict(boxstyle="round,pad=0.3", fc=regime_color + "18",
                          ec=regime_color, lw=1))
        ax.set_xlabel("Stress step (growing context)", fontsize=9.5, color=TEXT_MID)
        ax.set_ylabel("Latency (seconds)", fontsize=9.5, color=TEXT_MID)
        ax.tick_params(colors=TEXT_MID)
        ax.spines["bottom"].set_color(MID_GRAY)
        ax.spines["left"].set_color(MID_GRAY)

    plot_model(axes[0], mistral, "Mistral-7B-Instruct-v0.3",
               ABORT_COLOR, regime="abort", threshold=LATENCY_THRESHOLD_MS)
    plot_model(axes[1], phi4, "Phi-4-mini-instruct-8bit",
               ESCALATE_COLOR, regime="escalate", threshold=LATENCY_THRESHOLD_MS)

    # Mistral: annotate the cliff
    axes[0].annotate("latency cliff\n(steps 15–17)",
                     xy=(15, mistral[15]["latency_ms"] / 1000),
                     xytext=(8, mistral[10]["latency_ms"] / 1000 + 0.8),
                     fontsize=8.5, color=ABORT_COLOR,
                     arrowprops=dict(arrowstyle="->", color=ABORT_COLOR, lw=1))

    # Phi-4: explain why escalate fires despite clean latency — plain language, mid-chart
    axes[1].text(0.04, 0.55,
                 "Speed is fine throughout.\nEscalate fires because the model\nrepeatedly exceeded output word\nlimits and failed to carry state\ncorrectly across turns — failures\nthat don't show up in latency\nbut do show up in Fig 4.",
                 transform=axes[1].transAxes,
                 ha="left", va="center", fontsize=8, color=ESCALATE_COLOR,
                 bbox=dict(boxstyle="round,pad=0.4", fc=ESCALATE_COLOR + "12",
                           ec=ESCALATE_COLOR, lw=0.8))

    fig.text(0.01, -0.02,
             "Red dots mark steps where a failure condition was triggered. "
             "Mistral produces semantically stable output throughout, but becomes operationally unusable at step 15.",
             fontsize=8.5, color=TEXT_MID)

    # Title lives in the markdown
    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure3_stress_timeline.png", bbox_inches="tight")
    plt.close(fig)
    print("  Saved figure3_stress_timeline.png")


# ────────────────────────────────────────────────────────────────────────────
# Figure 4 — Recoverable vs unrecoverable probe failures per model
# ────────────────────────────────────────────────────────────────────────────

def make_figure4():
    # From baseline_phase_summary.json
    models_short = ["Phi-4-mini\n8bit", "Meta-Llama\n8B-3bit", "Mistral-7B\nv0.3",
                    "Phi-3-mini\n4k-4bit", "SmolLM\n1.7B-4bit"]
    regimes      = ["escalate", "escalate", "abort", "abort", "abort"]
    recoverable  = [4.0, 5.0, 3.0, 8.0, 6.0]
    unrecoverable= [3.0, 4.0, 1.0, 3.0, 6.0]
    TOTAL_PROBES = 14

    regime_colors = [ESCALATE_COLOR if r == "escalate" else ABORT_COLOR for r in regimes]

    fig, ax = plt.subplots(figsize=(10, 4.5))

    x = np.arange(len(models_short))
    bar_w = 0.55

    # Recoverable bars (lighter — 60% opacity approximated via hex)
    bars_r = ax.bar(x, recoverable, bar_w,
                    color=[c + "70" for c in regime_colors],
                    edgecolor=regime_colors, linewidth=1.1,
                    label="recoverable")

    # Unrecoverable bars stacked on top (full opacity)
    bars_u = ax.bar(x, unrecoverable, bar_w, bottom=recoverable,
                    color=regime_colors,
                    edgecolor=[TEXT_DARK] * len(models_short), linewidth=0.6,
                    label="unrecoverable")

    # Reference line: total probe battery
    ax.axhline(TOTAL_PROBES, color=MID_GRAY, lw=1.2, ls="--")
    ax.text(len(models_short) - 0.5, TOTAL_PROBES + 0.3, f"total probes ({TOTAL_PROBES})",
            ha="right", va="bottom", fontsize=8.5, color=TEXT_MID)

    # Annotate Mistral — straight above its own bar, plain language
    mistral_idx = 2
    total_mistral = recoverable[mistral_idx] + unrecoverable[mistral_idx]
    ax.annotate("Became too slow to use\nat 9+ secs by step 15.\n(See Fig 3)",
                xy=(mistral_idx, total_mistral + 0.3),
                xytext=(mistral_idx, total_mistral + 7.2),
                fontsize=8, color=ABORT_COLOR, ha="center",
                arrowprops=dict(arrowstyle="->", color=ABORT_COLOR, lw=1))

    # Total failure count labels on bars
    for i, (r, u) in enumerate(zip(recoverable, unrecoverable)):
        total = r + u
        ax.text(i, total + 0.2, f"{int(total)}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=TEXT_DARK)

    # Regime badges below x-axis labels
    for i, (regime, color) in enumerate(zip(regimes, regime_colors)):
        ax.text(i, -2.4, f"→ {regime}", ha="center", va="top",
                fontsize=8, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc=color + "18", ec=color, lw=0.8))

    ax.set_xticks(x)
    ax.set_xticklabels(models_short, fontsize=9, color=TEXT_DARK)
    ax.tick_params(axis="x", which="both", length=0, pad=20)
    ax.set_ylabel("Mean probe failures (of 14)", fontsize=9.5, color=TEXT_MID)
    ax.set_ylim(-3.5, TOTAL_PROBES + 3)
    ax.tick_params(colors=TEXT_MID)
    ax.spines["bottom"].set_color(MID_GRAY)
    ax.spines["left"].set_color(MID_GRAY)

    legend_elements = [
        mpatches.Patch(facecolor=MID_GRAY + "70", edgecolor=TEXT_MID,
                       label="recoverable (retry / repair possible)"),
        mpatches.Patch(facecolor=TEXT_MID, edgecolor=TEXT_DARK,
                       label="unrecoverable (escalate / abort required)"),
    ]
    ax.legend(handles=legend_elements, fontsize=8.5, loc="upper left",
              frameon=True, framealpha=0.9)

    # Title lives in the markdown

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure4_failure_breakdown.png", bbox_inches="tight")
    plt.close(fig)
    print("  Saved figure4_failure_breakdown.png")


# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Writing figures to {OUT_DIR}/")
    make_figure1()
    make_figure2()
    make_figure3()
    make_figure4()
    print("Done.")
