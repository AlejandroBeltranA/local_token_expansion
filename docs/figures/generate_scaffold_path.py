#!/usr/bin/env python3
"""
Generate the LTE scaffold path diagram as an SVG.

Visual logic: one horizontal row per model. All rows share the same staged
track. A model's bar extends as far as it got before exiting. ABORT models
drop a collapse marker at their exit step; RETRY and ESCALATE models reach
the end of the track and are labelled there.

Usage (from repo root):
    python docs/figures/generate_scaffold_path.py

Custom paths:
    python docs/figures/generate_scaffold_path.py \
        --local  results/my_sweep/baseline_phase_summary.json \
        --api    results/my_api/baseline_phase_summary.json \
        --output docs/figures/scaffold_path_diagram.svg
"""

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DISPLAY_NAMES = {
    "GPT-4o mini":                     "GPT-4o mini",
    "Claude Haiku 4.5":                "Claude Haiku 4.5",
    "Mistral-7B-Instruct-v0.3":        "Mistral-7B",
    "Phi-4-mini-instruct-8bit":        "Phi-4-mini",
    "Meta-Llama-3.1-8B-Instruct-3bit": "Llama-3.1-8B",
    "Phi-3-mini-4k-instruct-4bit":     "Phi-3-mini",
    "SmolLM-1.7B-Instruct-4bit":       "SmolLM-1.7B",
}

BACKEND_LABELS = {
    "openai":    "API · OpenAI",
    "anthropic": "API · Anthropic",
    "mlx":       "local · MLX",
}

# Fallback collapse step for ABORT models where first_gated_failure_step_range
# is null (persistent failure from the outset — near_cap_pressure triggers).
FALLBACK_ABORT_STEP = 2

# Total stress-phase steps in the scaffold.
STRESS_STEPS = 22

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def detect_backend(model_name: str, default: str = "unknown") -> str:
    n = model_name.lower()
    if any(k in n for k in ("gpt", "openai", "o1", "o3")):
        return "openai"
    if any(k in n for k in ("claude", "haiku", "sonnet", "opus")):
        return "anthropic"
    if "gemini" in n:
        return "google"
    return default


def load_models(json_path: Path, backend: str = "auto") -> list:
    with open(json_path) as f:
        data = json.load(f)
    result = []
    for m in data["models"]:
        recommendation = max(m["recommendation_counts"], key=m["recommendation_counts"].get)
        triggers = set(m["trigger_fire_counts"].keys())
        r = m.get("first_gated_failure_step_range")
        collapse_step = r[0] if r else None
        resolved = detect_backend(m["model_name"], default="unknown") if backend == "auto" else backend
        result.append({
            "model_name":         m["model_name"],
            "display_name":       DISPLAY_NAMES.get(m["model_name"], m["model_name"]),
            "backend":            resolved,
            "backend_label":      BACKEND_LABELS.get(resolved, resolved),
            "recommendation":     recommendation,
            "triggers":           triggers,
            "benchmark_failures": m["benchmark_contract_failures_mean"],
            "unrecoverable":      m["unrecoverable_contract_failures_mean"],
            "collapse_step":      collapse_step,
        })
    return result

# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

class SVG:
    def __init__(self):
        self._p = []

    def raw(self, s):
        self._p.append(s)

    def rect(self, x, y, w, h, fill, stroke="none", rx=4, sw=1.0):
        self._p.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def text(self, x, y, s, size=11, fill="#333", anchor="middle", weight="normal"):
        self._p.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" '
            f'font-family="system-ui,-apple-system,sans-serif">{s}</text>'
        )

    def line(self, x1, y1, x2, y2, stroke="#ccc", sw=1.0, dash=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self._p.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>'
        )

    def circle(self, cx, cy, r, fill, stroke="none", sw=1.5):
        self._p.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )

    def build(self, w, h):
        return (
            f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}">\n'
            + "\n".join(self._p)
            + "\n</svg>"
        )

# ---------------------------------------------------------------------------
# Diagram
# ---------------------------------------------------------------------------

# Canvas
W  = 1000
# H computed from row count below

# Horizontal zones (x-coordinates)
X_NAME_END   = 155   # right edge of model-name column
X_TRACK_END  = 870   # right edge of track = stress step 22
X_LABEL_START= 880   # where post-track labels begin

# Pre-stress sub-stage boundaries (within X_NAME_END → X_STRESS_START)
X_STRESS_START = 440   # where the stress phase begins on the track
X_PROBE_END    = X_NAME_END + (X_STRESS_START - X_NAME_END) * 0.34   # ≈265
X_CONTRACT_END = X_NAME_END + (X_STRESS_START - X_NAME_END) * 0.67   # ≈352

