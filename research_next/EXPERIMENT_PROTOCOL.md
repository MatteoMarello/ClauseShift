# Confirmatory protocol: ClauseShift-ID (prospective preregistration draft)

Status: **draft, not yet frozen, not run.** It becomes a preregistration when (1) the author has reviewed and
accepted it, (2) the two new families of §3 have been written and committed, and (3) this file and those families
are committed together *before* any confirmatory data are generated or any model is evaluated on them. The commit
hash of that freeze must be quoted in every confirmatory result. Pilots (`PILOT_RESULTS.md`) motivate the hypotheses;
none of their data are reused for confirmation.

Three layers are kept separate everywhere: **original** (registered ClauseShift v2 study), **exploratory** (audit and
pilots), **confirmatory** (this protocol).

## 1. Hypotheses (directional, fixed before data)

| ID | Hypothesis | Primary measure | Decision rule |
|---|---|---|---|
| C1 | Off-the-shelf NLI models given the facts in the premise behave like the lazy program | Item agreement with the lazy program, per model (DeBERTa-v3-base NLI, DeBERTa-v3-base MNLI-FEVER-ANLI, RoBERTa-large-MNLI) on the new-family test set | Supported for a model if the 95% bootstrap lower bound is ≥ 0.93 |
| C2 | Fine-tuned models check the exempted category less when the exemption is stated by cross-reference than inline | Within-case difference of false-flip rates, `xref_other_art1` − `inline_other`, on new-family probes | Supported for an initialisation if the seed-averaged difference has a cluster-bootstrap lower bound > 0 **and** is positive in ≥ 4 of 5 seeds |
| C3 | Paired training increases cross-reference category insensitivity relative to unpaired training (NLI initialisation) | Paired − unpaired false-flip rate on `xref_other_art1` | Supported if the mean over 5 seed pairs is > 0, the cluster-bootstrap lower bound is > 0, and a seed-level paired t-test (df = 4) gives p < 0.05 |
| C4 | Fine-tuned models read strict comparatives as non-strict at the boundary | Share of boundary-side errors that reproduce the satisfied side's label | Supported if the lower bound of the exact binomial 95% interval is > 0.5 for both initialisations; interpreted only together with the human baseline (Part B of `HUMAN_VALIDATION_PROTOCOL.md`) |
| C5 | A joint transition test separates condition-reading models from the lazy program, while hit@1 does not | Joint transition accuracy on decisive removals; hit@1 on the same items | Supported if lazy ≤ 0.10 and every NLI-initialised fine-tuned run ≥ 0.60 on the joint measure, while lazy hit@1 ≥ 0.95 |

Multiplicity: Holm correction over C1–C5 at family-wise α = 0.05 for the test-based rules (C3); interval-based rules
use 95% intervals as stated. All other analyses are exploratory.

C3 direction note: the pilot found the effect for the NLI initialisation only; the generic initialisation is analysed
but not part of C3.

## 2. Secondary question (RQ3, fair compositional test) — separate, may be run later

Train with the cross-reference construction attached to *scope* restrictions ("Article 1 applies only to <subjects>
in <place>", new operator `xref_scope`), keep inline exemptions, and withhold cross-referenced exemptions entirely.
Test on cross-referenced exemptions (held-out combination) and on their near misses. This satisfies the fairness
condition of Geiger et al. (2019) for a reference-resolution node. Hypothesis R1: accuracy on the held-out
combination is at least 0.20 below the in-distribution combinations (non-composition). Falsified if within 0.05.
Budget: 2 conditions × 5 seeds. Not part of the primary family.

## 3. Data

- **Training data**: the original ClauseShift v2 `train` split, unchanged (for C2–C5). For §2 only: a new training
  set produced by a *separate* generator module (`research_next/generator_id.py`, to be written), never by
  modifying `src/clauseshift/generator.py` or `data/`.
- **Epoch selection**: dev family `vehicles` (original dev split), dev macro-F1, as registered.
- **Confirmatory test families**: two **new** fictional families, written by the author before generation (subjects,
  obligation, four categories that differ in more than one word, places, numeric and date attributes, distractors,
  names), e.g. "boat moorings" and "museum loans". Generation seed **20270101**. Non-reserved and reserved templates as
  in v2.
- **Confirmatory test sets** (generated once, after the freeze):
  1. Standard ClauseShift operators, 40 pairs per operator per family (as v2 test).
  2. Cross-reference probe set: 300 base cases per family × six variants (as Pilot 2).
  3. Boundary set: 100 threshold and 100 date pairs per family with the cutoff at the case value, plus matched
     non-boundary pairs.
  4. Fixed transition set: 25 decided, well-posed items per flip operator per family.
- **Inclusion/exclusion**: all generated items are used. No item is removed after seeing model outputs. Items flagged
  as ambiguous by the human study are reported separately (sensitivity analysis), never silently removed.

## 4. Systems

- Lazy program (negative control) and majority class.
- Zero-shot: the four registered NLI models, pinned revisions, standard and facts-in-premise formats.
- Fine-tuned (registered recipe, `scripts/finetune.py` unchanged): `cross-encoder/nli-deberta-v3-xsmall` and
  `microsoft/deberta-v3-xsmall`, conditions paired and unpaired, **new seeds 3, 4, 5, 6, 7** (seeds 0–2 are
  exploratory material).
- Mechanism control (exploratory within the study): a text-only reference normaliser that rewrites
  "Article k does not apply to X" into an inline exemption attached to Article k, applied at test time to the
  fine-tuned models. Uses only the document text, never the specification.
- Oracle (reported separately, never as a system): the reference rule applied to the specification.

## 5. Analysis

- Unit of resampling: base case (probes) or minimal pair (standard operators); cluster bootstrap over cases with all
  seeds kept together; 10,000 resamples for primary measures.
- Seeds: per-seed values always reported; seed-level paired tests where stated.
- Non-convergence: a run whose best dev macro-F1 is below 0.60 is flagged. Primary analyses include all runs
  (intention-to-treat); a sensitivity analysis excluding flagged runs is reported next to it. No run is repeated or
  replaced.
- Program identification: the lattice of `scripts/program_fingerprint.py` is frozen as is (648 programs); selection
  on the original dev split, evaluation on the new families.
- Identifiability audit of the confirmatory test set reported before any model result.

## 6. Compute budget (CPU, 4 cores)

| Block | Runs | Estimated time |
|---|---|---|
| Fine-tuning, 2 initialisations × 2 conditions × 5 seeds | 20 | ≈ 20 × 17 min ≈ 5.7 h |
| Inference on confirmatory sets (fine-tuned + zero-shot) | – | ≈ 1.5 h |
| Secondary RQ3 study (optional) | 10 | ≈ 3 h |
| Total primary | | **≈ 7 h CPU**, no GPU required |

These runs are not launched by the assistant: the protocol must first be frozen by the author.

## 7. What would change the conclusions

- C2 fails in the new families → the pilot effect was family-specific; report as such.
- C3 fails → pairing does not reliably choose the shortcut; the pilot effect was a single-seed artefact.
- Human study shows annotators also read strict comparatives as non-strict → C4 describes a linguistic convention,
  not a model error.
- Program identification on new families selects programs outside the lattice for strong models (agreement close to
  accuracy) → the lattice is too coarse; report the residue.
