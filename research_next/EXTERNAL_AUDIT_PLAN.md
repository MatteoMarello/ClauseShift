# External identifiability audit — plan (committed before any computation on the external data)

Purpose: test whether the identifiability audit is a general method, by applying it to public benchmarks whose
candidate heuristics are defined in the original papers, independently of any model prediction. A null result (no
hidden indistinguishable pairs, good coverage) is a valid outcome and will be reported as such.

Honesty note: the author of this plan already knows the published headline results of HANS (MNLI-trained models
predict "entailment" on most HANS items) and ScoNe (MNLI-trained models struggle with scoped negation). The heuristic
spaces below are taken from the papers' own descriptions plus logically minimal alternatives; they are fixed here
before running any audit code or looking at item-level predictions.

## Benchmarks

| Benchmark | Source | Licence | Items used | Model predictions |
|---|---|---|---|---|
| HANS (McCoy, Pavlick & Linzen, 2019) | github.com/tommccoy1/hans | MIT | evaluation set, 30,000 items (30 subcases × 1,000) | published prediction files in the repository (BERT, ESIM, decomposable attention, SPINN); optionally the ClauseShift zero-shot NLI models on a stratified subsample |
| ScoNe-NLI (She, Potts, Bowman & Geiger, 2023) | github.com/selenashe/ScoNe | CC0 1.0 | test split, 6 splits × 200 items (contrast sets aligned by row index) | ClauseShift's four zero-shot NLI models (inference only, CPU) |

## Candidate heuristic spaces (fixed in advance)

### HANS (labels: entailment / non-entailment)
Defined from the paper's definitions of the three heuristics, computed from the text and the provided parses:
- `LO` lexical overlap: entailment iff every hypothesis word occurs in the premise.
- `SUB` subsequence: entailment iff the hypothesis is a contiguous subsequence of the premise.
- `CONST` constituent: entailment iff the hypothesis is the yield of a complete subtree of the premise parse.
- `ALL_E` constant entailment; `ALL_N` constant non-entailment.
- The intended rule is the gold label (no program is needed for the audit).
Normalisation: lower-case, final period removed, tokenisation on whitespace as in the released sentences.

### ScoNe (labels: entailment / neutral; contradiction is mapped to neutral for 3-way models)
Each item is described by its split (number of negations n, number of negations whose scope includes the lexical
item s) and its base label b (the label without negation, from `no_negation.csv` at the same row index).
Split features: no_negation (n=0, s=0); one_not_scoped (1, 0); one_scoped (1, 1); one_scoped_one_not_scoped (2, 1);
two_not_scoped (2, 0); two_scoped (2, 2). A "flip" exchanges entailment and neutral.
- `RULE` intended: flip iff s is odd (verified against the gold labels before use).
- `IGNORE` ignore negation: never flip.
- `PRESENCE` any negation flips: flip iff n ≥ 1.
- `PARITY_ALL` count negations ignoring scope: flip iff n is odd.
- `ANY_SCOPE` flip iff s ≥ 1 (ignores cancellation).
- `ONE_SCOPE` flip iff s = 1.
- `ALL_E`, `ALL_N` constants.
(The ScoNe paper's own flawed heuristics will be mapped onto these once its full text is read; any heuristic it
describes that is missing here will be added and reported as an addition.)

## Analyses (both benchmarks)

1. Separation matrix D[x, h] = 1 iff heuristic h disagrees with the gold label on item x; per-heuristic coverage
   c(h) = mean_x D[x, h]; distinguishing sets by subcase/split.
2. Pairwise distinguishability: number of items on which heuristics h and h' disagree; list indistinguishable pairs
   (zero items).
3. Minimal discriminating sets: smallest set of items such that every distinguishable pair of hypotheses
   (including the intended rule) is separated by at least one item; exact (by enumeration over item classes) where
   feasible, greedy otherwise.
4. Model identification: item agreement between each model's predictions and each heuristic; report ties as
   equivalence classes, never as a single "identified" heuristic.
5. Report whether the audit reveals anything not visible in the published aggregate metrics. If it does not, say so.