# Row geometry
ROW_H  = 48
BAR_H  = 20
BAR_Y_OFFSET = 14    # bar top within the row

# Colors
C = {
    "bg":         "#ffffff",
    "track_bg":   "#f3f3f5",
    "grid":       "#e8e8ee",
    "grid_light": "#f0f0f5",
    "title":      "#1a1a2e",
    "axis":       "#999999",
    "sub":        "#777777",
    "dark":       "#111111",

    "retry_bar":  "#2d6a4f",
    "retry_bg":   "#c8ecd6",
    "retry_text": "#1b5236",

    "esc_bar":    "#b56a20",
    "esc_bg":     "#fad9b0",
    "esc_text":   "#7a4510",

    "abort_bar":  "#b03030",
    "abort_bg":   "#f5c4c4",
    "abort_text": "#7a1f1f",

    "name_bg":    "#f7f7fa",
}

OUTCOME_COLORS = {
    "retry":    ("retry_bar",  "retry_bg",  "retry_text"),
    "escalate": ("esc_bar",    "esc_bg",    "esc_text"),
    "abort":    ("abort_bar",  "abort_bg",  "abort_text"),
}


def stress_x(step: float) -> float:
    """Map stress step (0–STRESS_STEPS) to x-coordinate."""
    return X_STRESS_START + (step / STRESS_STEPS) * (X_TRACK_END - X_STRESS_START)


def exit_x(m: dict) -> float:
    if m["recommendation"] == "abort":
        step = m["collapse_step"] if m["collapse_step"] is not None else FALLBACK_ABORT_STEP
        return stress_x(step)
    return X_TRACK_END


def sort_key(m: dict):
    """Sort: survivors at top (by benchmark_failures), then aborts (by collapse step desc)."""
    if m["recommendation"] != "abort":
        step = STRESS_STEPS
    else:
        step = m["collapse_step"] if m["collapse_step"] is not None else FALLBACK_ABORT_STEP
    return (-step, m["benchmark_failures"])


