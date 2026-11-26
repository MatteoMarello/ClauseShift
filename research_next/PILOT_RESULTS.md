# Pilot results

All pilots are **exploratory**. Predictions for Pilots 1–2 were fixed in `PILOT_PLAN.md` (commit `63b365c`) before
they were run; deviations from that plan are listed in §6. The data in `data/` and every original result are
unchanged. Re-trained models reproduce the registered runs exactly (item agreement 1.0000 with the stored test
predictions for all four configurations), so the probes evaluate the same models that the original report describes.

Compute: one 4-core CPU; four re-training runs (~16 min each) and inference only otherwise. Weights are kept in a
local, gitignored `checkpoints/` directory and are not distributed.

## Pilot 1 — the lazy reader

A program that reads only whether the claimed obligation is stated (and negated) and ignores every condition
(`scripts/lazy_reader.py`, `results/lazy_reader.json`, `results/lazy_agreement.json`):

| | Lazy reader | Best zero-shot model (DeBERTa-v3-base MNLI-FEVER-ANLI, standard format) |
|---|---|---|
| Accuracy | 0.529 | 0.531 |
| Pair accuracy | 0.310 | 0.316 |
| Flip-pair accuracy | 0.300 | 0.304 |
| Occlusion hit@1 (registered protocol) | **1.000** (300/300; top sentence = obligation in 300/300) | 1.000 |

Item-level agreement with the lazy reader (test, 2,560 items), facts-in-premise format: DeBERTa-v3-base NLI 0.983
(κ 0.970), DeBERTa-v3-base MNLI-FEVER-ANLI 0.982 (κ 0.968), RoBERTa-large-MNLI 0.966 (κ 0.937). Standard format:
0.919, 0.779, 0.518. Fine-tuned models: 0.43–0.61.

Predictions: P1a (lazy reader far below fine-tuned models in flip-pair accuracy) **holds** (0.300 vs. ~0.80).
P1b (hit@1 = 1.00) **holds**. P1c (agreement 0.00 on decisive removals) **could not be evaluated**: the lazy reader
is never correct on an item whose label depends on a condition, so the registered protocol, which samples correctly
answered items, contains no decisive removal for it. This is itself a flaw of the protocol (fixed in Pilot 4).

## Pilot 2 — cross-reference probes

Probe set: 200 base cases per family whose conditions are all satisfied, each rendered six ways (`make_probes.py`).
False-flip rate = share of base cases answered correctly whose answer changes when a label-preserving sentence is
added. Full table: `results/PROBE_TABLE.md`; within-case tests: `results/PROBE_PAIRED_TESTS.md`.

### Pre-specified family (vehicles)

| Model (seed 0) | acc. base | acc. `xref_case_art1` | false flips `xref_other_art1` | false flips `inline_other` | false flips `xref_case_art2` |
|---|---|---|---|---|---|
| NLI-init, paired | 0.81 | 1.00 | **0.75** [0.69, 0.81] | 0.56 [0.48, 0.64] | 0.02 |
| NLI-init, unpaired | 0.93 | 0.99 | **0.53** [0.46, 0.60] | 0.41 [0.34, 0.48] | 0.02 |
| generic-init, paired | 0.94 | 0.99 | **0.91** [0.87, 0.95] | 0.56 [0.49, 0.63] | 0.19 |
| generic-init, unpaired | 0.98 | 0.98 | **0.92** [0.88, 0.95] | 0.74 [0.68, 0.80] | **0.97** |
| lazy reader (control) | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| zero-shot DeBERTa-v3-base NLI | 0.80 | 0.02 | 0.04 | 0.06 | 0.01 |

