Fixed item set: 175 decided, well-posed flip-operator test items (25 per operator, no cross-reference), 641 sentence removals. Cells: v2 joint transition accuracy (correct on the full header-free document AND on the shortened one); in brackets v1 single-input agreement (shortened document only).

| System | Full-doc acc. | Obligation removed → insufficient | Decisive removed → expected change | Non-decisive removed → kept | hit@1 |
|---|---|---|---|---|---|
| lazy_reader | 0.720 | 0.720 (1.000; n=175) | 0.000 (1.000; n=49) | 0.715 (0.715; n=417) | 1.000 |
| ft_deberta-v3-xsmall_paired_s0 | 0.680 | 0.554 (0.766; n=175) | 0.388 (0.796; n=49) | 0.571 (0.683; n=417) | 0.931 |
| ft_deberta-v3-xsmall_unpaired_s0 | 0.640 | 0.549 (0.823; n=175) | 0.327 (0.694; n=49) | 0.544 (0.662; n=417) | 0.931 |
| ft_nli-deberta-v3-xsmall_paired_s0 | 0.897 | 0.886 (0.989; n=175) | 0.776 (0.857; n=49) | 0.803 (0.849; n=417) | 1.000 |
| ft_nli-deberta-v3-xsmall_unpaired_s0 | 0.851 | 0.823 (0.971; n=175) | 0.653 (0.898; n=49) | 0.787 (0.851; n=417) | 1.000 |
| zeroshot_nli-deberta-v3-base | 0.640 | 0.480 (0.811; n=175) | 0.020 (0.816; n=49) | 0.619 (0.674; n=417) | 0.903 |
| zeroshot_DeBERTa-v3-base-mnli-fever-anli | 0.703 | 0.634 (0.903; n=175) | 0.224 (0.816; n=49) | 0.659 (0.695; n=417) | 0.966 |
