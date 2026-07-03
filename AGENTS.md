# AGENTS.md — Local Token Expansion / TAIGR Paper Project

## Working conventions

**Always ask where to save outputs at the start of a session before creating any files.**
Do not assume the draft folder, the root, or any other location. Ask first.

## Project structure

```
local_token_expansion/
├── lte/                        # Core framework code
├── suites/                     # Probe suite YAML definitions
├── configs/                    # Run configurations
├── results/                    # Experimental results (weekend_sweep_full/ is the main sweep)
├── docs/
│   ├── whitepaper_draft.md     # Original LTE whitepaper (source material)
│   ├── figures/                # Paper figures (figure1–4)
│   └── ...
└── research/
    └── draft/
        ├── taigr_paper_v2.md   # Current paper draft (TAIGR @ ICML 2026)
        ├── literature_review.md # Verified literature review with summaries
        └── literature/         # Downloaded PDFs — read these, don't web-fetch
```

## Paper context

**Submission:** TAIGR @ ICML 2026 — Second Workshop on Technical AI Governance Research
**Deadline:** 24 April 2026, 23:59 AOE
**Track:** Full paper (8 pages) or tiny paper (2 pages)
**Review:** Double-blind — all author names and repo links must be anonymised

**Framework name:** Local Threshold Evaluation (LTE) — do not rename, repo references intact
**Previous name:** Local Token Expansion — may appear in code/configs, that's fine

## Citation rules

- Always verify citations against actual PDFs in `research/draft/literature/` before including
- Do not cite papers found only via web search without PDF confirmation
- Several TAIGR organising/advisory committee members are co-authors on key papers — cite precisely:
  - Casper et al. 2024 (Black-Box Audits): co-authors include Kolt, Wei, Bucknall
  - Kolt, Caputo et al. 2026 (Legal Alignment): co-authors include Reuel, Casper, Bommasani, Hammond, Wei
  - Hammond, Chan et al. 2025 (Multi-Agent Risks): co-author includes Reuel
  - Harack et al. 2025 (Verification for International AI Governance): co-authors include Reuel, Bucknall

## Voice

Alex's writing voice is documented in `alex_writing_voice.md` (uploads folder).
Key rules: British English, declarative opening sentences, no "furthermore/moreover/it is worth noting",
no AI tells ("robust", "shed light on", "underscore", "nuanced", "multifaceted").

## Key corrections already made

- Santoni de Sio co-author = Jeroen van den Hoven (not Di Nucci)
- Du et al. (2025) not "Hsieh et al." for arXiv:2510.05381
- Perez et al. 2023 (ACL Findings, model-written evals) not 2022 red-teaming paper
- "Wan et al. 2025" = 2025 Foundation Model Transparency Index (Alexander Wan first author) — real paper, not a honeypot
