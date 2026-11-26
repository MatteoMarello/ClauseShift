# Independent review of `EXPERIMENT_PROTOCOL.md` (v1 draft)

Reviewer stance: a statistician and an NLP methodologist reading the draft adversarially, before any confirmatory
run. The v1 draft is kept unchanged as a historical record; the revisions are in `EXPERIMENT_PROTOCOL_v2.md`. Pilot
results are not modified.

Severity: **[major]** would invalidate or mislead a confirmatory conclusion; **[minor]** weakens it; **[note]**
clarification.

## 1. Definition and aggregation of C2

1. **[major] Conditioning on base correctness creates model-dependent subsamples.** The false-flip rate is computed
   only on base cases a model answers correctly. Two models are then compared on different case sets, and a model
   that is wrong on "easy" bases is evaluated on fewer, harder ones. Recommendation: make the primary measure the
   **joint pair accuracy** on (base, variant) — correct on both — computed on all cases, which is the minimal-pair
   criterion the pilots showed to be robust; keep the conditional false-flip rate as secondary.
2. **[major] Aggregation across families and seeds is unspecified.** "Seed-averaged difference … cluster bootstrap"
   does not say whether the two new families are pooled, averaged, or must agree. With only two families, a pooled
   estimate can be driven by one. Recommendation: estimate per family; the decision requires the same sign in every
   family and a pooled interval excluding 0 (family-stratified cluster bootstrap over cases, seeds kept together).
3. **[minor] The contrast xref_other − inline_other mixes two constructions** that differ in length and position
   (a separate Article 3 vs. a sentence inside Article 1). Recommendation: add an inline control placed in a
   separate article without a reference ("Article 3. Owners of X are exempt from this requirement" is ambiguous; use
   "Article 3. Owners of X are exempt from the requirement in Article 1" vs. "…from the requirement stated above") —
   see §9 controls.

## 2. Comparability of the training conditions

4. **[major] Paired and unpaired training differ in more than pairing.** At equal size, unpaired training sees twice
   as many distinct cases and documents (diversity), and its label distribution varies with the random side
   choice, while paired training is exactly balanced within each pair. The pilot's "pairs teach the token" reading
   is confounded with "less diversity teaches the token". Recommendation: report the label and operator
   distributions of every training set; add (if budget allows) a **diversity-matched unpaired control** — unpaired
   items drawn from 1,200 pairs only (both sides never together) — so that paired vs. this control isolates the
   co-presence of the two sides. Decision for the author (compute: +5 runs).
5. **[minor] Batch composition is not controlled.** `finetune.py` shuffles items, so the two sides of a pair are
   usually in different batches; the "contrast" acts across the epoch, not within a gradient step. State this; do not
   claim a within-batch mechanism.
6. **[note] Training budget.** 12/15 registered runs selected the last epoch; non-convergence differs by condition
   (generic-init paired). Keep the registered recipe for comparability, but report dev curves and flag runs below
   the convergence threshold, as planned.

## 3. Label balance and example diversity in the probes

7. **[major] All pilot base cases are in the "required" state.** An irrelevant exemption can only push "required"
   towards "not required", so a model with a prior towards "exempt when an exemption sentence appears" is detected,
   but the probe is one-directional. Recommendation: draw base cases in all three states (required, not required via
   a failing condition, insufficient via an unstated attribute) in equal proportions; the expected label of every
   label-preserving variant is the base label.
8. **[major] Category similarity is a confound.** Vehicles' categories differ in one word ("owners of electric /
   petrol cars"), which raised inline false flips to 0.41–0.74. New families must have categories that are lexically
   distinct (and the protocol should record a similarity score, e.g. token Jaccard, per category pair); in addition,
   include a planned *similar-category* subset as a separate, labelled stratum rather than an accident.

## 4. Seed and family variability

9. **[major] Two new families cannot support a claim "across families".** Family is a random factor with two
   levels; a family-level interval is not estimable. Either (a) state all conclusions as conditional on the two
   families, or (b) write **four smaller families** (same total items). (b) is preferable scientifically and costs
   the author more writing. Decision for the author.
10. **[major] Seed variance of the probe measures is unknown.** The pilot has one seed per condition. Registered
    seeds differ by up to 0.36 (generic-init) in flip-pair accuracy. See §5.

## 5. Statistical power with five seeds

`results/POWER_ANALYSIS.md` (one-sided paired t-test over seed pairs, α = 0.05):

| Seed pairs | True effect | σ = 0.10 | σ = 0.15 | σ = 0.20 |
|---|---|---|---|---|
| 5 | 0.10 | 0.58 | 0.34 | 0.24 |
| 5 | 0.20 | 0.97 | 0.79 | 0.58 |
| 8 | 0.20 | 1.00 | 0.96 | 0.82 |
| 10 | 0.20 | 1.00 | 0.99 | 0.90 |

