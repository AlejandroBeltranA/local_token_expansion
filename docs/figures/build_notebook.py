#!/usr/bin/env python3
"""Generates paper_figures.ipynb — run once to create the notebook."""

import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.0"},
}

def md(src): return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

cells = []

# ── Title ─────────────────────────────────────────────────────────────────────
cells.append(md("""\
# LTE Paper Figures

Six figures for the TAIGR @ ICML 2026 paper.
Run from the repo root. Figures are saved to `docs/figures/`.

| Figure | Description |
|--------|-------------|
| 1 | Intervention pipeline |
| 2 | Trigger × model heatmap (7 models) |
| 3 | Stress timeline: Mistral-7B vs Claude Haiku 4.5 |
| 4 | Recoverable vs unrecoverable failures (7 models) |
| 5 | Scaffold path: shared battery, model exit points |
| 6 | Benchmark failures vs stress resilience — the key scatter |
"""))

# ── Imports ───────────────────────────────────────────────────────────────────
cells.append(code("""\
import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Repo root detection ───────────────────────────────────────────────────────
# Works regardless of whether you run the notebook from the repo root,
# from docs/figures/, or anywhere else.
def _find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "results").exists() and (p / "lte").exists():
            return p
    raise RuntimeError(
        f"Could not locate repo root from {start}. "
        "Make sure the notebook is inside the local_token_expansion repo."
    )

REPO_ROOT     = _find_repo_root(Path.cwd())
LOCAL_RUNS    = REPO_ROOT / "results" / "weekend_sweep_full" / "runs"
API_RUNS      = REPO_ROOT / "results" / "api_baseline_sweep" / "runs"
LOCAL_SUMMARY = REPO_ROOT / "results" / "weekend_sweep_full" / "baseline_phase_summary.json"
API_SUMMARY   = REPO_ROOT / "results" / "api_baseline_sweep"  / "baseline_phase_summary.json"
OUT_DIR       = REPO_ROOT / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root : {REPO_ROOT}")
print(f"Output dir: {OUT_DIR}")
"""))

# ── Palette ───────────────────────────────────────────────────────────────────
cells.append(code("""\
# ── Palette & style ──────────────────────────────────────────────────────────
# Canonical colours for this paper. These supersede the values in
# scripts/generate_figures.py (ESCALATE_COLOR="#E8A838", ABORT_COLOR="#C94040").
# All six figures use these three colours for intervention states.
RETRY_C    = "#2d6a4f"
ESCALATE_C = "#c07530"
ABORT_C    = "#b03030"
RETRY_BG   = "#c8ecd6"
ESC_BG     = "#fad9b0"
ABORT_BG   = "#f5c4c4"
NEUTRAL_C  = "#4A7FC1"
LIGHT_GRAY = "#F2F2F2"
MID_GRAY   = "#CCCCCC"
TEXT_DARK  = "#1A1A1A"
TEXT_MID   = "#555555"

REGIME_COLOR = {"retry": RETRY_C, "escalate": ESCALATE_C, "abort": ABORT_C}
REGIME_BG    = {"retry": RETRY_BG,"escalate": ESC_BG,     "abort": ABORT_BG}

plt.rcParams.update({
    "font.family":        "sans-serif",
    "font.size":          11,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "figure.dpi":         150,
})
SAVE_KW = dict(bbox_inches="tight", dpi=150)
"""))