def generate_svg(all_models: list) -> str:
    models = sorted(all_models, key=sort_key)
    n = len(models)

    HEADER_H = 75
    FOOTER_H = 30
    H = HEADER_H + n * ROW_H + FOOTER_H

    svg = SVG()
    svg.rect(0, 0, W, H, C["bg"])

    # ── Title ──────────────────────────────────────────────────────────────
    svg.text(W / 2, 22, "LTE Scaffold: All Models, Shared Battery, Different Exit Points",
             size=13, fill=C["title"], weight="600")

    # ── Stage header ───────────────────────────────────────────────────────
    HEADER_Y = 36  # top of stage label band

    # Pre-stress band label
    pre_cx = (X_NAME_END + X_STRESS_START) / 2
    svg.text(pre_cx, HEADER_Y + 10, "PRE-STRESS", size=7.5, fill=C["axis"], weight="700")

    # Stress band label
    stress_cx = (X_STRESS_START + X_TRACK_END) / 2
    svg.text(stress_cx, HEADER_Y + 10, "STRESS PHASE", size=7.5, fill=C["axis"], weight="700")

    # Sub-stage labels
    for x0, x1, label in [
        (X_NAME_END,    X_PROBE_END,    "PROBE"),
        (X_PROBE_END,   X_CONTRACT_END, "CONTRACT"),
        (X_CONTRACT_END,X_STRESS_START, "TRIGGER"),
    ]:
        svg.text((x0 + x1) / 2, HEADER_Y + 22, label, size=6.5, fill=C["sub"])

    # Stress step tick labels
    for step in [2, 5, 10, 15, 20, 22]:
        sx = stress_x(step)
        svg.text(sx, HEADER_Y + 22, str(step), size=6.5, fill=C["sub"])

    # Horizontal header separator
    svg.line(X_NAME_END, HEADER_H - 4, X_TRACK_END, HEADER_H - 4, stroke=C["grid"], sw=0.8)

    TRACK_TOP = HEADER_H
    TRACK_BOT = HEADER_H + n * ROW_H

    # ── Vertical grid lines ────────────────────────────────────────────────
    for x in [X_PROBE_END, X_CONTRACT_END, X_STRESS_START]:
        svg.line(x, TRACK_TOP, x, TRACK_BOT, stroke=C["grid"], sw=0.8)

    # Light ticks inside stress zone
    for step in [5, 10, 20]:
        svg.line(stress_x(step), TRACK_TOP, stress_x(step), TRACK_BOT,
                 stroke=C["grid_light"], sw=0.6)

    # Collapse-gate reference lines (dashed, named)
    for step, label in [(2, "step 2"), (15, "step 15"), (22, "step 22")]:
        sx = stress_x(step)
        svg.line(sx, TRACK_TOP - 4, sx, TRACK_BOT,
                 stroke="#ccccdd", sw=1.0, dash="3 3")

    # ── Model rows ─────────────────────────────────────────────────────────
    for i, m in enumerate(models):
        row_top = TRACK_TOP + i * ROW_H
        bar_top = row_top + BAR_Y_OFFSET
        bar_cx  = bar_top + BAR_H / 2

        bar_key, bg_key, text_key = OUTCOME_COLORS[m["recommendation"]]
        bar_col  = C[bar_key]
        bg_col   = C[bg_key]
        text_col = C[text_key]

        ex = exit_x(m)

        # Row zebra background
        if i % 2 == 0:
            svg.rect(X_NAME_END, row_top, X_TRACK_END - X_NAME_END, ROW_H,
                     "#f9f9fb", "none", rx=0)

        # Full grey track (ghost of what could have been)
        svg.rect(X_NAME_END, bar_top, X_TRACK_END - X_NAME_END, BAR_H,
                 C["track_bg"], "none", rx=3)

        # Completed bar — how far this model got
        bar_w = ex - X_NAME_END
        svg.rect(X_NAME_END, bar_top, bar_w, BAR_H, bg_col, bar_col, rx=3, sw=0.8)

        # ── Model name (left column) ──
        svg.text(X_NAME_END - 8, bar_cx - 5, m["display_name"],
                 size=9, fill=C["dark"], anchor="end", weight="600")
        svg.text(X_NAME_END - 8, bar_cx + 7, m["backend_label"],
                 size=7, fill=C["sub"], anchor="end")

        # ── Exit marker and label ──
        if m["recommendation"] == "abort":
            step = m["collapse_step"] if m["collapse_step"] is not None else FALLBACK_ABORT_STEP
            # Collapse marker: filled circle with ✕
            svg.circle(ex, bar_cx, 8, bar_col, "white", sw=1.5)
            svg.text(ex, bar_cx + 4, "✕", size=9, fill="white", weight="700")
            # Label in the blank portion of the track
            lx = ex + 12
            svg.text(lx, bar_cx - 4, "ABORT", size=8.5, fill=text_col, anchor="start", weight="700")
            svg.text(lx, bar_cx + 7, f"step {step}  ·  {m['benchmark_failures']} fail",
                     size=7, fill=C["sub"], anchor="start")
        else:
            state = m["recommendation"].upper()
            # End-of-track marker: small tick
            svg.line(X_TRACK_END, bar_top - 2, X_TRACK_END, bar_top + BAR_H + 2,
                     stroke=bar_col, sw=2)
            svg.text(X_LABEL_START, bar_cx - 4, state,
                     size=8.5, fill=text_col, anchor="start", weight="700")
            svg.text(X_LABEL_START, bar_cx + 7,
                     f"{m['benchmark_failures']} fail  ·  {m['unrecoverable']} unrec.",
                     size=7, fill=C["sub"], anchor="start")

    # ── Right border ───────────────────────────────────────────────────────
    svg.line(X_TRACK_END, TRACK_TOP, X_TRACK_END, TRACK_BOT, stroke=C["grid"], sw=1)

    # ── Footer note ────────────────────────────────────────────────────────
    svg.text(
        X_NAME_END, H - 10,
        "◆  Mistral-7B exits at step 15 with 4.0 mean failures — the same count as Claude Haiku 4.5, "
        "which completes the full battery (step 22).",
        size=7.5, fill=C["sub"], anchor="start"
    )

    return svg.build(W, H)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate LTE scaffold path diagram as SVG.")
    parser.add_argument("--local",  default="results/weekend_sweep_full/baseline_phase_summary.json")
    parser.add_argument("--api",    default="results/api_baseline_sweep/baseline_phase_summary.json")
    parser.add_argument("--output", default="docs/figures/scaffold_path_diagram.svg")
    args = parser.parse_args()

    all_models = []

    local_path = Path(args.local)
    if local_path.exists():
        print(f"Loading local models from {local_path}")
        all_models.extend(load_models(local_path, backend="mlx"))
    else:
        print(f"Warning: {local_path} not found — skipping.")

    if args.api:
        api_path = Path(args.api)
        if api_path.exists():
            print(f"Loading API models from {api_path}")
            all_models.extend(load_models(api_path, backend="auto"))
        else:
            print(f"Warning: {api_path} not found — skipping.")

    if not all_models:
        print("No models loaded. Check your JSON paths.")
        return

    svg = generate_svg(all_models)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg)
    print(f"Written → {out}  ({len(svg):,} chars)")


if __name__ == "__main__":
    main()
