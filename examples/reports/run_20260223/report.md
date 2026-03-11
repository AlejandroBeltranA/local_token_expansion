# LTE Report

- Records: 4
- Models: 1
- Approx token counting present: yes

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| mock-model | 1.1546 | 0.0000 | 0.0000 | 0.0000 |

## Per-suite breakdown

### core_conciseness — mock-model
- ER(mean): 1.5944
- RCS(mean): 0.0000

### structured_extraction — mock-model
- ER(mean): 0.7147
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.0000 model=mock-model suite=core_conciseness prompt_id=summarize_concise
- RCS=0.0000 model=mock-model suite=core_conciseness prompt_id=summarize_detailed
- RCS=0.0000 model=mock-model suite=structured_extraction prompt_id=extract_json
- RCS=0.0000 model=mock-model suite=structured_extraction prompt_id=extract_table

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
