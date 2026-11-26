# Decision memo

Date: 2026-11-26. Basis: `SCIENTIFIC_AUDIT.md`, `PILOT_RESULTS.md`, `NOVELTY_ASSESSMENT.md`, `LITERATURE_REVIEW.md`.
All evidence cited here is **exploratory** (computed after the original results were known, one seed per condition
for the probes, two of three probe families added post hoc). Nothing in this memo is a confirmed finding.

## 1. Best scientific direction

**Identifiability-aware evaluation of rule application: what a minimal-pair benchmark can tell apart, and which
program a model actually runs.**

Core questions: RQ2 (benchmarks hide what they cannot identify; does the training regime decide which hidden shortcut
is learned?) with RQ1 (behavioural program identification) as its method. Supporting section: RQ4 (evidence metrics
must be contrastive). Secondary, separate study: RQ3 (a fair compositional test of cross-references).

Discarded as main lines: external validity on real contracts (Direction D: no compatible released benchmark with
controlled edits; ContractNLI is usable only for a narrow "lazy heuristic" check), neuro-symbolic solvers (Direction C:
a template parser solves synthetic data trivially; kept only as a reference-normalisation control), a new legal
benchmark (crowded: COMPACT, CLAUSE, ContractNLI, LegalBench), and the paired-vs-unpaired effect on accuracy as a
headline (small and fragile).

## 2. Hypothesised original contribution

1. A **benchmark identifiability audit**: for a lattice of plausible partial rule readings, count the items that
   separate each one from the intended rule. Applied to ClauseShift, a benchmark built with near-miss controls,
   invariance pairs and a hypothesis-only control, it finds a dimension (cross-references) with **zero** identifying
   items.
2. **Probes generated from the audit** reveal that models with near-identical scores on that dimension run different
   incomplete programs, and that the **training regime chooses the program**: training on complete minimal pairs is
   associated with keying on the pair's single lexical difference (the article digit) — the opposite of the usual
   motivation for counterfactual data.
3. A transferable evaluation lesson: every single-input criterion we tried (accuracy, invariance, occlusion hit@1,
   post-removal agreement) is satisfied, or nearly, by a program that reads no condition; only **joint contrastive
   criteria** (pair accuracy, joint transition accuracy) reject it.

## 3. Evidence

For (exploratory):
- Lazy program ≈ off-the-shelf NLI models: item agreement 0.966–0.983 (κ 0.94–0.97) with facts in the premise; same
  aggregate scores as the best zero-shot model (accuracy 0.529 vs 0.531; flip-pair 0.300 vs 0.304).
- Identifiability: 0 of 2,560 test items separate "resolve the reference" from "react to Article 1"; only 23 and 17
  separate strict from non-strict thresholds and dates.
- Probes: irrelevant exemptions stated by reference cause more answer changes than the same exemption inline in
  12/12 model×family cells (10/12 intervals exclude 0); NLI-initialised paired training raises them by +0.17 to +0.36
  over unpaired training in all three families; the generic-init unpaired model treats any reference naming the
  case's category as an exemption (0.85–0.97 false flips for "Article 2"), the paired one keys on "Article 1".
- Evidence: lazy program hit@1 = 1.00; joint transition accuracy on decisive removals 0.00 (lazy) vs. 0.65–0.78
  (NLI-init fine-tuned).
- Re-trained models reproduce the registered runs exactly, so the probes describe the reported models.

Against:
- One seed per condition in the probes; registered seeds differ by up to 0.36 in the paired-vs-unpaired comparison.
- Two of three probe families were added after seeing the first; the pre-specified prediction S1 failed on its
  control (inline false flips 0.41–0.74 in vehicles, not < 0.1): models match categories poorly in general, and the
  reference-specific part is a difference on top of that.
- The shortcut exists because of our own generator design; reviewers may call it a dataset bug.
- Synthetic templates, ~100-token documents, small encoders, no LLMs, no human validation.
- Closely related ideas exist (HANS, ScoNe, causal abstraction, underspecification, recent shortcut-discovery work
  such as UNMASK and "Catching Shortcuts", read only as abstracts). The novelty margin is real but narrow.
- The program lattice was designed after seeing the audit.

## 4. Experiments still needed

1. The confirmatory study in `EXPERIMENT_PROTOCOL.md` (new families written by the author, 5 new seeds per
   condition, frozen lattice, hypotheses C1–C5).
2. Human study Parts A–C (`HUMAN_VALIDATION_PROTOCOL.md`), in particular the strict-boundary baseline.
3. An LLM check: one or two open-weight instruction-tuned models (7–8B) on the confirmatory probes, to show the
   identifiability argument is not specific to small encoders.
4. The identifiability audit applied to one external benchmark with a known structure (e.g. a public contrast set or
   ScoNe), to show the method is general.
5. Full-text reading of ScoNe, causal abstraction, UNMASK, "Catching Shortcuts" and the numeracy-NLI paper before any
   novelty claim.

## 5. Skills required

Experimental design and preregistration; bootstrap and cluster-bootstrap inference; fine-tuning transformers with
PyTorch/Transformers; writing a controlled generator; Bayesian experimental design (for the adaptive part);
annotation study design and agreement statistics; scientific writing (precise claims, limitations).

## 6. Computational resources

- Primary confirmatory study: ≈ 7 CPU-hours on the current 4-core machine (no GPU needed).
- Secondary RQ3 study: ≈ 3 CPU-hours.
- LLM check: a single GPU with ≥ 24 GB for a 7–8B model in bf16; a few GPU-hours of inference (estimate, not
  measured). Not available in this container.

## 7. Indispensable human activities

- Write the two new fictional families (vocabulary, categories that differ in more than one word) and freeze the
  protocol.
- Recruit at least three annotators, run Parts A–C, adjudicate.
- Decide the target venue and timeline; write the paper's introduction, framing and limitations.
- Verify novelty against the full texts listed above.
- Re-derive key numbers by hand (study guide exercises) to own the results.

## 8. Recommendation: **CONDITIONAL GO**

Go for the identifiability direction **if** the following conditions are met, in this order:
1. Confirmatory C2 holds in the new families (reference-specific category insensitivity, ≥ 4 of 5 seeds).
2. Either C3 holds (pairs choose the digit-keyed program) or the paper is reframed around C2 + C1 + C5 without the
   pairing claim.
3. The full-text novelty check does not reveal prior work that already counts distinguishing items per heuristic for
   existing benchmarks.

If condition 1 fails: **NO GO** for a paper on this direction; publish the completed ClauseShift study as a
technical report (with the lazy-reader and joint-criterion results as a short section) and consider a workshop
note on contrastive evidence criteria.

Realistic target if conditions hold: an ACL 2027 Student Research Workshop or an analysis workshop (BlackboxNLP /
NLLP 2027), not ACL 2027 main (ARR deadline January 4, 2027 is too close for the confirmatory study and human
validation). See `PUBLICATION_ROADMAP.md`.