# ── Data loading ──────────────────────────────────────────────────────────────
cells.append(code("""\
# ── Data loading ─────────────────────────────────────────────────────────────
# Stress steps completed before exit — from stress.jsonl line counts + summary.
# Phi-3 and SmolLM: 3 lines each (steps 0–2, abort after 3 consecutive failures).
# Mistral: first_gated_failure_step_range = [15, 15].
# Haiku, GPT-4o mini, Phi-4, Llama: complete all 22 steps.
STRESS_EXIT = {
    "GPT-4o mini":      22,
    "Claude Haiku 4.5": 22,
    "Phi-4-mini":       22,
    "Llama-3.1-8B":     22,
    "Mistral-7B":       15,
    "Phi-3-mini":        2,
    "SmolLM-1.7B":       2,
}
DISPLAY = {
    "GPT-4o mini":                     "GPT-4o mini",
    "Claude Haiku 4.5":                "Claude Haiku 4.5",
    "Mistral-7B-Instruct-v0.3":        "Mistral-7B",
    "Phi-4-mini-instruct-8bit":        "Phi-4-mini",
    "Meta-Llama-3.1-8B-Instruct-3bit": "Llama-3.1-8B",
    "Phi-3-mini-4k-instruct-4bit":     "Phi-3-mini",
    "SmolLM-1.7B-Instruct-4bit":       "SmolLM-1.7B",
}

def _load(path, backend):
    with open(path) as f:
        raw = json.load(f)
    out = []
    for m in raw["models"]:
        regime = max(m["recommendation_counts"], key=m["recommendation_counts"].get)
        short  = DISPLAY.get(m["model_name"], m["model_name"])
        out.append({
            "name":        short,
            "full":        m["model_name"],
            "backend":     backend,
            "regime":      regime,
            "failures":    m["benchmark_contract_failures_mean"],
            "recoverable": m["recoverable_contract_failures_mean"],
            "unrecoverable": m["unrecoverable_contract_failures_mean"],
            "latency_ms":  m["mean_stress_latency_ms_mean"],
            "triggers":    set(m["trigger_fire_counts"].keys()),
            "steps":       STRESS_EXIT.get(short, 22),
        })
    return out

local_models = _load(LOCAL_SUMMARY, "local")
api_models   = _load(API_SUMMARY,   "API")
all_models   = api_models + local_models   # API first (better performers appear at top of figures)

print(f"{'Model':<24} {'Regime':<10} {'Failures':>8}  {'Steps':>5}")
print("-" * 54)
for m in all_models:
    print(f"{m['name']:<24} {m['regime']:<10} {m['failures']:>8.1f}  {m['steps']:>5}")
"""))

# ── Figure 1 ──────────────────────────────────────────────────────────────────
cells.append(md("## Figure 1 — Intervention Pipeline"))
cells.append(code("""\
def make_figure1():
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    stages = [
        (1.1,  "Model Output",       "raw generation",                               NEUTRAL_C),
        (3.3,  "Metrics",            "ER · LORR · RCS · Latency",                    NEUTRAL_C),
        (5.5,  "Trigger Evaluation", "6 failure families",                           NEUTRAL_C),
        (7.7,  "Intervention State", "continue / retry / repair\\nescalate / abort", NEUTRAL_C),
        (9.9,  "Action",             "automated response\\n+ audit log",              "#5A9E6F"),
    ]
    box_w, box_h, arrow_y = 1.65, 1.4, 1.6

    for x, label, sublabel, color in stages:
        rect = mpatches.FancyBboxPatch(
            (x - box_w/2, arrow_y - box_h/2), box_w, box_h,
            boxstyle="round,pad=0.08", linewidth=1.2,
            edgecolor=color, facecolor=color + "18",
        )
        ax.add_patch(rect)
        ax.text(x, arrow_y + 0.22, label,    ha="center", va="center",
                fontsize=10, fontweight="bold", color=color)
        ax.text(x, arrow_y - 0.28, sublabel, ha="center", va="center",
                fontsize=8.5, color=TEXT_MID, linespacing=1.4)

    for i in range(len(stages) - 1):
        x0 = stages[i][0]   + box_w/2 + 0.02
        x1 = stages[i+1][0] - box_w/2 - 0.02
        ax.annotate("", xy=(x1, arrow_y), xytext=(x0, arrow_y),
                    arrowprops=dict(arrowstyle="-|>", color=MID_GRAY, lw=1.4))

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure1_pipeline.png", **SAVE_KW)
    plt.show()

make_figure1()
"""))

