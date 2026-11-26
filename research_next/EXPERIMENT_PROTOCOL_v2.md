# Confirmatory protocol v2 (draft, NOT frozen, NOT run)

Supersedes the v1 draft (`EXPERIMENT_PROTOCOL.md`, kept unchanged) after the independent review
(`PROTOCOL_REVIEW.md`). Freezing requires the author's decisions listed in §10; until then nothing here is a
preregistration and no confirmatory data may be generated.

Layers: **original** (ClauseShift v2 registered study) · **exploratory** (audit, pilots, external audit) ·
**confirmatory** (this protocol, after the freeze commit). Confirmatory statistics never use pilot families
(vehicles, enrollment, research_funding), seeds 0–2, or the pilot probe sets.

## 1. Hypotheses

Primary (Holm-corrected, family-wise α = 0.05):

| ID | Hypothesis | Primary measure | Decision rule |
|---|---|---|---|
| P1 (was C2) | Fine-tuned models check the exempted category less when the exemption is stated by cross-reference than inline | Difference in **joint pair accuracy** (correct on base and on variant) between `inline_other` and `xref_other`, computed on all cases | Positive in every new family; family-stratified cluster bootstrap (cases resampled within family, seeds kept together) gives one-sided p < α after Holm |
| P2 (was C3) | Paired training lowers joint accuracy on `xref_other` relative to unpaired training (NLI initialisation) | Seed-level paired difference (paired − unpaired) in joint accuracy on `xref_other` | One-sided paired t-test over seed pairs, p < α after Holm; number of seed pairs fixed from the seed-variance pilot (§6) |

Secondary (95% intervals, no confirmatory claim): S1 lazy-program agreement of zero-shot models (was C1);
S2 boundary readings (was C4, extended, §4); S3 joint transition test (was C5, with the mutant audit, §5);
S4 program identification on new families (frozen lattice + additions of §3).

## 2. Data

- Training data: the original ClauseShift v2 `train` split, unchanged.
- Epoch selection: original dev (vehicles), dev macro-F1.
- **New families**: written by the author (`FAMILY_DESIGN_EXERCISE.md`). Preferred: **four** smaller families
  rather than two large ones (review §4); category names lexically distinct (token Jaccard ≤ 0.34 between any two
  categories of a family), plus a planned similar-category stratum.
- Generation seed 20270101, generated once after the freeze commit, by a separate module
  (`research_next/generator_id.py`, to be written; `src/clauseshift/generator.py` and `data/` stay unchanged).

### Probe design (per family)
Base cases in three equal strata of base label state: required; not required (one failing condition);
insufficient (condition on an unstated attribute). For each base case, variants:

| Variant | Construction | Label vs. base |
|---|---|---|
| `xref_case` | "Article k does not apply to <case category>", k = obligation article | changes (if base not already decided otherwise) |
| `xref_case_other_article` | same, k = another article | same |
| `xref_other` | "Article k does not apply to <other category>", k = obligation article | same |
| `inline_case` / `inline_other` | inline exemption, case / other category | changes / same |
| `separate_other` | separate article stating an exemption from "the requirement above" for another category, no article number | same |
| `renumbered_*` | obligation stated in Article 2 (Article 1 another obligation); the xref variants use "Article 2" | as above |
| `order_*` | cross-reference article placed before the obligation article | as above |
| `nonce_other` | exemption for a category from another family or a nonce category | same |
| `synonym_case` | case category paraphrased in the exemption ("electric-car owners") | changes |

Boundary set: per family, 50 threshold and 50 date base cases at exact equality (strict reading: condition fails),
50 + 50 at cutoff + 1 unit / + 1 day (satisfied), and matched far-from-boundary items.

Fixed transition set: built from item **signatures** so that every pair of lattice programs distinguishable in
principle is separated by at least k = 19 decisive removals (FORMALIZATION §5, ε = 0.2, δ = 0.01): this requires
adding boundary, negation and unknown-attribute removals that the pilot set lacked (`METRIC_MUTANT_AUDIT.md`).

