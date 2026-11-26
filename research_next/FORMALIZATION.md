# Formalisation of the identifiability audit

Scope: definitions that make the audit precise and computable, plus the few results that change what one does in
practice. Vocabulary is aligned with mutation analysis (software testing) and outcome-based strategy classification
(cognitive psychology), where the same objects already exist (`NOVELTY_VERIFICATION.md`).

## 1. Objects

- **Inputs and labels.** X is the input space (document–hypothesis pairs), Y a finite label set, |Y| = c.
- **Benchmark.** A finite multiset B ⊆ X of evaluation items.
- **Intended rule.** r : X → Y, the labelling function the benchmark is meant to test. In ClauseShift r is computed
  from the specification (`gold_label`); in HANS and ScoNe it is given by the gold labels, i.e. known only on B.
- **Candidate heuristic space.** H = {h₁, …, h_m}, functions X → Y representing plausible *wrong* readings of the
  task (in mutation-analysis terms: mutants of r). Requirement: H is specified from the task description and the
  benchmark's construction, **before and independently of any model's predictions**. Let H̄ = H ∪ {r}.
- **Model.** A trained model induces a prediction function m : X → Y; we observe it only on the items we query.

## 2. Distinguishing sets, separation matrix, coverage

- **Distinguishing set** of h on B: D_B(h) = {x ∈ B : h(x) ≠ r(x)}.
- **Separation (kill) matrix** S ∈ {0,1}^{|B|×m}, S[x, h] = 1[h(x) ≠ r(x)].
- **Coverage** of h: κ_B(h) = |D_B(h)| / |B|. In mutation terms, h is *killed* by B iff |D_B(h)| ≥ 1, and the
  *mutation score* of B is the share of non-equivalent h that are killed.
- **Count, not only fraction.** Identification under noise depends on |D_B(h)|, the absolute number of
  distinguishing items (Section 5). A benchmark with κ = 0.007 but 20,000 items can be adequate; one with κ = 0.009
  over 2,560 items (23 items, ClauseShift's strict-vs-non-strict thresholds) may be marginal for noisy models.

## 3. Pairwise distinguishability and equivalence classes

- **Pairwise distinguishing set**: Δ_B(h, h') = {x ∈ B : h(x) ≠ h'(x)}, for h, h' ∈ H̄.
- **Behavioural equivalence on B**: h ~_B h' iff Δ_B(h, h') = ∅. This is an equivalence relation; its classes
  H̄/~_B are the most a benchmark can tell apart. Equivalence on B does **not** imply equality on X (HANS: lexical
  overlap ~_B constant entailment, but they differ on most MNLI items).
- **Pairwise separation matrix** P ∈ {0,1}^{|B|×(|H̄| choose 2)}, P[x, {h,h'}] = 1[h(x) ≠ h'(x)]; S is the
  sub-matrix of pairs involving r.
- **Subsumption** (from mutation analysis): h subsumes h' on B if ∅ ≠ D_B(h) ⊆ D_B(h'): every item that exposes h
  also exposes h'. Subsumed heuristics add no auditing burden once h is covered.
- **Unions of benchmarks.** Δ_{B₁∪B₂} = Δ_{B₁} ∪ Δ_{B₂}, so identifiability can hold for a union and fail for each
  part. This is the formal content of the HANS + MNLI observation.

## 4. Minimum discriminating sets

- **Problem.** Find the smallest T ⊆ B such that every distinguishable pair is separated: for all h ≠ h' in H̄ with
  Δ_B(h, h') ≠ ∅, there is x ∈ T with h(x) ≠ h'(x). This is a **minimum hitting set** (dually, set cover) over the
  family of pairwise distinguishing sets — the test-suite minimisation problem of software testing. NP-hard in
  general; greedy gives a (1 + ln N) approximation, N = number of pairs.
- **Why it is easy here.** Define the signature σ(x) = (h(x))_{h ∈ H̄}. Items with the same signature are
  interchangeable for discrimination, so the problem reduces to the distinct signatures, of which there are few
  (HANS: 6; ScoNe: 12). Exact search over signature subsets is then trivial (results: 3 items for HANS, 3 for ScoNe).
- **For noisy models one item per pair is not enough**: the right object is a *multicover* — each pair separated by
  at least k items, with k from Section 5. This is still a covering integer programme over signatures.
- **Design use.** When a pair has Δ_B = ∅ (ClauseShift's article-token cross-reference shortcut; ScoNe's "exactly one
  scoped negation" vs. parity), no subset of B helps: new items must be generated, and the signature tells which
  property they need (e.g. a cross-reference naming another category; three scoped negations).

## 5. Identification of a model

- **Agreement**: A_B(m, h) = (1/|B|) Σ_x 1[m(x) = h(x)]. Accuracy is A_B(m, r).
- **Noise model** (outcome-based strategy classification): the model follows one h* ∈ H̄ and deviates with
  probability ε, uniformly over the other c − 1 labels. Likelihood
  L(h) = Π_x (1 − ε)^{1[m(x)=h(x)]} (ε/(c−1))^{1[m(x)≠h(x)]}. Posterior w(h) ∝ prior(h)·L(h). The identified set is
  the smallest set of equivalence classes holding a chosen share of posterior mass; ties under ~_B are reported as
  classes, never broken arbitrarily.
- **How many distinguishing items are needed (the one result used for design).** Let the model follow r with error
  rate ε, and let h ≠ r. On the k items of D(h), the per-item difference Z = 1[m = r] − 1[m = h] has mean
  μ = (1 − ε) − ε/(c − 1) ≥ 1 − ε − ε and lies in [−1, 1]. By Hoeffding's inequality, the probability that h agrees
  at least as often as r on those items is at most exp(−k μ² / 2). To keep it below δ:
  **k ≥ 2 ln(1/δ) / μ².** Examples (c = 3, δ = 0.01): ε = 0.1 → k ≥ 13; ε = 0.2 → k ≥ 19; ε = 0.3 → k ≥ 31. The
  same bound applies with the roles of r and h exchanged. This turns "is this heuristic covered?" into a number.
  ClauseShift has 23 and 17 items separating strict from non-strict thresholds and dates: enough for ε ≤ 0.2 models,
  borderline beyond; 0 items for the cross-reference token shortcut.
- **Adaptive selection.** Choosing the next item to maximise the expected information gain about h* is Bayesian
  optimal experimental design; under the symmetric noise model the gain equals the entropy of the posterior
  predictive label distribution minus a constant (Pilot 3).

## 6. What behavioural identification does and does not show

1. It is **relative to H**: the best h may be a poor description (agreement close to accuracy for strong ClauseShift
   models). The residual 1 − max_h A(m, h) must always be reported.
2. It is **relative to B**: models are identified only up to ~_B; a different benchmark can split a class.
3. It is **behavioural**: two networks with different internal computations that produce the same outputs on B are
   indistinguishable by this method. "The model behaves like program h on B" never implies "the network computes h".
   Mechanistic claims require interventions on internal states (causal abstraction, Geiger et al. 2021).
4. It is **selection-sensitive**: choosing h from a large H on the evaluation data overstates fit; select on held-out
   data or report the number of candidates.
5. H must be written before seeing model predictions; otherwise the audit can be tuned to the model.

## 7. What the formalism buys (and what it does not)

Useful: an explicit, computable notion of *what a benchmark cannot test* (equivalence classes), a count-based target
for *how much* testing is enough (Section 5), and a cheap exact construction of small diagnostic sets (Section 4).
Not needed: probabilistic coverage theory, general complexity results, or learning-theoretic identifiability — the
hypothesis spaces are small and finite, so enumeration suffices.
