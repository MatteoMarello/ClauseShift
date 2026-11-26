# External identifiability audit — results and interpretation

Plan (heuristics fixed before computation): `EXTERNAL_AUDIT_PLAN.md`. Generated tables:
`results/external/EXTERNAL_AUDIT.md`, `results/external/external_audit.json`, `results/external/hans_mnli_union.json`.
Scripts: `scripts/external_audit.py`, `scripts/scone_zero_shot.py`, `scripts/hans_mnli_union.py`.
Licences: HANS MIT; ScoNe CC0 1.0; MNLI validation (GLUE copy) used locally for counts only, not redistributed.
All analyses exploratory. Model predictions on HANS are the four prediction files published with HANS; on ScoNe, the
four ClauseShift zero-shot NLI models (inference only).

## Answers to the four questions

**1. Are there indistinguishable pairs of strategies?** Yes, in both benchmarks.
- HANS: lexical overlap (LO) ≡ constant entailment — 0 of 30,000 items separate them, because every HANS hypothesis
  consists of premise words. HANS separates LO from the gold rule (15,000 items) and from subsequence/constituent,
  but cannot tell whether a model applies lexical overlap or simply predicts "entailment" on HANS-like inputs. The
  HANS paper does not discuss this (it relies on MNLI training statistics to argue for heuristic adoption).
- ScoNe: the intended rule (flip iff an odd number of negations scope over the lexical item) ≡ "flip iff exactly one
  scoped negation" — 0 of 1,200 items separate them. These correspond to the paper's two "correct" algorithms
  (ScoNe-Bool and ScoNe-Count), which the authors present as both solving the task; the audit makes explicit that
  ScoNe cannot test the difference, which only appears with three or more scoped negations.

**2. Are some heuristics poorly covered?**
- ScoNe: "any scoped negation flips" (ignoring cancellation) is exposed by a single split (two_scoped; 200 items,
  coverage 0.167); all other flawed strategies by two or three splits.
- MNLI validation-matched (the in-distribution set that HANS-style claims rely on): only 236 of 9,815 items have full
  lexical overlap, and only **27** of them are non-entailment. The lexical-overlap heuristic, read as "full overlap ⇒
  entailment", is contradicted by the gold label on 27 items (0.28%); with the bound of FORMALIZATION §5 this is
  enough to identify a low-noise model (k ≥ 13 for ε = 0.1) but not by a wide margin.
- HANS: every hypothesis in our space is exposed by ≥ 9,000 items; coverage is not a problem.

**3. Does the method reveal gaps not visible in aggregate metrics?**
- HANS: **partly yes.** The aggregate pattern (near-0 accuracy on non-entailment subsets) is read as "the model
  adopted the heuristic"; the audit shows HANS alone licenses only "lexical overlap *or* constant entailment". The
  claim needs the union HANS ∪ MNLI: MNLI dev separates LO from constant entailment on 9,579 items, HANS separates LO
  from the rule on 15,000. Neither benchmark alone identifies the heuristic. All four published models fall in the
  LO ≡ ALL_E class on HANS (agreement 0.927–0.988).
- ScoNe: **mostly no.** Item-level identification places all four zero-shot NLI models in the ignore-negation class
  (agreement 0.922–0.978, no ties), which the split-level accuracy profile already suggests (the paper reports this
  profile for its MNLI-only models and attributes the ignore-negation pattern explicitly only to InstructGPT). The
  one non-obvious point is the equivalence of the two correct algorithms. This is a null result for "hidden gaps"
  and is reported as such.

**4. Can small, more discriminating sets be built?** Yes. Exact minimum hitting sets over item signatures: **3 items**
separate all 14 distinguishable hypothesis pairs on HANS (of 30,000 items), and **3 items** separate all 33 on ScoNe
(of 1,200). For noisy models the relevant object is a multicover (each pair separated by k items, k ≈ 13–31 for
ε = 0.1–0.3), still two orders of magnitude smaller than the benchmarks.

## What this does and does not show

- It shows the audit is **general and cheap**: definitions from the papers, no training, a few seconds of compute.
- It does **not** show that the published conclusions are wrong. HANS's authors use MNLI evidence that resolves
  the LO-vs-constant ambiguity; ScoNe's authors design the splits to separate the flawed algorithms they propose.
- The value demonstrated is diagnostic: making explicit, with counts, which claims a benchmark can support alone,
  which need a second benchmark, and which items would be needed to test the rest.
- Heuristic spaces were small and hand-specified; a richer space (e.g. partial-overlap thresholds for HANS, other
  scope heuristics for ScoNe) could reveal more equivalences. This is a limitation, not a hidden success.