# ── Figure 2 ──────────────────────────────────────────────────────────────────
cells.append(md("## Figure 2 — Trigger × Model Heatmap (7 models)"))
cells.append(code("""\
TRIGGER_KEYS   = ["over_expansion","near_cap_pressure","context_decay","latency_cliff","persistent_failure"]
TRIGGER_LABELS = ["Over-expansion","Near-cap pressure","Context decay","Latency cliff","Persistent failure"]

def make_figure2():
    models_sorted = sorted(all_models, key=lambda m: m["failures"])
    n_m, n_t = len(models_sorted), len(TRIGGER_KEYS)

    fired = np.array([[int(k in m["triggers"]) for k in TRIGGER_KEYS]
                       for m in models_sorted])

    fig, ax = plt.subplots(figsize=(9, 5.8))

    for mi, m in enumerate(models_sorted):
        color = REGIME_COLOR[m["regime"]]
        for ti in range(n_t):
            val  = fired[mi, ti]
            face = color + "CC" if val else LIGHT_GRAY
            edge = color         if val else MID_GRAY
            ax.add_patch(mpatches.FancyBboxPatch(
                (ti + 0.1, mi + 0.1), 0.8, 0.8,
                boxstyle="round,pad=0.05",
                facecolor=face, edgecolor=edge, linewidth=1.2,
            ))
            if val:
                ax.text(ti + 0.5, mi + 0.5, "✓", ha="center", va="center",
                        fontsize=13, color="white", fontweight="bold")

        # Model name
        ax.text(-0.15, mi + 0.58, m["name"],    ha="right", va="center", fontsize=9,  color=TEXT_DARK)
        ax.text(-0.15, mi + 0.20, f"[{m['backend']}]", ha="right", va="center", fontsize=7, color=TEXT_MID)
        # Regime badge
        ax.text(-2.05, mi + 0.5, f"→ {m['regime']}", ha="left", va="center",
                fontsize=8.5, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.25", fc=color + "20", ec=color, lw=0.9))

    for ti, label in enumerate(TRIGGER_LABELS):
        ax.text(ti + 0.5, n_m + 0.18, label, ha="center", va="bottom",
                fontsize=9, color=TEXT_MID, rotation=22)

    ax.set_xlim(-2.5, n_t)
    ax.set_ylim(-0.3, n_m + 0.9)
    ax.axis("off")

    legend_handles = [
        mpatches.Patch(facecolor=RETRY_C    + "CC", edgecolor=RETRY_C,    label="retry"),
        mpatches.Patch(facecolor=ESCALATE_C + "CC", edgecolor=ESCALATE_C, label="escalate"),
        mpatches.Patch(facecolor=ABORT_C    + "CC", edgecolor=ABORT_C,    label="abort"),
        mpatches.Patch(facecolor=LIGHT_GRAY,         edgecolor=MID_GRAY,   label="did not fire"),
    ]
    ax.legend(handles=legend_handles, loc="upper center",
              bbox_to_anchor=(0.55, -0.02), ncol=4, fontsize=8.5,
              frameon=True, framealpha=0.9)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure2_trigger_heatmap.png", **SAVE_KW)
    plt.show()

make_figure2()
"""))

