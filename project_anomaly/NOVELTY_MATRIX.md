# Novelty matrix

Categories: **new result** (a claim we believe is not in the literature *and* is supported by our data);
**new method/algorithm**; **transfer** (a known method applied to a new setting); **empirical finding** (an
observation, possibly known in kind); **known** (already in the literature; we only reproduce it); **rejected**.
"Checked" lists what was actually searched in this session; a search that finds nothing is weak evidence of novelty.

| # | Item | Our evidence | Closest work | Category | Novelty claim we are willing to make |
|---|---|---|---|---|---|
| 1 | "Copy is not compare": boundary errors caused by string identity (C1) | Falsified (Pilot 1) | — | **rejected** | None |
| 2 | Psychometric curves of condition reading (P_sat vs signed distance) | Pilot 1b, 4 models, 30 base cases per cell | Shah et al., Findings ACL 2023 (distance/size/ratio effects in LLM number comparison); Cacioli, arXiv 2603.20642 (2026, Weber's law in transformers; preprint, seen only via abstract); Thukral et al. 2021 (temporal NLI probes); LoNLI (2021) | **transfer** | Applying a psychometric function to *rule application in NLI*, with the decisive condition held fixed and the value moved, as a diagnostic. Modest. |
| 3 | Non-monotone curves at surface-feature disagreements (leading digit, month-day) | Pilot 1b (probe data); held-out test: H_lex not supported, H_md fails the run-consistency criterion | "Date Fragments" (arXiv 2505.16088, date tokenisation); general reports of digit-string comparison errors | **empirical finding** (weak) | None beyond "observed in these models"; known in kind. |
| 4 | Year blindness acquired from date-edit training (A12) | Post hoc on stored test predictions: 6/6 runs with date edits ≤ 0.51 vs 3/3 without = 1.00 on 35 items | Joshi & He, ACL 2022 (counterfactual edits leave unperturbed robust features under-learned) | **empirical finding; candidate new result** | Not yet. If confirmed by the training experiment, a concrete, mechanistically specific instance of the Joshi & He mechanism inside a minimal-pair benchmark: the generator's edit distribution decides which sub-field of a value the model learns to compare. Searched: "date comparison ignore year", "month day heuristic" — nothing specific found. |
| 5 | Negation symmetry consistency of NLI models | Pilot 2 | BECEL (Jang et al., COLING 2022; negational consistency); Asai & Hajishirzi 2020 | **known** | None |
| 6 | Symmetrised decoding p(y\|x)·p(σy\|νx) | Gains +0.008 to +0.029 | Test-time augmentation; consistency correction (e.g. ConCoRD, 2022) | **known in kind** | None |
| 7 | Proposition 4 (no gain on consistent items; \|gain\| ≤ 1 − consistency) | Proof + exact check | Elementary; likely folklore | **known in kind** | Stated for completeness only |
| 8 | Error recurrence under the symmetry falls with accuracy (A14) | 6 models, descriptive | Not specifically searched | **empirical finding** | None until replicated on more models |
| 9 | Single-input evidence criteria reward ignoring the deleted clause (Prop. 1–2) | Proof; v1/v2 metric audit in `research_next` | Hooker et al., NeurIPS 2019 (ROAR); Hase et al., NeurIPS 2021 (out-of-distribution problem in erasure explanations) — from memory, not re-checked in this session | **transfer / clarification** | A precise, task-specific statement of a known concern: deletion moves the input into the region where the shortcut is correct. |
| 10 | Generic-init models ignore isolated threshold/date conditions | Pilot 1/1b | — | **empirical finding** | Specific to these models |

**Bottom line.** Nothing here is a verified new result today. Item 4 is the only candidate; it rests on 35 test
items, three seeds per group and a post hoc comparison, and it has an obvious confound (training-set size). Items 2
and 9 are transfers with teaching value.
