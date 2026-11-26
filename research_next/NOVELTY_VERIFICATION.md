# Novelty verification (2026-11-26)

Question: does a methodology equivalent to the proposed "identifiability audit" already exist? The proposal has six
components: (1) an explicit space of candidate heuristic programs derived from the intended rule; (2) a binary
separation matrix (items × heuristics, 1 if the heuristic disagrees with the intended label); (3) per-heuristic
coverage; (4) pairwise indistinguishable hypotheses (equivalence classes); (5) minimum discriminating item sets;
(6) model identification by item-level agreement under a noise model.

Reading status follows `LITERATURE_REVIEW.md`: [FT] main text read verbatim (by the assistant or an automated
reader; partially summarised parts are flagged), [ABS] abstract/snippet only. Absence of a match in our searches is
**not** evidence that no equivalent work exists; it only bounds what we checked.

## 1. Verdict

**The methodology is not new. Its components exist, mostly outside NLP; what we could not find is their combined
application to NLP benchmark design.** Concretely:

| Component | Where it already exists | Status of our check |
|---|---|---|
| (1) Candidate programs derived from a reference | *Mutation analysis* in software testing (mutants of a reference program); HANS and ScoNe define heuristics/algorithms by hand for one phenomenon each | HANS [FT], ScoNe [FT]; mutation literature [ABS/secondary] |
| (2) Separation (kill) matrix | Mutation analysis: tests × mutants "kill" matrix; UNMASK builds a feature-firing matrix on training data (not disagreement with the intended rule) | UNMASK [FT, partly summarised] |
| (3) Coverage per heuristic | Mutation score; HANS/ScoNe give per-subset accuracy; UNMASK gives per-feature coverage | as above |
| (4) Indistinguishable hypotheses | Equivalent mutants and mutant subsumption (Ammann et al.); in cognitive psychology, strategy classification is known to fail when strategies predict the same choices; underspecification (D'Amour et al.) at the level of predictors | psychology and SE sources [ABS/secondary]; underspecification [FT, ~17% verbatim] |
| (5) Minimum discriminating sets | Test-suite minimisation as minimum set cover / hitting set (Yoo & Harman survey); optimal experimental design for model discrimination | [ABS/secondary] |
| (6) Identification by item-level agreement with a noise model | *Outcome-based strategy classification* (Bröder & Schiffer 2003; Glöckner 2009 MM-ML): decision strategies classified from choice patterns on diagnostic item types assuming a constant execution-error rate — this is mathematically the same model as our Pilot 3 likelihood | [ABS/secondary] |
| Benchmark adequacy via mutants of the reference solution | Code-LLM benchmarks: SWE-Proof and TEA-Bench-BR report surviving mutants as evidence that a specification/test suite does not distinguish wrong solutions | [ABS, search summaries only] |

Within NLP specifically:
- **HANS** [FT]: three heuristics with a stated nesting; models identified from per-subcase accuracy; no separation
  matrix, no pairwise analysis, no minimal set. The paper does not discuss that lexical overlap is indistinguishable
  from constant entailment on HANS (appendix D notes models "generally outputting entailment").
- **ScoNe** [FT]: four explicit algorithms (two correct, two flawed); split design separates the flawed ones; no
  matrix, no item-level identification; the two "correct" algorithms are acknowledged as both solving the task.
- **BERTs of a feather; Linear connectivity** [FT, partly]: models with equal in-distribution accuracy follow
  different strategies on HANS subsets; identification by subset accuracy, not item-level agreement.
- **Causal abstraction** [FT, ~30% verbatim]: algorithm identification by interventions on internal states — a
  stronger, mechanistic notion; not behavioural.
- **Friedman et al. 2022; UNMASK 2026** [FT]: discover shortcut features from data; neither measures what an
  *evaluation set* can distinguish relative to the intended rule; neither selects discriminating sets.
- **Active testing; tinyBenchmarks; IRT leaderboards** [FT/ABS]: adaptive or reduced item selection to estimate risk,
  accuracy or latent ability — not to identify a decision rule.
- **"Catching Shortcuts" (reported as ACL 2025)**: not found after three searches; status unknown. Closest titles
  found: "Short-circuiting Shortcuts" (CoNLL 2025), "Supervised and Unsupervised Probing of Shortcut Learning"
  (Findings ACL 2025) [ABS].

## 2. Consequences for the contribution

- Claiming a "new methodology" would be wrong. The defensible claim is a **transfer**: mutation analysis of the task
  specification plus outcome-based strategy classification, applied to NLP benchmarks, with concrete findings that
  aggregate metrics did not show.
- The transfer must cite and use the existing vocabulary (mutant, kill matrix, equivalent mutant, subsumption,
  minimisation; strategy classification, diagnostic items), not invent new names for them.
- What is specific to NLP and appears unexamined: (a) the heuristic "mutants" of an NLP task are *readings of the
  input* (ignore a clause, read "more than" as "at least", key on a token), so equivalence depends on the benchmark's
  generative design, not on program semantics; (b) identifiability can be a property of a *union* of benchmarks (HANS
  separates lexical overlap from the rule, MNLI dev separates it from constant entailment; neither alone suffices);
  (c) training data design (counterfactual pairs) may select *which* non-identified mutant a model implements.

## 3. Searches run (alternative terminology)

test distinguishability; hypothesis discrimination; behavioural equivalence; diagnostic test selection; specification
testing; mutation testing (NLP, benchmarks, equivalent mutants); shortcut coverage; model identification / strategy
classification; optimal experimental design for model discrimination. Results that matter are listed above; the rest
concern deep-learning mutation testing (mutating models, not specifications), neuron coverage, and code benchmarks.

## 4. What remains unverified

- Full texts of the mutation-analysis and strategy-classification sources (definitions taken from secondary
  descriptions).
- "Catching Shortcuts".
- Whether any NLP benchmark paper reports surviving "heuristic mutants" for its own test set (the closest analogue,
  SWE-Proof/TEA-Bench-BR, is for code).