# ── Figure 3 ──────────────────────────────────────────────────────────────────
cells.append(md("""\
## Figure 3 — Stress Timeline: Mistral-7B vs Claude Haiku 4.5

Both models produce **4.0 mean benchmark failures**. Mistral collapses at step 15
(latency cliff). Haiku completes all 22 steps but repeatedly crosses the
context-decay threshold. Same failure count; opposite intervention states.
"""))
cells.append(code("""\
def load_stress(run_dir):
    with open(run_dir / "stress.jsonl") as f:
        return [json.loads(l) for l in f]

MISTRAL_RUN = LOCAL_RUNS / "unified_weekend_baseline_mistral-7b-instruct-v03_t0p0_m192_s0"
HAIKU_RUN   = API_RUNS   / "unified_weekend_baseline_claude_haiku_45_t0p0_m192_s0"

LATENCY_THRESHOLD_MS = 7500

def make_figure3():
    mistral = load_stress(MISTRAL_RUN)
    haiku   = load_stress(HAIKU_RUN)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    def plot_panel(ax, data, title, color, regime, threshold_ms):
        steps   = [d["step"]       for d in data]
        latency = [d["latency_ms"] / 1000 for d in data]

        ax.plot(steps, latency, color=color, lw=2, zorder=3)
        ax.fill_between(steps, latency, alpha=0.12, color=color)

        for d in data:
            if d["is_failure"]:
                ax.scatter(d["step"], d["latency_ms"]/1000,
                           s=55, color=ABORT_C, zorder=5)

        thresh_s = threshold_ms / 1000
        ax.axhline(thresh_s, color=ABORT_C, lw=1.1, ls="--", alpha=0.6)
        ax.text(0.01, thresh_s + 0.1, "latency threshold", color=ABORT_C,
                fontsize=8, va="bottom", transform=ax.get_yaxis_transform())

        ax.set_title(title, fontsize=11, fontweight="bold", color=TEXT_DARK, pad=8)
        rc = REGIME_COLOR[regime]
        ax.text(0.97, 0.06, f"→ {regime}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=10, fontweight="bold", color=rc,
                bbox=dict(boxstyle="round,pad=0.3", fc=rc+"18", ec=rc, lw=1))
        ax.set_xlabel("Stress step (growing context)", fontsize=9.5, color=TEXT_MID)
        ax.set_ylabel("Latency (seconds)",             fontsize=9.5, color=TEXT_MID)
        ax.tick_params(colors=TEXT_MID)
        ax.spines["bottom"].set_color(MID_GRAY)
        ax.spines["left"].set_color(MID_GRAY)

    plot_panel(axes[0], mistral, "Mistral-7B  (local · MLX)",
               ABORT_C, "abort", LATENCY_THRESHOLD_MS)
    plot_panel(axes[1], haiku,   "Claude Haiku 4.5  (API · Anthropic)",
               ESCALATE_C, "escalate", LATENCY_THRESHOLD_MS)

    # Mistral: annotate the latency cliff
    cliff = next((d for d in mistral if d["latency_ms"] >= LATENCY_THRESHOLD_MS), mistral[-1])
    axes[0].annotate(
        f"latency cliff\\n(step {cliff['step']})",
        xy=(cliff["step"], cliff["latency_ms"]/1000),
        xytext=(cliff["step"] - 5, cliff["latency_ms"]/1000 + 1.4),
        fontsize=8.5, color=ABORT_C,
        arrowprops=dict(arrowstyle="->", color=ABORT_C, lw=1),
    )

    # Haiku: explain why escalate fires despite clean latency
    axes[1].text(0.04, 0.60,
        "Latency stays flat throughout.\\n"
        "ESCALATE fires because context_decay\\n"
        "triggers in all 6 runs: state integrity\\n"
        "breaks under accumulating context,\\n"
        "not under speed pressure.",
        transform=axes[1].transAxes,
        ha="left", va="center", fontsize=8, color=ESCALATE_C,
        bbox=dict(boxstyle="round,pad=0.4", fc=ESCALATE_C+"12", ec=ESCALATE_C, lw=0.8))

    fig.text(0.01, -0.02,
        "Both models: 4.0 mean benchmark failures. "
        "Red dots = steps where a failure condition triggered. "
        "Intervention state is determined by trigger pattern and stress outcome — not failure count alone.",
        fontsize=8, color=TEXT_MID)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure3_stress_timeline.png", **SAVE_KW)
    plt.show()

make_figure3()
"""))