## 3. Heuristic space (frozen at the freeze commit)

The 648-program lattice, plus programs added after the pilots and declared as such:
`xref = any_reference` (any cross-reference naming the case category exempts; pilot behaviour of generic-init
unpaired), `xref = presence` (any cross-reference exempts), `comparison = approximate` (errs within one unit of the
cutoff on both sides), `exemption = string_match` (exemption applies only on exact string match of the category
phrase). Programs are defined on specifications; their post-removal and probe predictions are computed without models.

## 4. Systems and runs

- Lazy program; majority; zero-shot NLI models (pinned revisions; standard and facts-in-premise formats).
- Fine-tuned, registered recipe unchanged: NLI initialisation, paired and unpaired, **n seed pairs from §6**,
  new seeds starting at 3. Generic initialisation: same seeds, analysed descriptively only (not in P2).
- Optional (author's decision, +runs): diversity-matched unpaired control (one side of each of 1,200 pairs).
- Mechanism control: text-only reference normaliser applied at test time (rewrites references into inline
  exemptions); exploratory.

## 5. Analyses

- Primary measures as in §1; per-family estimates always reported; seeds and families listed.
- Clustering: cases within family; seeds kept together; 10,000 bootstrap resamples; seed-level paired t-test for P2.
- Non-converged runs (best dev macro-F1 < 0.60): included (intention-to-treat); sensitivity analysis without them.
- Before any model result: identifiability audit of the generated confirmatory sets (coverage counts per program,
  equivalence classes, minimum discriminating sets) and the **mutant audit of the transition metric** — the intended
  rule must be the unique top program on the joint score; if not, the fixed set is regenerated *before* models are
  evaluated.
- Program identification: selection on original dev; agreement and residual reported on new families.
- Analysis code committed with the freeze and run end-to-end on simulated predictions.

## 6. Seed-variance pilot (requires authorisation, before the freeze)

NLI initialisation, paired and unpaired, seeds 1 and 2 (seed 0 exists): 4 runs, ≈ 1 CPU-hour, evaluated on the
pilot probe families only. Estimate σ of the paired-minus-unpaired difference in joint `xref_other` accuracy; choose
n seed pairs for power 0.8 at δ = 0.15 (`results/POWER_ANALYSIS.md`). If the required n exceeds 10, P2 is dropped as
a confirmatory hypothesis and reported descriptively. These runs are exploratory and do not enter confirmatory tests.

## 7. Budget (CPU, 4 cores)

| Block | Runs | Time |
|---|---|---|
| Seed-variance pilot | 4 | ≈ 1 h |
| Confirmatory fine-tuning (NLI paired/unpaired) | 2n (n = 5–10) | ≈ 3–6 h |
| Generic-init descriptive runs | 2n | ≈ 3–6 h (optional) |
| Diversity-matched control | n | ≈ 1.5–3 h (optional) |
| Inference on all sets | – | ≈ 2 h |

## 8. Interpretation rules

- P1 holds, P2 fails → reference-specific category insensitivity is real; the pairing claim is withdrawn.
- P1 fails in any family → no claim about cross-references beyond "pilot families".
- S2: non-strict reading claimed only if (a) equality items are mostly wrong, (b) cutoff+1 items are mostly right,
  and (c) human annotators mostly choose the strict reading on the same templates.
- Behavioural identification never licenses claims about internal mechanisms (FORMALIZATION §6).

## 9. Changes from v1

Primary measure (conditional false flips → joint pair accuracy); two primary hypotheses with Holm; per-family
decision; three base-label strata; lexically distinct categories and a planned similar-category stratum; four
families recommended; seed-variance pilot and power-based n; added controls (renumbering, order, nonce, synonym,
separate article); near-boundary items and approximate-comparison heuristic; mutant audit of the transition metric
and signature-based fixed set; heuristics added after the pilots declared.

## 10. Decisions required from the author before the freeze

See `DECISION_MEMO.md` §9.
