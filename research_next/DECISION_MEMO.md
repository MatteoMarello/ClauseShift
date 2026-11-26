# Decision memo (v2)

Date: 2026-11-26. Supersedes v1 (commit `d96c10b`, in git history). Basis: `NOVELTY_VERIFICATION.md`,
`FORMALIZATION.md`, `EXTERNAL_AUDIT_RESULTS.md`, `PROTOCOL_REVIEW.md`, `PILOT_RESULTS.md`, `SCIENTIFIC_AUDIT.md`.
Every result cited here is **exploratory**. No confirmatory run has been made; no new fine-tuning was done in this
round.

## 1. What changed since v1

1. **Novelty**: the methodology is **not new**. Its components exist as mutation analysis (kill matrix, equivalent
   mutants, subsumption, test-suite minimisation as hitting set) in software testing — including recent use for
   *code-LLM benchmark adequacy* — and as outcome-based strategy classification in cognitive psychology (identifying
   a decision strategy from choices on diagnostic items under a constant error rate). We found no application to NLP
   benchmarks for NLI/rule reading that combines them; that absence is a search result, not proof.
2. **External validity of the method**: on HANS and ScoNe, heuristics defined from the papers alone yield
   indistinguishable pairs on both benchmarks, 3-item minimum discriminating sets, and item-level identification of
   published and zero-shot models; one finding is not discussed in the original paper (HANS cannot separate lexical
   overlap from constant entailment), one is acknowledged implicitly (ScoNe's two correct algorithms), and the ScoNe
   identification is a null result for hidden gaps.
3. **Metric audit**: the transition-test metric itself was audited with the program lattice: single-input scoring
   gives 432/648 programs a perfect score; joint scoring removes the lazy program (0.000) but still leaves 24/648
   programs tied with the rule on the pilot item set — the item set, not the metric, is the limit.
4. **Protocol**: the v1 draft has major issues (primary measure, aggregation, multiplicity, diversity confound,
   power); v2 fixes them and needs your decisions (§9) before it can be frozen.

## 2. The contribution, separated

### A. General methodological contribution — "benchmarks as test suites"
Treat a benchmark as a test suite and plausible wrong readings of the task as mutants of the intended rule; report
per-mutant distinguishing counts, equivalence classes, a sample-size target per mutant, minimum discriminating sets,
and identify models by item-level agreement under an explicit noise model.
- Status: **a transfer and synthesis**, not an invention. Formalised (`FORMALIZATION.md`), implemented, cheap.
- Evidence it is useful: findings in B and C that aggregate metrics did not show (ClauseShift cross-reference
  dimension with 0 items; HANS LO ≡ constant entailment; MNLI dev with 27 LO-contradicting items; the metric audit).
- Interest independent of D (C3/P2): **yes**. A–C stand without any claim about counterfactual training.

### B. Empirical application to ClauseShift
- 0 of 2,560 test items distinguish cross-reference resolution from an article-token shortcut; 23/17 items
  separate strict from non-strict comparisons.
- Off-the-shelf NLI models behave like a "topic + negation only" program (96.6–98.3% item agreement).
- Probes: reference-specific category insensitivity in 12/12 model×family cells (one seed; post hoc families).
- Evidence metrics: single-input criteria certify the lazy program; joint criteria do not, but need designed items.
- Status: exploratory, synthetic, small encoders, no human validation.

### C. Results on external benchmarks
- HANS: LO ≡ constant entailment (0/30,000 items); 3 items separate all 14 distinguishable pairs; four published
  models in the LO ≡ ALL_E class. MNLI dev: 27/9,815 items contradict the LO implication.
- ScoNe: intended rule ≡ "exactly one scoped negation" (0/1,200); 3 items suffice; four zero-shot NLI models
  identified as ignore-negation (0.92–0.98).
- Status: done, exploratory, licences compatible (MIT, CC0). Heuristic spaces are small.

### D. Counterfactual training and shortcut learning
- Pilot: NLI-init paired training raised reference-specific errors over unpaired training by +0.17 to +0.36 in three
  families (one seed); generic init mixed; the pre-specified control failed in the pre-specified family.
- Confounds identified in review: diversity (unpaired sees twice as many cases), label-state imbalance of probes,
  category similarity, unknown seed variance; power with 5 seeds is adequate only if δ ≈ 0.2 and σ ≤ 0.15.
- Status: **weakest part**; needs the seed-variance pilot before it is worth confirmatory compute.

## 3. Evidence for and against (overall)

For: consistent, checkable findings across one synthetic and two external benchmarks; cheap, reproducible scripts;
a clean link to established theory (mutation analysis, strategy classification, experimental design); results that
reinterpret aggregate numbers (lazy-reader equivalence, LO ≡ ALL_E).
Against: no methodological novelty in the strict sense; small hand-written heuristic spaces; one of two external
audits finds nothing hidden; ClauseShift results are synthetic and exploratory; D is fragile; no human validation; no
LLM evaluation.

## 4. Experiments still needed (in order of value per cost)

1. Extend the external audit with **richer, independently written heuristic spaces** (written by you before
   computing) and a third benchmark (e.g. a CheckList suite or a public contrast set). No training. High value.
2. Seed-variance pilot (4 runs, ≈ 1 CPU-hour; needs authorisation) → decide whether D/P2 is testable.
3. Confirmatory study v2 on your new families (≈ 4–8 CPU-hours depending on n and options).
4. Human study Parts A–C.
5. An open-weight instruction-tuned LLM on the confirmatory probes and on HANS/ScoNe (needs a GPU).

## 5. Skills required

Experimental design and preregistration; bootstrap/cluster inference and power analysis; mutation-analysis and
set-cover reasoning; writing a controlled generator and heuristic programs; annotation study management; precise
scientific writing that distinguishes transfer from invention.

## 6. Computational resources

External audits and metric audits: seconds to minutes on CPU. Seed-variance pilot: ≈ 1 CPU-hour. Confirmatory
study: ≈ 4–8 CPU-hours. LLM evaluation: one ≥ 24 GB GPU, a few GPU-hours (estimate). No paid API is needed.

## 7. Indispensable human activities

Write the new families (`FAMILY_DESIGN_EXERCISE.md`); write additional heuristic spaces for HANS/ScoNe before
computing; recruit and coordinate ≥ 3 annotators (`ANNOTATOR_RECRUITMENT.md`); adjudicate; take the decisions in §9;
write the paper's framing and limitations yourself.

## 8. Recommendation: **CONDITIONAL GO**, reframed

Go on **A + B + C** as the core contribution ("benchmarks as test suites for shortcut hypotheses"), presented
explicitly as a transfer of mutation analysis and strategy classification to NLP evaluation, with D as an optional,
clearly separated empirical section. Conditions:
1. A focused novelty check on the two source fields' full texts and on NLP evaluation papers using "mutation" or
   "strategy classification" vocabulary does not find the same application to NLP benchmarks.
2. The extended external audit (step 4.1) produces at least one further non-trivial equivalence or coverage gap on an
   independently specified heuristic space — or, if it does not, the paper is framed as a tool/position paper with
   the existing HANS/ClauseShift findings and modest claims.
3. D enters the paper only if the seed-variance pilot shows P2 is testable with ≤ 10 seed pairs.

NO GO conditions: a prior NLP paper with the same combined method; or the external audits yield nothing beyond what
the original papers state (then publish the ClauseShift technical report and a short note on contrastive evidence
criteria).

Realistic level: workshop or Student Research Workshop paper (analysis/evaluation workshops) in 2027; a
Findings-level paper would additionally need LLM evaluation and several external benchmarks. ACL 2027 (ARR deadline
4 January 2027) is not recommended.

## 9. Decisions you must take before freezing the protocol

1. **Framing**: methodological-transfer paper (A+B+C, recommended) or counterfactual-training paper (D-centred)?
2. **Families**: two large or four small new families (four recommended); write them yourself.
3. **Seed-variance pilot**: authorise the 4 runs (≈ 1 CPU-hour) or drop P2 as confirmatory now.
4. **Diversity-matched unpaired control**: include (+n runs) or report the confound as a limitation.
5. **Primary measure**: joint pair accuracy (recommended) vs. conditional false-flip rate.
6. **Primary hypotheses and multiplicity**: accept P1 + P2 with Holm, everything else secondary?
7. **Heuristic space**: review the lattice and the four post-pilot additions; add any heuristic you consider
   plausible *now*, before any confirmatory data exist.
8. **Generic initialisation**: descriptive only, or drop to save compute?
9. **Boundary study**: accept the near-boundary items and the human baseline as conditions for any strictness claim?
10. **Human study**: who annotates; you only adjudicate items whose labels you have seen.
11. **External extension**: which third benchmark, and your own heuristic spaces for HANS/ScoNe.
12. **Thresholds**: ε and δ for the sample-size target (proposed ε = 0.2, δ = 0.01 → k = 19); category Jaccard ≤ 0.34.
13. **Venue and timeline**, and how AI assistance will be declared.