# ── Figure 4 ──────────────────────────────────────────────────────────────────
cells.append(md("## Figure 4 — Failure Breakdown (7 models)"))
cells.append(code("""\
TOTAL_PROBES = 14

def make_figure4():
    models_sorted = sorted(all_models, key=lambda m: m["failures"])
    names  = [m["name"]         for m in models_sorted]
    rec    = [m["recoverable"]  for m in models_sorted]
    unrec  = [m["unrecoverable"]for m in models_sorted]
    colors = [REGIME_COLOR[m["regime"]] for m in models_sorted]

    fig, ax = plt.subplots(figsize=(11, 5.0))
    x, bar_w = np.arange(len(names)), 0.55

    ax.bar(x, rec, bar_w, color=[c+"70" for c in colors],
           edgecolor=colors, linewidth=1.1, label="recoverable")
    ax.bar(x, unrec, bar_w, bottom=rec, color=colors,
           edgecolor=[TEXT_DARK]*len(names), linewidth=0.6, label="unrecoverable")

    ax.axhline(TOTAL_PROBES, color=MID_GRAY, lw=1.2, ls="--")
    ax.text(len(names) - 0.5, TOTAL_PROBES + 0.3, f"total probes ({TOTAL_PROBES})",
            ha="right", va="bottom", fontsize=8.5, color=TEXT_MID)

    # Mistral / Haiku callout
    mi_i = next(i for i,m in enumerate(models_sorted) if m["name"] == "Mistral-7B")
    ha_i = next(i for i,m in enumerate(models_sorted) if "Haiku" in m["name"])
    tot_m = rec[mi_i] + unrec[mi_i]
    ax.annotate(
        "Same count as Haiku 4.5 —\\ncollapse under stress (step 15)\\nproduces ABORT, not ESCALATE",
        xy=(mi_i, tot_m + 0.2), xytext=(mi_i - 0.6, tot_m + 5.0),
        fontsize=8, color=ABORT_C, ha="center",
        arrowprops=dict(arrowstyle="->", color=ABORT_C, lw=1),
    )

    # Total labels and regime badges
    for i, (r, u, m) in enumerate(zip(rec, unrec, models_sorted)):
        ax.text(i, r+u+0.2, f"{r+u:.1f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=TEXT_DARK)
        color = REGIME_COLOR[m["regime"]]
        ax.text(i, -2.2, f"→ {m['regime']}", ha="center", va="top",
                fontsize=7.5, fontweight="bold", color=color,
                bbox=dict(boxstyle="round,pad=0.2", fc=color+"18", ec=color, lw=0.8))
        ax.text(i, -3.3, m["backend"], ha="center", va="top",
                fontsize=7, color=TEXT_MID)

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, color=TEXT_DARK)
    ax.tick_params(axis="x", which="both", length=0, pad=30)
    ax.set_ylabel("Mean probe failures (of 14)", fontsize=9.5, color=TEXT_MID)
    ax.set_ylim(-4.5, TOTAL_PROBES + 4)
    ax.tick_params(colors=TEXT_MID)
    ax.spines["bottom"].set_color(MID_GRAY)
    ax.spines["left"].set_color(MID_GRAY)

    legend_handles = [
        mpatches.Patch(facecolor=MID_GRAY+"70", edgecolor=TEXT_MID, label="recoverable"),
        mpatches.Patch(facecolor=TEXT_MID,       edgecolor=TEXT_DARK, label="unrecoverable"),
    ]
    ax.legend(handles=legend_handles, fontsize=8.5, loc="upper left", framealpha=0.9)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure4_failure_breakdown.png", **SAVE_KW)
    plt.show()

make_figure4()
"""))

