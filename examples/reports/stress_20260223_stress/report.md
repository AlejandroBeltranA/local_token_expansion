# LTE Report

- Records: 3
- Models: 1
- Approx token counting present: yes

## Stress cliff (persistent failure)

- mock-model: cliff_reached=yes step=2 reasons=['rcs'] context_fraction=0.2910

## Per-model summary

| model | ER(mean) | LORR(mean) | RCS(mean) | VD(mean, paired) |
| --- | ---: | ---: | ---: | ---: |
| mock-model | 1.0168 | 0.3333 | 0.0000 | n/a |

## Per-suite breakdown

### stress — mock-model
- ER(mean): 1.0168
- RCS(mean): 0.0000

## Worst prompts (by metric)

- RCS=0.0000 model=mock-model suite=stress prompt_id=step_0000
- RCS=0.0000 model=mock-model suite=stress prompt_id=step_0001
- RCS=0.0000 model=mock-model suite=stress prompt_id=step_0002

## Notes

- VD is computed using `output_tokens` for paired `variant: concise|detailed` cases with the same `pair_id`.
- If any records use approximate token counting, treat ER/LORR/VD as approximate as well.
