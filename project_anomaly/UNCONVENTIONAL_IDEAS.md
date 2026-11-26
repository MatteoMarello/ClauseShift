# Unconventional ideas — and the conventional ones we are trying not to default to

## 1. What a language model would most likely propose for this brief

Listed so that we can recognise them and require specific evidence before pursuing any of them:

1. Graph-enhanced Transformer over a clause graph (articles as nodes, references as edges).
2. Hierarchical attention (sentence → article → document).
3. External memory / key-value store for definitions and references.
4. Neuro-symbolic pipeline: parse rules into logic, solve with a reasoner.
5. Contrastive learning on minimal pairs (pull invariant pairs together, push flip pairs apart).
6. Mixture of experts per edit operator.
7. A new attention variant ("reference-aware attention", "symbolic attention").
8. Generic counterfactual augmentation at scale.
9. Self-verification / chain-of-thought / LLM-as-judge consistency loops.
10. Curriculum learning from easy to hard operators.
11. Adversarial training against the lazy program.
12. Calibration or uncertainty layers ("know when insufficient").

Why we do not start from them: each adds capacity or machinery to fix a failure whose *cause* we have not isolated.
The audit already shows that several "failures" are properties of the data and the evaluation (identifiability gaps,
saturated metrics), which no architecture fixes. They become admissible only if an isolated mechanism points to them.

## 2. Independent hypotheses, by discipline (generated before comparing them)

| Discipline | Structure it understands well | Hypothesis about NLP systems it suggests | Falsifiable prediction | Verdict |
|---|---|---|---|---|
| Formal languages / compilers | Identifier binding vs. string identity; lexical scope | Models conflate *string identity* with *semantic satisfaction*: a value that appears verbatim in a condition is treated as matching it | Boundary errors disappear when the equal value is written in a different surface form | **Pilot 1** |
| Abstract algebra / symmetry | Group actions, invariants, equivariance | The task has an exact label symmetry — negating the claim permutes entailed↔contradicted and fixes insufficient. Errors that are *covariant* under it are consistent wrong beliefs; non-covariant errors are noise | A large share of fine-tuned errors is covariant (systematic), while zero-shot errors are not; symmetrised decoding helps only when errors are non-covariant | **Pilot 2** |
| Coding theory | Repetition codes; decoding gains only with independent errors | Querying a model on several symmetric views is a repetition code; its gain is bounded by error correlation across views | Gain from symmetrisation ≈ predicted from the measured error covariance | Folded into Pilot 2 |
| Statistical mechanics / dynamical systems | Order parameters, abrupt changes | During fine-tuning the identified program changes in jumps, not smoothly, and in a reproducible order | The best-fitting lattice program changes at a few steps; dimensions are acquired in a fixed order | **Pilot 3 (conditional on budget)** |
| Cognitive psychology | Strategy identification; inertia | Models fail by inertia: decisive edits leave answers unchanged (A10). Inertia is measurable as the probability mass that does not move | Insensitivity, not confusion, dominates across model families | Already observed; descriptive |
| Information theory / MDL | Shortest description among equally good hypotheses | Among programs equivalent on the training data, SGD picks the one with the shortest description in token features (digit cue < category comparison) | Probe-identified programs rank lowest in a description-length measure | Hard to make non-circular; deferred |
| Experimental design | Discriminating experiments | Benchmarks are designed for difficulty, not discrimination | Already the identifiability line (research_next) | Not repeated here |
| Neuroscience / variable binding | Role–filler binding | Category matching fails when fillers are lexically close (vehicles) | Errors scale with lexical similarity of category names | Observed (vehicles); confound for others |
| Control theory | Feedback, steady-state error | A model that is "corrected" on one dimension drifts on another (format fix ↓ condition reading, A1) | Interventions that raise accuracy move agreement towards the lazy program | Observed (A1) |
| Measurement theory | Validity: what a metric measures | Single-input criteria are satisfiable by degenerate programs; only contrastive criteria are not | Every single-input criterion can be maximised by a program that reads no condition | Observed (research_next) |
| Constraint satisfaction | Joint decoding under constraints | Pair constraints could correct predictions — but only with knowledge of which pairs flip, unavailable at test time | — | Rejected (not deployable) |
| Physics (experimental) | Null tests, blinding, control of systematics | The "irrelevant article" probe is a null test that models fail at very different rates with equal accuracy (A3) | Null-test failure rates are not predicted by accuracy | Observed; needs seeds |

## 3. Our own direction not in the brief (from a concrete anomaly)

**"Copy is not compare."** A2: at an exact numeric or date boundary the case value and the cutoff are written as the
*same string*. Every fine-tuned error there reproduces the "satisfied" label. Elsewhere in the training data a verbatim
match between case and condition is exactly the signal that a condition *engages* the case: a matching place name
satisfies a scope restriction, a matching category triggers an exemption. The hypothesis is that the models use
string identity as a stand-in for the relation the condition expresses, so that at the boundary "more than 50"
followed by "50" reads as a match rather than as a failed comparison. If so, what looks like a failure of strict
comparison is a failure to separate identity of form from relation of value. It is small, falsifiable with a
surface-form change that does not alter meaning, and, if true, would apply to any model reading rules with numbers,
dates or names. This direction did not come from the seeds in the brief.