# ── Figure 5 ──────────────────────────────────────────────────────────────────
cells.append(md("""\
## Figure 5 — Scaffold Path: Shared Battery, Model Exit Points

One row per model. All rows share the same staged track. Bars extend as far
as each model got. ABORT models hit a collapse marker at their exit step.
"""))
cells.append(code("""\
# Pre-stress is a thin visual band — all models pass it, nothing interesting happens there.
# The stress phase (steps 1–22) carries the narrative and dominates the x-axis.
PRE_W      = 1.2   # width of the pre-stress band in axis units (compressed)
MAX_STEPS  = 22
TRACK_TOTAL = PRE_W + MAX_STEPS   # ≈ 23.2

def exit_x(m):
    return PRE_W + m["steps"] if m["regime"] == "abort" else TRACK_TOTAL

def make_figure5():
    def sort_key(m):
        return (0, m["failures"]) if m["regime"] != "abort" else (1, -m["steps"])
    models_sorted = sorted(all_models, key=sort_key)

    ROW_H, BAR_H = 0.72, 0.40
    BAR_OFF = (ROW_H - BAR_H) / 2

    fig, ax = plt.subplots(figsize=(13, 5.2))
    n = len(models_sorted)

    # Pre-stress / stress phase divider
    ax.axvline(PRE_W, color="#ccccdd", lw=1.2, ls="--", zorder=1)

    # Light stress-phase grid
    for step in [5, 10, 15, 20]:
        ax.axvline(PRE_W + step, color="#eeeeee", lw=0.6, zorder=1)
    # Key collapse-gate reference lines
    for step in [2, 15, 22]:
        ax.axvline(PRE_W + step, color="#ccccdd", lw=1.0, ls="--", zorder=1)

    for i, m in enumerate(models_sorted):
        y     = i * ROW_H
        color = REGIME_COLOR[m["regime"]]
        bg    = REGIME_BG[m["regime"]]
        ex    = exit_x(m)

        # Zebra rows
        if i % 2 == 0:
            ax.axhspan(y, y + ROW_H, color="#f9f9fb", zorder=0)

        # Pre-stress band: neutral fill (all models pass)
        ax.barh(y + BAR_OFF, PRE_W, BAR_H, left=0, color="#e8e8f0", zorder=2)

        # Ghost stress track
        ax.barh(y + BAR_OFF, MAX_STEPS, BAR_H, left=PRE_W, color="#f3f3f5", zorder=2)

        # Completed stress bar
        stress_len = ex - PRE_W
        if stress_len > 0:
            ax.barh(y + BAR_OFF, stress_len, BAR_H, left=PRE_W,
                    color=bg, edgecolor=color, linewidth=0.9, zorder=3)

        # Model name (left)
        ax.text(-0.2, y + ROW_H/2 + 0.07, m["name"],
                ha="right", va="center", fontsize=9, fontweight="bold", color=TEXT_DARK)
        ax.text(-0.2, y + 0.07, f"[{m['backend']}]",
                ha="right", va="center", fontsize=7, color=TEXT_MID)

        # Exit marker and label
        if m["regime"] == "abort":
            ax.plot(ex, y + ROW_H/2, "X", ms=10, color=color,
                    markeredgecolor="white", markeredgewidth=1.5, zorder=5)
            ax.text(ex + 0.25, y + ROW_H/2 + 0.06,
                    f"ABORT  step {m['steps']}  ·  {m['failures']:.0f} fail",
                    ha="left", va="center", fontsize=8.5, color=color, fontweight="bold")
        else:
            ax.plot(TRACK_TOTAL, y + ROW_H/2, "|", ms=13, mew=2, color=color, zorder=5)
            ax.text(TRACK_TOTAL + 0.25, y + ROW_H/2 + 0.06,
                    f"{m['regime'].upper()}  ·  {m['failures']:.1f} fail",
                    ha="left", va="center", fontsize=8.5, color=color, fontweight="bold")

    # Header labels
    top = n * ROW_H + 0.05
    ax.text(PRE_W / 2, top + 0.22, "PRE-STRESS\\n(all pass)",
            ha="center", va="bottom", fontsize=7, color=TEXT_MID,
            fontweight="bold", linespacing=1.3)
    ax.text(PRE_W + MAX_STEPS / 2, top + 0.18, "STRESS PHASE  (steps 1 – 22)",
            ha="center", va="bottom", fontsize=8, color=TEXT_MID, fontweight="bold")

    # Step tick labels
    for step in [2, 5, 10, 15, 20, 22]:
        ax.text(PRE_W + step, top, str(step),
                ha="center", va="bottom", fontsize=7, color="#aaaaaa")

    ax.set_xlim(-3.2, TRACK_TOTAL + 5.0)
    ax.set_ylim(-0.4, n * ROW_H + 0.75)
    ax.axis("off")

    ax.text(PRE_W, -0.35,
        "◆  Mistral-7B and Claude Haiku 4.5 share the same mean benchmark failures (4.0). "
        "Haiku completes the full battery (step 22) → ESCALATE. "
        "Mistral collapses at step 15 → ABORT.",
        ha="left", va="top", fontsize=7.5, color=TEXT_MID)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure5_scaffold_path.png", **SAVE_KW)
    plt.show()

make_figure5()
"""))

