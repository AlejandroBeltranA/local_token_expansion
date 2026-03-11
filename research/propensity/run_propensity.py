#!/usr/bin/env python3
"""
Run rolling prompt experiments against an MLX model and log each step.

This script is designed so a non‑technical reader can follow what happens:
1) Load a model and tokenizer.
2) Create a prompt for each step (either language‑specific or feature‑accretion).
3) Ask the model to respond.
4) Measure signals like repetition, novelty, truncation, and format adherence.
5) Stop when the model hits a defined “breaking” condition.
6) Write everything to a JSONL file for analysis.
"""
import argparse
import gc
import itertools
import json
import random
import re
import time
from pathlib import Path
from statistics import mean

# Simple string patterns that hint the model is refusing to answer.
REFUSAL_PATTERNS = [
    r"\bI\s*(?:can't|cannot|won't|will not)\b",
    r"\bI\s*do not\s*have the ability\b",
    r"\bI'm sorry\b",
    r"\bI cannot assist\b",
    r"\bAs an AI\b",
]
# Patterns that suggest the model is saying “I already answered this.”
ALREADY_ANSWERED_PATTERNS = [
    r"\bI (?:already|previously) (?:answered|covered|addressed)\b",
    r"\bAs (?:mentioned|stated) (?:earlier|before)\b",
    r"\bI (?:said|explained) (?:earlier|before)\b",
    r"\bThis is (?:similar|the same) as before\b",
    r"\bI'm repeating myself\b",
]
# Patterns that suggest the model is stalling or giving up.
STALL_PATTERNS = [
    r"\bI don't know\b",
    r"\bNot sure\b",
    r"\bNo further\b",
    r"\bN/A\b",
]


def load_config(path: Path) -> dict:
    """Load experiment settings from a JSON config file."""
    return json.loads(path.read_text())


def detect_max_context(model_path: Path, fallback: int = 4096) -> int:
    """Read the model config to discover its maximum context length."""
    cfg_path = model_path / "config.json"
    if not cfg_path.exists():
        return fallback
    try:
        cfg = json.loads(cfg_path.read_text())
    except json.JSONDecodeError:
        return fallback
    for key in ("max_position_embeddings", "max_seq_len", "n_ctx", "context_length"):
        value = cfg.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return fallback


def ensure_dir(path: Path) -> None:
    """Create output directories if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)


def normalize_prompt(prompt: str) -> str:
    """Normalize spacing so prompts are consistent."""
    return " ".join(prompt.strip().split())


def compute_ngrams(text: str, n: int = 3) -> list[tuple[str, ...]]:
    """Return n‑grams for repetition/similarity scoring."""
    tokens = text.split()
    if len(tokens) < n:
        return []
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def repetition_rate(text: str, n: int = 3) -> float:
    """Compute how repetitive a response is (higher = more repetition)."""
    ngrams = compute_ngrams(text, n=n)
    if not ngrams:
        return 0.0
    unique = len(set(ngrams))
    return 1.0 - (unique / len(ngrams))


def token_novelty_score(text: str, seen_tokens: set[str]) -> tuple[float, set[str]]:
    """
    Measure how much of this response is *new* compared to all previous text.
    Returns (novelty_score, updated_seen_tokens).
    """
    tokens = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", text)]
    if not tokens:
        return 0.0, seen_tokens
    new_tokens = [t for t in tokens if t not in seen_tokens]
    novelty = len(new_tokens) / len(tokens)
    return novelty, seen_tokens | set(tokens)


def summarize_features(features: list[str], max_chars: int) -> str:
    """Compact the feature ledger into a short summary for the prompt."""
    summary = "; ".join(features)
    if max_chars <= 0 or len(summary) <= max_chars:
        return summary
    return summary[-max_chars:]


def extract_feature_name(text: str) -> str | None:
    """Extract the 'Feature:' name from the response (if present)."""
    match = re.search(r"^\s*Feature:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def format_adherence(text: str) -> dict:
    """Check whether required sections are present in the response."""
    required = ["Feature:", "Motivation:", "Behavior change:", "Patch:", "Test:"]
    missing = [label for label in required if label.lower() not in text.lower()]
    return {
        "format_missing": missing,
        "format_ok": len(missing) == 0,
    }

def levenshtein(a: str, b: str) -> int:
    """Compute edit distance between two strings."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            ins = curr[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            curr.append(min(ins, delete, sub))
        prev = curr
    return prev[-1]