11. **[major]** Five seed pairs are adequate only if the true effect is ≈ 0.2 and the between-seed SD of the
    difference is ≤ 0.15. Nothing tells us σ. For the generic initialisation (registered flip-pair SD 0.215) the
    test would likely be under-powered. Recommendation: (a) restrict C3 to the NLI initialisation, as v1 already
    does; (b) before freezing, run a **small seed-variance pilot** (NLI-init, paired and unpaired, two extra seeds:
    4 runs, ≈ 1 CPU-hour; requires authorisation) on the *pilot* families only, estimate σ, and set the number of
    confirmatory seeds from it (target power 0.8 for δ = 0.15); (c) if σ > 0.2, drop C3 as a confirmatory hypothesis
    and report it descriptively.

## 6. Multiple comparisons

12. **[major] Inconsistent multiplicity control.** v1 applies Holm "over C1–C5" but only C3 has a test-based rule;
    the others are interval rules. Recommendation: designate **two primary hypotheses** (C2 and C3), each with a
    p-value (family-stratified cluster bootstrap or permutation over seed labels for C3), Holm-corrected at
    family-wise α = 0.05. C1, C4, C5 become **secondary**, reported with 95% intervals and no confirmatory claim.

## 7. Confirmatory vs. exploratory separation

13. **[minor]** The analysis code for C2–C5 should be written and run on *simulated* predictions before the freeze
    and committed with it, so that no analysis decision is made after seeing confirmatory data.
14. **[minor]** The pilot families (vehicles, enrollment, research_funding) and seeds 0–2 must not enter any
    confirmatory statistic; v1 states this for seeds, v2 adds it for probe families.
15. **[note]** The program lattice is frozen in v1 (648 programs); v2 adds the heuristics needed by the new controls
    (§9) *before* the freeze and records which were added after the pilots.

## 8. Strict vs. non-strict comparisons (C4)

16. **[major] "Non-strict reading" is not the only heuristic consistent with boundary errors.** An "approximate
    comparison" heuristic (errs within a small distance of the cutoff on both sides) also errs at equality. The
    pilot's 100% copy rate cannot distinguish them, because no items lie *just above* the cutoff. Recommendation: add
    near-boundary items at cutoff + 1 unit (and dates one day after) whose correct reading is "satisfied"; a non-strict
    reader is right there, an approximate reader is not. Add both heuristics to H.
17. **[major] Template wording matters**: "more than", "exceeds", "above", "unless … greater than" may differ in
    perceived strictness, and "after 3 May" with an event on 3 May is arguably vaguer than numeric equality. Report
    C4 per template and per type (numeric/date); interpret only against the human baseline (Part B), which must use
    the same templates.

## 9. Can the joint transition metric reward other shortcuts? (C5) — and requested controls

18. **[major] The metric itself should be audited with mutants.** A metric is valid only if the intended rule scores
    higher than every plausible wrong program. Recommendation: before the freeze, compute the joint transition score
    for every program in the lattice (programs are defined on specifications, so post-removal predictions are
    computable without models) and check that r is ranked first and that the lazy and token-shortcut programs score
    low. A program that ignores categories but tracks condition *presence* could, for example, score well on decisive
    removals of failing conditions; this check would reveal it. Also report conditional transition accuracy
    P(correct after | correct before) next to the joint score.
19. **[minor]** Removal variants lose the article headers; keep the header-free control and add a header-preserving
    removal variant (re-number articles after deletion) as a robustness check.

Requested controls (all as additional probe variants, labels from the specification):

| Control | Construction | What it separates |
|---|---|---|
| Renumbered references | Obligation stated in Article 2 (Article 1 = another obligation); exemptions "Article 2 does not apply to …" | Digit-"1" shortcut vs. reference resolution (the digit no longer marks the obligation) |
| Article order | Cross-reference article placed before vs. after the obligation article | Position heuristics ("last article exempts") |
| Irrelevant categories | Exemption naming a category from another family or a nonce category | Presence-of-exemption heuristic vs. category matching |
| Lexical complexity | Multi-word vs. single-word category names; synonyms of the case category ("an owner of an electric car" vs. "electric-car owners") | Surface string matching vs. category matching |
| Similar categories (stratum) | Categories differing in one word | Measures, instead of suffering, the vehicles-type confound |

## 10. Verdict

The v1 protocol is directionally right but **not ready to freeze**: the primary measure should change (joint pair
accuracy), the aggregation and multiplicity rules must be specified, the paired/unpaired comparison needs a
diversity control or an explicit caveat, the number of seeds must come from a seed-variance estimate, and C4/C5 need
additional heuristics and a mutant audit of the metric. These changes are implemented in `EXPERIMENT_PROTOCOL_v2.md`.
