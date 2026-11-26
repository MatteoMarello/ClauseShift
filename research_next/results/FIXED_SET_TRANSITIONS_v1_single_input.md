Fixed item set: 175 decided, well-posed flip-operator test items (25 per operator, no cross-reference), 641 sentence removals.

| System | Obligation removed → insufficient | Decisive removed → expected change | Non-decisive removed → kept | hit@1 (same items) |
|---|---|---|---|---|
| lazy_reader | 1.000 (n=175) | 1.000 (n=49) | 0.715 (n=417) | 1.000 |
| ft_deberta-v3-xsmall_paired_s0 | 0.766 (n=175) | 0.796 (n=49) | 0.683 (n=417) | 0.931 |
| ft_deberta-v3-xsmall_unpaired_s0 | 0.823 (n=175) | 0.694 (n=49) | 0.662 (n=417) | 0.931 |
| ft_nli-deberta-v3-xsmall_paired_s0 | 0.989 (n=175) | 0.857 (n=49) | 0.849 (n=417) | 1.000 |
| ft_nli-deberta-v3-xsmall_unpaired_s0 | 0.971 (n=175) | 0.898 (n=49) | 0.851 (n=417) | 1.000 |
| zeroshot_nli-deberta-v3-base | 0.811 (n=175) | 0.816 (n=49) | 0.674 (n=417) | 0.903 |
| zeroshot_DeBERTa-v3-base-mnli-fever-anli | 0.903 (n=175) | 0.816 (n=49) | 0.695 (n=417) | 0.966 |
