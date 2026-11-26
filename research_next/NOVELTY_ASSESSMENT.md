# Novelty assessment

Method: for each candidate contribution, the closest prior work found in this session (`LITERATURE_REVIEW.md`), what
that work already establishes, and what remains. "Not found" means not found by our searches (ACL Anthology, arXiv,
proceedings; 2026-11-25); it is not proof of absence. Several key papers were read only in part (reading status in
`RELATED_WORK_MATRIX.md`), so every "open" verdict below must be re-checked against full texts before writing.

| # | Candidate contribution | Closest prior work | Already established there | What would be new | Verdict |
|---|---|---|---|---|---|
| 1 | Zero-shot NLI models behave like an "obligation-spotting" program (98% item agreement) | HANS (heuristics as hypotheses); partial-input baselines (Poliak et al.; Feng et al. 2019); ScoNe (flawed-heuristic algorithms) | NLI models adopt shallow heuristics; partial-input baselines reveal artefacts | A *full-input, rule-subset* program that reproduces off-the-shelf models item by item (κ ≈ 0.97) on rule documents; the reinterpretation of "partial competence" scores | **Moderately new as a finding; not new as an idea.** Strong supporting result, not a paper by itself |
| 2 | Behavioural program identification over a lattice of partial rule readings, selected on held-out data | HANS; ScoNe; causal abstraction (mechanistic); decision-rule extraction | Comparing behaviour with candidate algorithms; testing algorithm implementation via interventions | A systematic lattice over rule-reading dimensions, held-out selection, and use across training regimes | **Incremental-to-moderate.** Needs careful positioning against ScoNe and causal abstraction |
| 3 | Benchmark identifiability audit (items that distinguish each heuristic from the rule) | Underspecification (D'Amour et al.); fair generalization tasks (Geiger et al. 2019); contrast sets; HANS | Equal test performance can hide different solutions; tests must expose the relevant distinctions | Counting distinguishing items per heuristic for an *existing* benchmark; showing a benchmark with near-miss controls had a zero-item dimension; using the audit to generate breaking probes | **Most promising.** Simple, general, testable on other benchmarks |
| 4 | Counterfactual pairs determine *which* shortcut is learned (Pilot 2) | Joshi & He 2022 (aligned perturbations; unperturbed features); Huang et al. 2020; Teney et al. 2020 | CAD helps on perturbed features and can amplify biases | Direct evidence that, at equal size, paired training teaches the minimal lexical difference of the pair (the digit) while unpaired training learns construction presence; both pass the in-distribution test | **Potentially new and surprising**, but currently one seed and post hoc test families; must be confirmed |
| 5 | Lazy program saturates sentence-level evidence hit@1; only joint (contrastive) criteria reject it | Hsia et al. 2024 (gaming ERASER); Hase et al. 2021 (OOD); Zhou et al. 2022 (ground-truth unit tests) | Removal-based metrics can be gamed and are OOD | Non-adversarial saturation caused by a universally necessary sentence; the observation that every single-input criterion tried (accuracy, invariance, hit@1, post-removal agreement) is satisfied by a no-condition program while joint criteria are not | **Small but clean and general.** A strong section, possibly a short paper |
| 6 | Expected-label-transition test for evidence | CEBaB; Kamahi & Yaghoobzadeh 2024; ground-truth attribution | Counterfactual effects as an evaluation target | Specification-derived transitions with an "insufficient" outcome on rule documents | **Incremental.** Depends on synthetic specifications |
| 7 | Adaptive identification of a model's program | Active testing; IRT-based efficient evaluation (tinyBenchmarks) | Adaptive item selection for accuracy estimation | Selection for *algorithm identification* | **Incremental**; nice demonstration, not central |
| 8 | Strict comparatives read as non-strict at boundaries | Numeracy-in-NLI work (EQUATE; Mahendra et al. 2025, abstract only) | Weak numeric reasoning | 100% of boundary errors are non-strict readings; needs a human baseline (convention) | **Unclear.** Must check full texts and run the human study before any claim |
| 9 | Legal-domain multi-clause benchmark | COMPACT, CLAUSE, ContractNLI, LegalBench | Real-text multi-clause benchmarks exist | – | **Not a contribution** |

## Which ClauseShift results are already in the literature

Minimal-pair evaluation, item-vs-pair accuracy gaps, the null-to-small effect of counterfactual pairs at equal size,
weak numeric reasoning in NLI, OOD problems of occlusion, and multi-clause legal benchmarks are all established. The
ClauseShift v2 study is a careful replication-and-diagnostic in a controlled domain, publishable as a technical
report; its novelty as a benchmark is limited (as the original review already said).

## Where the surprise is

The surprising part is not any single number but the combination: (i) a benchmark built specifically to defeat
shortcuts (near misses, invariance pairs, hypothesis-only control, disjoint families) still contained a dimension that
no item could test; (ii) four fine-tuned models with near-identical scores on that dimension run three different
programs once the dimension is probed; (iii) the training regime — pairs vs. single sides — decides which program is
learned, in a direction (pairs teach the edit token) that inverts the usual motivation for counterfactual data; and
(iv) the evaluation tools that were supposed to catch this (invariance, evidence metrics) reward the wrong programs.
Contribution 3 + 4 is the recommended core; 1, 5 and 8 are supporting evidence.

## Risks to novelty

- A paper on "benchmark identifiability" or "behavioural program identification" may exist under other names
  (e.g., "specification tests", "behavioural equivalence", "spurious-feature coverage"). A targeted search with these
  terms, and a read of ScoNe and causal-abstraction full texts, is required before writing.
- Shortcut discovery and benchmark auditing are active areas: UNMASK (arXiv 2608.09209, 2026; discovers and causally
  verifies spurious features in NLI classifiers), "Catching Shortcuts" (ACL 2025), a TruthfulQA surface-leakage audit
  (arXiv 2609.13003, 2026) and a shortcut-learning analysis in Findings of EMNLP 2024 were found as abstracts or
  summaries only. They must be read before claiming contribution 3; the distinguishing point to verify is whether any
  of them counts, per hypothesised heuristic, the items that separate it from the intended rule.
- The synthetic setting may make reviewers see the shortcut as a dataset bug. The framing must be methodological:
  the audit is general, and the bug was found by it.