# ── Figure 6 ──────────────────────────────────────────────────────────────────
cells.append(md("""\
## Figure 6 — Benchmark Failures vs Stress Resilience

**The key scatter.** X = mean benchmark contract failures. Y = stress phase steps
completed before exit. Each dot is a model; size encodes unrecoverable failures.

Mistral-7B and Claude Haiku 4.5 sit at the **same X** (4.0 failures) but at
different Y (step 15 vs step 22), producing opposite intervention states.
A scaffold that only counts failures cannot distinguish them.
"""))
cells.append(code("""\
def make_figure6():
    fig, ax = plt.subplots(figsize=(9, 6.5))

    DOT_SCALE = 130   # size for 1.0 unrecoverable failure

    # ── Marker shape encodes context_decay ────────────────────────────────────
    # Circle (o)  = context_decay did NOT fire  → output-bounded failures only
    # Diamond (D) = context_decay fired (6/6)   → state integrity also degrades
    # This is the visual key to understanding why GPT-4o mini is RETRY and Haiku is ESCALATE
    # despite both completing step 22 with similar failure counts.
    for m in all_models:
        color  = REGIME_COLOR[m["regime"]]
        marker = "D" if "context_decay" in m["triggers"] else "o"
        ax.scatter(m["failures"], m["steps"],
                   s=DOT_SCALE * max(m["unrecoverable"], 0.5),
                   marker=marker, color=color, alpha=0.85,
                   edgecolors="white", linewidths=1.2,
                   zorder=4)

    # ── Mistral / Haiku vertical bracket (same x, different y) ───────────────
    mistral = next(m for m in all_models if m["name"] == "Mistral-7B")
    haiku   = next(m for m in all_models if "Haiku" in m["name"])
    gpt4o   = next(m for m in all_models if "GPT"   in m["name"])

    y_lo = mistral["steps"] + 0.5
    y_hi = haiku["steps"]   - 0.5
    ax.plot([4.0, 4.0], [y_lo, y_hi], color="#999999", lw=1.2, ls="--", zorder=3)
    for y in [y_lo, y_hi]:
        ax.plot([3.82, 4.18], [y, y], color="#999999", lw=1.2, zorder=3)
    ax.text(4.35, (y_lo + y_hi) / 2,
            "same failure count (4.0)\\n"
            "7-step gap in stress resilience\\n"
            "→ opposite intervention states",
            ha="left", va="center", fontsize=8.5, color="#333333",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#cccccc", lw=0.8))

    # ── GPT-4o vs Haiku: explain the RETRY / ESCALATE split ──────────────────
    # Both sit at step 22; the difference is context_decay firing for Haiku.
    ax.annotate(
        "context_decay: ✗\\n→ RETRY",
        xy=(gpt4o["failures"], gpt4o["steps"]),
        xytext=(gpt4o["failures"] - 2.2, gpt4o["steps"] - 4.5),
        fontsize=8, color=RETRY_C, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=RETRY_C + "aa", lw=1.0),
    )
    ax.annotate(
        "context_decay: ✓ (6/6 runs)\\n→ ESCALATE",
        xy=(haiku["failures"], haiku["steps"]),
        xytext=(haiku["failures"] + 1.2, haiku["steps"] - 4.5),
        fontsize=8, color=ESCALATE_C, fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=ESCALATE_C + "aa", lw=1.0),
    )

    # ── Model name labels ─────────────────────────────────────────────────────
    offsets = {
        "GPT-4o mini":      (-0.5,  1.1),
        "Claude Haiku 4.5": ( 0.5,  1.1),
        "Phi-4-mini":       ( 0.5,  1.1),
        "Llama-3.1-8B":     ( 0.5,  1.1),
        "Mistral-7B":       (-0.5, -1.5),
        "Phi-3-mini":       (-0.5,  1.1),
        "SmolLM-1.7B":      ( 0.5,  1.1),
    }
    for m in all_models:
        color = REGIME_COLOR[m["regime"]]
        dx, dy = offsets.get(m["name"], (0.4, 0.7))
        ax.annotate(
            m["name"],
            xy=(m["failures"], m["steps"]),
            xytext=(m["failures"] + dx, m["steps"] + dy),
            fontsize=8.5, color=color, fontweight="bold",
            arrowprops=dict(arrowstyle="-", color=color + "70", lw=0.8)
                if (abs(dx) + abs(dy)) > 0.8 else None,
        )

    # ── Reference line ────────────────────────────────────────────────────────
    ax.axhline(22, color="#dddddd", lw=1.0, ls=":", zorder=1)
    ax.text(13.8, 22.4, "full battery (step 22)",
            ha="right", va="bottom", fontsize=8, color="#aaaaaa")

    # ── Axes ──────────────────────────────────────────────────────────────────
    ax.set_xlabel("Mean benchmark contract failures (per run)", fontsize=10.5, color=TEXT_MID)
    ax.set_ylabel("Stress phase: steps completed before exit",  fontsize=10.5, color=TEXT_MID)
    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-2, 26)
    ax.tick_params(colors=TEXT_MID)
    ax.spines["bottom"].set_color(MID_GRAY)
    ax.spines["left"].set_color(MID_GRAY)

    # ── Legend ────────────────────────────────────────────────────────────────
    state_handles = [
        mpatches.Patch(facecolor=RETRY_C,    edgecolor=RETRY_C,    label="RETRY"),
        mpatches.Patch(facecolor=ESCALATE_C, edgecolor=ESCALATE_C, label="ESCALATE"),
        mpatches.Patch(facecolor=ABORT_C,    edgecolor=ABORT_C,    label="ABORT"),
    ]
    shape_handles = [
        plt.scatter([], [], marker="o", color="#888888", s=60, label="context_decay: no"),
        plt.scatter([], [], marker="D", color="#888888", s=60, label="context_decay: yes (6/6 runs)"),
    ]
    size_handles = [
        plt.scatter([], [], s=DOT_SCALE*v, color="#888888", alpha=0.75, label=f"{v:.0f}")
        for v in [1, 2, 4, 6]
    ]
    leg1 = ax.legend(handles=state_handles, title="Intervention state",
                     loc="lower right", fontsize=9, title_fontsize=8.5)
    ax.add_artist(leg1)
    leg2 = ax.legend(handles=shape_handles, title="Marker shape",
                     loc="center right", fontsize=8.5, title_fontsize=8.5)
    ax.add_artist(leg2)
    ax.legend(handles=size_handles, title="Dot size = mean\\nunrecoverable failures",
              loc="upper left", fontsize=8.5, title_fontsize=8.5)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "figure6_failure_vs_resilience.png", **SAVE_KW)
    plt.show()

make_figure6()
"""))

# ── Run all ───────────────────────────────────────────────────────────────────
cells.append(md("## Run All Figures at Once"))
cells.append(code("""\
for fn in [make_figure1, make_figure2, make_figure3,
           make_figure4, make_figure5, make_figure6]:
    fn()
    plt.close("all")
print(f"All figures saved to {OUT_DIR}/")
"""))

nb.cells = cells

out = Path(__file__).parent / "paper_figures.ipynb"
with open(out, "w") as f:
    nbf.write(nb, f)
print(f"Written → {out}")