Verdicts on the fixed predictions:
- **S1 (xref_other > 0.5 and inline_other < 0.1): not supported as stated.** The first half holds for all four
  fine-tuned models (0.53–0.92), but the inline control is far above 0.1 (0.41–0.74). In this family the models
  match categories poorly in general (its four categories differ in one word: "owners of electric / hybrid / diesel /
  petrol cars"; the original dev near-miss invariance was 0.74–0.79).
- **S2 (paired > unpaired on xref_other, both initialisations): half supported.** NLI-init 0.75 vs 0.53; generic-init
  0.91 vs 0.92.
- **S3 (`xref_case_art1` > 0.8 for NLI-init models): supported** (1.00, 0.99).

### Post hoc extension to the two test families (decided after seeing the vehicles results)

Within-case difference of false-flip rates, `xref_other_art1` − `inline_other` (95% bootstrap over cases):

| Model | vehicles | enrollment | research_funding |
|---|---|---|---|
| NLI-init, paired | +0.198 [+0.136, +0.265] | +0.385 [+0.313, +0.451] | +0.236 [+0.157, +0.309] |
| NLI-init, unpaired | +0.113 [+0.048, +0.177] | +0.199 [+0.138, +0.260] | +0.041 [−0.021, +0.103] |
| generic-init, paired | +0.351 [+0.282, +0.426] | +0.285 [+0.218, +0.352] | +0.104 [+0.036, +0.171] |
| generic-init, unpaired | +0.179 [+0.117, +0.245] | +0.276 [+0.204, +0.347] | +0.040 [−0.025, +0.106] |

Positive in 12/12 model×family cells; the interval excludes 0 in 10/12. An irrelevant exemption stated *by reference*
changes the answer more often than the same exemption stated inline.

Paired minus unpaired training, false flips on `xref_other_art1` (same cases, both models correct on base):

| Initialisation | vehicles | enrollment | research_funding |
|---|---|---|---|
| NLI checkpoint | +0.281 [+0.206, +0.356] | +0.172 [+0.115, +0.229] | +0.362 [+0.288, +0.429] |
| generic checkpoint | −0.005 [−0.059, +0.049] | +0.109 [+0.026, +0.198] | +0.204 [+0.131, +0.277] |

### What the four models do with cross-references (descriptive, seed 0)

All four solve the in-distribution construction (`xref_case_art1`, 0.89–1.00 in every family), so the original
benchmark cannot tell them apart (identifiability 0). The probes separate three behaviours:
- **generic-init, unpaired**: also flips for "Article **2** does not apply to <case category>" (0.85–0.97): it treats
  *any* cross-reference naming the case's category as an exemption, ignoring the article number.
- **generic-init, paired** and **NLI-init, paired**: rarely flip for Article 2 (0.00–0.19) but often flip for
  Article 1 naming *another* category (0.48–0.91): they key on "Article 1" and under-use the category.
- **NLI-init, unpaired**: the most category-sensitive of the four (0.25–0.53 false flips), still above its inline
  control in two families.

Reading: in this pilot, the training regime determines *which* incomplete program a model learns for a construction
that the benchmark cannot test. Pairs, whose two sides differ only in the article digit, are associated with the
digit-keyed program; for the NLI-initialised model they also reduce category checking. This is the opposite of the
usual motivation for counterfactual pairs, and it is based on **one seed per condition**: the bootstrap intervals
cover case sampling only. In the registered runs, the per-seed paired-minus-unpaired differences in flip-pair accuracy span
0.04 (NLI-init) and 0.36 (generic-init), so the paired-vs-unpaired contrasts must be replicated with new seeds before any claim.

## Pilot 3 — adaptive program identification

Bayesian adaptive item selection over the 648-program lattice, with the saved test predictions as oracle
(`scripts/adaptive_identification.py`): items needed until ≥ 90% of the posterior mass stays on programs within 0.01
of the best agreement.

| Model | Adaptive | Random (median of 20) |
|---|---|---|
| zero-shot DeBERTa-v3-base NLI, facts in premise | 13 | 85.5 |
| zero-shot RoBERTa-large-MNLI, facts in premise | 13 | 88 |
| zero-shot DeBERTa-v3-base MNLI-FEVER-ANLI | 47 | 154 |
| fine-tuned NLI-init paired s1 | 29 | 130 |
| fine-tuned NLI-init unpaired s0 | 17 | 74.5 |
| fine-tuned generic-init paired s0 | 14 | 104 |
| fine-tuned generic-init unpaired s0 | 139 | 155 (5/20 not identified within 300) |

Roughly 3–7× fewer items for six of seven models; no gain for the model the lattice describes worst. A first
criterion (posterior mode) was replaced because tie-breaking under the uniform prior favoured the "ignore everything"
program; the replaced numbers are not reported as results.

## Exploratory analyses run alongside the pilots

- **Program identification** (`results/PROGRAM_FINGERPRINT.md`): zero-shot models → "topic + negation only";
  generic-init fine-tuned → non-strict comparisons, scope ignored; NLI-init fine-tuned → reference rule up to the
  cross-reference dimension, which is not identifiable.
- **Identifiability of the test set**: items distinguishing each one-dimension deviation from the rule — cross-reference
  "article token" **0**; strict vs. non-strict thresholds 23 and dates 17; ignore scope 80; ignore exemptions 174;
  "any exemption applies" 479; ignore unstated attributes 458.
- **Boundary errors** (audit A3): 100% of fine-tuned boundary errors reproduce the non-strict reading (38 boundary
  pairs).

## Pilot 4 — transitions on a fixed item set

One stratified set of 175 decided, well-posed test items (25 per flip operator, no cross-reference; 641 sentence
removals), identical for every system (`scripts/fixed_set_transitions.py`, `results/FIXED_SET_TRANSITIONS.md`).

**First version (v1, single input) failed in an instructive way.** Scoring only the prediction on the shortened
document, the lazy reader obtained **1.000** on decisive removals (n = 49): it always answers "required", and after
the failing condition is removed "required" is indeed the expected label. A model that never reacts to the clause is
credited for "getting the transition right". The v1 table is kept in `results/FIXED_SET_TRANSITIONS_v1_single_input.md`.

**Second version (v2, joint)** credits a removal only if the prediction is correct on the full (header-free) document
*and* on the shortened one, i.e. the minimal-pair criterion applied to sentence removal:

| System | Full-doc acc. | Obligation removed → insufficient | **Decisive removed → expected change** | Non-decisive removed → kept | hit@1 (same items) |
|---|---|---|---|---|---|
| lazy reader | 0.720 | 0.720 | **0.000** | 0.715 | 1.000 |
| zero-shot DeBERTa-v3-base NLI | 0.640 | 0.480 | **0.020** | 0.619 | 0.903 |
| zero-shot DeBERTa-v3-base MNLI-FEVER-ANLI | 0.703 | 0.634 | **0.224** | 0.659 | 0.966 |
| generic-init, paired s0 | 0.680 | 0.554 | **0.388** | 0.571 | 0.931 |
| generic-init, unpaired s0 | 0.640 | 0.549 | **0.327** | 0.544 | 0.931 |
| NLI-init, paired s0 | 0.897 | 0.886 | **0.776** | 0.803 | 1.000 |
| NLI-init, unpaired s0 | 0.851 | 0.823 | **0.653** | 0.787 | 1.000 |

Joint decisive-transition accuracy broadly follows flip-pair accuracy (fine-tuned NLI-init > generic-init > zero-shot),
with one telling exception: flip-pair accuracy ranks the lazy reader (0.300) level with the best zero-shot model
(0.304), while the joint transition test places it last (0.000). hit@1 is 0.90–1.00 for all systems, including the
lazy reader. n = 49 decisive removals per system, so the
intervals are wide (not computed in this pilot).

**General lesson (the most transferable result of the pilots).** Every evaluation criterion we tried that looks at a
single input — accuracy, invariance, occlusion hit@1, post-removal agreement — was satisfied, or nearly so, by a
program that reads no condition. Only criteria that require being right on *both* members of a controlled contrast
(pair accuracy, joint transition accuracy) rejected it.

## 5. Summary of what the pilots changed

1. The zero-shot results are better described as "obligation spotting" than as "failing hard edits".
2. The cross-reference result of the original study is not interpretable in either direction (unfair hold-out;
   non-identifiable in-distribution). Probes show that fine-tuned models check the exempted category less when it is
   stated by reference, and that the training regime changes which incomplete program is learned.
3. Evidence metrics must use joint (contrastive) criteria; single-input criteria certify the lazy program.
## 6. Deviations from the pilot plan

1. Pilot 2 probes for `enrollment` and `research_funding` were added after the vehicles results were seen, because
   the inline control failed in vehicles. These results are labelled post hoc everywhere.
2. Within-case paired tests (xref vs. inline; paired vs. unpaired) were not in the plan; they were added to replace
   comparisons of independent intervals.
3. Pilot 3 and Pilot 4 were not in the plan (designed after Pilot 1).
4. The identification criterion of Pilot 3 was changed once, for the reason given above.