def extract_memory_answer(text: str, tag: str) -> str | None:
    """Extract the model's memory answer from common tag patterns."""
    patterns = [
        rf"{re.escape(tag)}\\s*:\\s*([A-Za-z#+ -]+)",
        r"Language\\s*:\\s*([A-Za-z#+ -]+)",
        r"Previous\\s+language\\s*(?:was|:)\\s*([A-Za-z#+ -]+)",
        r"Previously\\s+coding\\s+in\\s*([A-Za-z#+ -]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            answer = match.group(1).strip()
            return re.sub(r"[^\\w#+\\- ]+", "", answer).strip()
    # Fallback: check first line only to avoid grabbing unrelated text
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    match = re.search(r"Language\\s*:\\s*([A-Za-z#+ -]+)", first_line, re.IGNORECASE)
    if match:
        answer = match.group(1).strip()
        return re.sub(r"[^\\w#+\\- ]+", "", answer).strip()
    return None

def detect_language(text: str) -> str | None:
    """Heuristic language detection from code blocks + keywords."""
    code_blocks = re.findall(r"```([a-zA-Z#+\\-]+)?\n(.*?)```", text, re.DOTALL)
    # Prefer first labeled non-diff block
    for label, code in code_blocks:
        label = (label or "").strip().lower()
        if label and label != "diff":
            return label
    # If only diff blocks exist, ignore labels and use content
    code = code_blocks[0][1] if code_blocks else text

    probes = [
        ("python", [r"\\bdef\\b", r"\\bimport\\b", r"\\bNone\\b", r"\\bself\\b"]),
        ("javascript", [r"\\bfunction\\b", r"\\bconst\\b", r"\\blet\\b", r"\\b=>\\b"]),
        ("typescript", [r"\\binterface\\b", r"\\btype\\b", r"\\bimplements\\b", r":\\s*\\w+", r"\\breadonly\\b"]),
        ("go", [r"\\bfunc\\b", r"\\bpackage\\b", r"\\bdefer\\b", r"\\berr\\b"]),
        ("rust", [r"\\bfn\\b", r"\\blet\\s+mut\\b", r"\\bimpl\\b", r"\\bcrate\\b"]),
        ("java", [r"\\bpublic class\\b", r"\\bstatic void\\b", r"\\bSystem\\.out\\b"]),
        ("c#", [r"\\bnamespace\\b", r"\\busing\\b", r"\\bpublic class\\b", r"\\basync\\b"]),
        ("c++", [r"\\b#include\\b", r"\\bstd::\\b", r"\\bcout\\b"]),
        ("ruby", [r"\\bdef\\b", r"\\bend\\b", r"\\bclass\\b", r":\\w+"]),
        ("php", [r"<\\?php", r"\\becho\\b", r"\\b\\$[a-zA-Z_]+"]),
        ("swift", [r"\\bimport\\b", r"\\bfunc\\b", r"\\blet\\b", r"\\bvar\\b"]),
        ("kotlin", [r"\\bfun\\b", r"\\bval\\b", r"\\bvar\\b", r"\\bdata class\\b"]),
        ("elixir", [r"\\bdefmodule\\b", r"\\bdef\\b", r"\\bdo\\b", r"\\bend\\b"]),
        ("lua", [r"\\blocal\\b", r"\\bfunction\\b", r"\\bend\\b"]),
    ]
    scores = {}
    for lang, patterns in probes:
        scores[lang] = sum(1 for p in patterns if re.search(p, code))
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else None


def jaccard_similarity(a: list[tuple[str, ...]], b: list[tuple[str, ...]]) -> float:
    """Compare two responses by overlapping n‑grams (0 = different, 1 = identical)."""
    if not a or not b:
        return 0.0
    set_a = set(a)
    set_b = set(b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def has_refusal(text: str) -> bool:
    """Detect refusal language."""
    for pattern in REFUSAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def has_already_answered(text: str) -> bool:
    """Detect 'already answered' language."""
    for pattern in ALREADY_ANSWERED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def has_stall(text: str, min_tokens: int = 20) -> bool:
    """Detect unusually short or stalled answers."""
    token_count = len(text.split())
    if token_count > 0 and token_count < min_tokens:
        return True
    for pattern in STALL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def build_prompt(tokenizer, conversation):
    """Convert a conversation into a model‑ready prompt string."""
    if hasattr(tokenizer, "apply_chat_template"):
        try:
            prompt = tokenizer.apply_chat_template(conversation=conversation, add_generation_prompt=True)
        except TypeError:
            prompt = tokenizer.apply_chat_template(conversation, add_generation_prompt=True)
    else:
        # Fallback: simple concatenation if no chat template is available
        parts = []
        for turn in conversation:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            parts.append(f"{role}: {content}")
        parts.append("assistant:")
        prompt = "\n".join(parts)

    if not isinstance(prompt, str):
        prompt = tokenizer.decode(prompt)

    return prompt


def generate_with_fallback(generate_fn, base_kwargs, sampling_kwargs):
    """Call MLX generate, dropping unsupported args if needed."""
    """Call generate() while stripping unsupported kwargs from older mlx-lm versions."""
    kwargs = dict(base_kwargs)
    kwargs.update(sampling_kwargs)

    while True:
        try:
            return generate_fn(**kwargs)
        except TypeError as exc:
            msg = str(exc)
            match = re.search(r"unexpected keyword argument '([^']+)'", msg)
            if not match:
                raise
            bad_key = match.group(1)
            if bad_key == "temperature" and "temp" not in kwargs:
                kwargs.pop("temperature", None)
                kwargs["temp"] = sampling_kwargs.get("temperature")
                continue
            if bad_key in kwargs:
                kwargs.pop(bad_key, None)
                continue
            raise


def main() -> None:
    """
    Main experiment loop:
    - Load config
    - Iterate over sampling parameter combos
    - Generate responses step‑by‑step
    - Log metrics and stop on breakdown conditions
    """
    parser = argparse.ArgumentParser(description="Run rolling-chat propensity experiments with MLX models.")
    parser.add_argument("--config", default="research/propensity/local_llm_propensity.json", help="Path to config JSON")
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_config(config_path)

    model_path = Path(cfg["model_path"]).expanduser()
    if not model_path.is_absolute():
        model_path = (Path.cwd() / model_path).resolve()

    output_dir = Path(cfg["output_dir"]).expanduser()
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()
    ensure_dir(output_dir)

    run_name = cfg.get("run_name", model_path.name)
    output_file = output_dir / f"{run_name}.jsonl"

    max_context = detect_max_context(model_path)
    max_gen_tokens = int(cfg.get("max_gen_tokens", 512))
    safety_margin = int(cfg.get("safety_margin_tokens", 64))
    max_steps_per_run = int(cfg.get("max_steps_per_run", 0))
    repetition_rate_threshold = float(cfg.get("repetition_rate_threshold", 0.0))
    repetition_consecutive = int(cfg.get("repetition_consecutive", 0))
    rolling_window = int(cfg.get("rolling_window", 5))
    spike_threshold = float(cfg.get("spike_threshold", 2.0))
    stall_min_tokens = int(cfg.get("stall_min_tokens", 20))
    breakdown_rep_threshold = float(cfg.get("breakdown_repetition_threshold", 0.2))
    breakdown_sim_threshold = float(cfg.get("breakdown_similarity_threshold", 0.6))
    breakdown_score_threshold = float(cfg.get("breakdown_score_threshold", 1.5))
    mode = cfg.get("mode", "prompt_repeat")
    feature_categories = cfg.get("feature_categories", [])
    spec_summary_max_chars = int(cfg.get("spec_summary_max_chars", 800))
    novelty_threshold = float(cfg.get("novelty_threshold", 0.0))
    novelty_consecutive = int(cfg.get("novelty_consecutive", 0))
    format_adherence_required = bool(cfg.get("format_adherence_required", False))
    memory_check = bool(cfg.get("memory_check", False))
    memory_tag = cfg.get("memory_tag", "MemoryCheck")
    memory_question = cfg.get(
        "memory_question",
        "MemoryCheck: What language were we coding in immediately before this step?",
    )
    memory_response_instruction = cfg.get(
        "memory_response_instruction",
        "",
    )
    memory_probe_min_steps = int(cfg.get("memory_probe_min_steps", 1))
    memory_probe_max_steps = int(cfg.get("memory_probe_max_steps", 5))
    latency_ratio_threshold = float(cfg.get("latency_ratio_threshold", 0.0))
    latency_window = int(cfg.get("latency_window", 3))
    latency_consecutive = int(cfg.get("latency_consecutive", 0))
    eta_log_every_steps = int(cfg.get("eta_log_every_steps", 10))

    prompt_template = cfg["prompt_template"]
    repeat_prompt_template = cfg.get("repeat_prompt_template", "")
    prev_response_max_chars = int(cfg.get("prev_response_max_chars", 0))
    languages = list(cfg["languages"])

    temperatures = list(cfg.get("temperatures", [0.7]))
    top_p_values = list(cfg.get("top_p_values", [0.9]))
    top_k_values = list(cfg.get("top_k_values", [0]))
    repetition_penalties = list(cfg.get("repetition_penalties", [1.0]))
    runs_per_combo = int(cfg.get("runs_per_combo", 1))
    max_runs = int(cfg.get("max_runs", 100))

    rng = random.Random(cfg.get("seed", 0))

    try:
        from mlx_lm import generate, load
    except Exception as exc:
        raise SystemExit(f"Failed to import mlx_lm: {exc}")

    model, tokenizer = load(path_or_hf_repo=str(model_path))

    combos = list(itertools.product(temperatures, top_p_values, top_k_values, repetition_penalties))
    total_runs = min(max_runs, len(combos) * runs_per_combo)

    run_counter = 0
    combo_counter = 0

    with output_file.open("w") as out:
        for combo in combos:
            temp, top_p, top_k, rep_penalty = combo
            for run_index in range(runs_per_combo):
                if run_counter >= total_runs:
                    break

                run_id = f"{run_name}_run_{run_counter:04d}"
                combo_id = f"combo_{combo_counter:03d}"

                conversation = []
                response_history = []
                response_token_history = []
                last_response_by_language = {}
                feature_ledger = []
                seen_tokens = set()
                novelty_streak = 0
                last_language = None
                latency_streak = 0
                duration_history = []
                next_memory_probe = rng.randint(memory_probe_min_steps, memory_probe_max_steps)
                language_pool = languages[:]
                rng.shuffle(language_pool)
                language_cursor = 0

                step = 0
                repetition_streak = 0
                run_start = time.time()
                stop_reason = "completed"
                error_message = None

                while True:
                    if language_cursor >= len(language_pool):
                        language_pool = languages[:]
                        rng.shuffle(language_pool)
                        language_cursor = 0

                    language = language_pool[language_cursor]
                    language_cursor += 1

                    prompt_type = "base"
                    if mode == "feature_accretion":
                        try:
                            prompt = prompt_template.format(language=language)
                        except KeyError:
                            prompt = prompt_template
                        prompt_type = "feature_delta"
                    else:
                        if repeat_prompt_template and language in last_response_by_language:
                            prev_lang_response = last_response_by_language.get(language, "")
                            if prev_response_max_chars > 0:
                                prev_lang_response = prev_lang_response[-prev_response_max_chars:]
                            prompt = repeat_prompt_template.format(
                                language=language,
                                prev_language_response=prev_lang_response,
                            )
                            prompt_type = "repeat"
                        else:
                            prompt = prompt_template.format(language=language)
                    prompt = normalize_prompt(prompt)
                    memory_probe_used = False
                    if memory_check and step == next_memory_probe:
                        memory_block = memory_question
                        if memory_response_instruction:
                            memory_block = f"{memory_block}\n{memory_response_instruction}"
                        prompt = (
                            f"{memory_block}\n"
                            "Answer on the first line with: Language: <language>. Then continue with the feature delta format.\n\n"
                            f"{prompt}"
                        )
                        memory_probe_used = True
                        next_memory_probe = step + rng.randint(memory_probe_min_steps, memory_probe_max_steps)

                    conversation.append({"role": "user", "content": prompt})
                    prompt_text = build_prompt(tokenizer, conversation)
                    prompt_tokens = len(tokenizer.encode(prompt_text))

                    budget = max_context - prompt_tokens - safety_margin
                    if budget <= 0:
                        stop_reason = "context_budget_exhausted"
                        conversation.pop()
                        break

                    step_max_tokens = min(max_gen_tokens, budget)

                    start = time.time()
                    try:
                        base_kwargs = {
                            "model": model,
                            "tokenizer": tokenizer,
                            "prompt": prompt_text,
                            "max_tokens": step_max_tokens,
                            "verbose": False,
                        }
                        sampling_kwargs = {
                            "temperature": temp,
                            "top_p": top_p,
                            "top_k": top_k,
                            "repetition_penalty": rep_penalty,
                        }
                        response = generate_with_fallback(generate, base_kwargs, sampling_kwargs)
                    except Exception as exc:
                        stop_reason = "generation_error"
                        error_message = str(exc)
                        conversation.pop()
                        break
                    duration = time.time() - start
                    duration_history.append(duration)

                    if isinstance(response, tuple):
                        response = response[0]
                    response = str(response).strip()

                    conversation.append({"role": "assistant", "content": response})
                    if mode != "feature_accretion":
                        last_response_by_language[language] = response

                    response_tokens = len(tokenizer.encode(response)) if response else 0
                    response_history.append(response)
                    response_token_history.append(response_tokens)

                    prev_response = response_history[-2] if len(response_history) > 1 else ""
                    current_ngrams = compute_ngrams(response)
                    prev_ngrams = compute_ngrams(prev_response)

                    if len(response_token_history) > 1:
                        window = response_token_history[-rolling_window - 1:-1]
                        avg_recent = mean(window) if window else response_token_history[-2]
                    else:
                        avg_recent = response_tokens
                    spike_ratio = (response_tokens / avg_recent) if avg_recent else 0.0
                    spike_flag = spike_ratio >= spike_threshold if avg_recent else False

                    rep_rate = repetition_rate(response)
                    novelty_score, seen_tokens = token_novelty_score(response, seen_tokens)
                    feature_name = extract_feature_name(response) if mode == "feature_accretion" else None
                    format_status = format_adherence(response) if mode == "feature_accretion" else {"format_ok": True, "format_missing": []}
                    if feature_name:
                        feature_ledger.append(feature_name)

                    memory_expected = last_language
                    memory_answer = extract_memory_answer(response, memory_tag) if memory_check else None
                    memory_match = None
                    memory_distance = None
                    if memory_check and memory_expected and memory_probe_used:
                        answer_norm = (memory_answer or "").strip().lower()
                        expected_norm = memory_expected.strip().lower()
                        if answer_norm:
                            memory_match = 1 if answer_norm == expected_norm else 0
                            memory_distance = levenshtein(answer_norm, expected_norm)
                        else:
                            memory_match = None
                            memory_distance = None
                    if repetition_rate_threshold > 0 and rep_rate >= repetition_rate_threshold:
                        repetition_streak += 1
                    else:
                        repetition_streak = 0

                    already_answered = has_already_answered(response)
                    stalled = has_stall(response, min_tokens=stall_min_tokens)
                    refused = has_refusal(response)
                    similarity_to_prev = jaccard_similarity(current_ngrams, prev_ngrams)
                    hit_max = response_tokens >= step_max_tokens if step_max_tokens else False

                    breakdown_score = 0.0
                    breakdown_score += 1.0 if refused else 0.0
                    breakdown_score += 1.0 if already_answered else 0.0
                    breakdown_score += 1.0 if stalled else 0.0
                    breakdown_score += 0.5 if hit_max else 0.0
                    breakdown_score += 0.5 if rep_rate >= breakdown_rep_threshold else 0.0
                    breakdown_score += 0.5 if similarity_to_prev >= breakdown_sim_threshold else 0.0
                    breakdown_flag = breakdown_score >= breakdown_score_threshold

                    record = {
                        "record_type": "prompt_response",
                        "run_id": run_id,
                        "combo_id": combo_id,
                        "step": step,
                        "prompt_type": prompt_type,
                        "language": language,
                        "mode": mode,
                        "prompt": prompt,
                        "response": response,
                        "prompt_tokens": prompt_tokens,
                        "response_tokens": response_tokens,
                        "total_tokens": prompt_tokens + response_tokens,
                        "max_context": max_context,
                        "max_gen_tokens": step_max_tokens,
                        "temperature": temp,
                        "top_p": top_p,
                        "top_k": top_k,
                        "repetition_penalty": rep_penalty,
                        "duration_sec": round(duration, 4),
                        "repetition_rate": round(rep_rate, 4),
                        "similarity_to_prev": round(similarity_to_prev, 4),
                        "refusal_flag": refused,
                        "already_answered_flag": already_answered,
                        "stall_flag": stalled,
                        "spike_ratio": round(spike_ratio, 4),
                        "spike_flag": spike_flag,
                        "hit_max_gen_tokens": hit_max,
                        "novelty_score": round(novelty_score, 4),
                        "feature_name": feature_name,
                        "feature_ledger_count": len(feature_ledger),
                        "format_ok": format_status["format_ok"],
                        "format_missing": format_status["format_missing"],
                        "memory_expected": memory_expected,
                        "memory_answer": memory_answer,
                        "memory_match": memory_match,
                        "memory_distance": memory_distance,
                        "memory_probe_used": memory_probe_used,
                        "detected_language": None,
                        "language_drift": None,
                        "memory_correct": memory_match,
                        "memory_contamination": None,
                        "breakdown_score": round(breakdown_score, 2),
                        "breakdown_flag": breakdown_flag,
                    }

                    detected = detect_language(response)
                    record["detected_language"] = detected
                    if detected:
                        record["language_drift"] = 1 if detected != language.strip().lower() else 0
                        if memory_expected:
                            record["memory_contamination"] = 1 if detected == memory_expected.strip().lower() and detected != language.strip().lower() else 0

                    out.write(json.dumps(record) + "\n")
                    out.flush()

                    step += 1

                    if max_steps_per_run and eta_log_every_steps > 0 and step % eta_log_every_steps == 0:
                        avg_step_time = sum(duration_history) / len(duration_history)
                        remaining_in_run = max_steps_per_run - step
                        remaining_runs = total_runs - run_counter - 1
                        total_remaining_steps = remaining_in_run + max(0, remaining_runs) * max_steps_per_run
                        eta_minutes = (avg_step_time * total_remaining_steps) / 60.0
                        print(
                            f"ETA for model '{run_name}': ~{eta_minutes:.1f} min remaining "
                            f"({total_remaining_steps} steps)."
                        )

                    if max_steps_per_run and step >= max_steps_per_run:
                        stop_reason = "max_steps_reached"
                        break

                    if repetition_consecutive and repetition_streak >= repetition_consecutive:
                        stop_reason = "repetition_threshold_reached"
                        break

                    if novelty_threshold > 0:
                        if novelty_score < novelty_threshold:
                            novelty_streak += 1
                        else:
                            novelty_streak = 0
                        if novelty_consecutive and novelty_streak >= novelty_consecutive:
                            stop_reason = "novelty_threshold_reached"
                            break

                    if format_adherence_required and not format_status["format_ok"]:
                        stop_reason = "format_adherence_failed"
                        break

                    if latency_ratio_threshold > 0 and len(duration_history) > 1:
                        recent = duration_history[-(latency_window + 1):-1] if latency_window > 0 else duration_history[:-1]
                        baseline = sum(recent) / len(recent) if recent else None
                        if baseline and duration >= latency_ratio_threshold * baseline:
                            latency_streak += 1
                        else:
                            latency_streak = 0
                        if latency_consecutive and latency_streak >= latency_consecutive:
                            stop_reason = "latency_threshold_reached"
                            break

                    last_language = language

                run_duration = time.time() - run_start
                summary = {
                    "record_type": "run_summary",
                    "run_id": run_id,
                    "combo_id": combo_id,
                    "steps": step,
                    "temperature": temp,
                    "top_p": top_p,
                    "top_k": top_k,
                    "repetition_penalty": rep_penalty,
                    "stop_reason": stop_reason,
                    "error_message": error_message,
                    "duration_sec": round(run_duration, 4),
                }
                out.write(json.dumps(summary) + "\n")
                out.flush()

                run_counter += 1
                combo_counter += 1
                gc.collect()

            if run_counter >= total_runs:
                break

    print(f"Wrote results to {output_file}")


if __name__ == "__main__":
    main()
