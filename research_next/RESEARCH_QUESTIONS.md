# Candidate research questions

Each question is stated so that a specific result would falsify it. Evidence labels: **[E]** exploratory evidence
already in hand (post hoc, on analysed data); **[P]** pilot result (exploratory, predictions fixed in advance in
`PILOT_PLAN.md`); **[—]** no evidence yet.

The common thread is a shift of the unit of evaluation: from *how often* a model is right to *which program* it
behaves like, and from *how hard* a benchmark is to *which programs it can tell apart*.

---

## RQ1. Which program does the model run?

*Can the item-level behaviour of NLI models on rule documents be described by an explicit program from a small
lattice of partial or deviant rule readings, and do training regimes (zero-shot NLI, NLI-initialised fine-tuning,
generic-initialised fine-tuning, paired vs. unpaired) select different programs?*

- Operationalisation: 648 programs varying seven reading dimensions (threshold/date: ignore, non-strict, strict;
  scope; exemption: ignore / any category / read; cross-reference: ignore / article token / read; unstated
  attribute; negation). Program selected on dev, item agreement and Cohen's κ reported on held-out data.
- Falsified if: the best program's held-out agreement is not higher than that of the reference rule plus a
  pre-specified margin for any model class, or if the selected program is unstable across seeds of the same regime.
- Evidence [E]: zero-shot DeBERTa-base/RoBERTa-large with facts in the premise agree with the "topic + negation
  only" program on 96.6–98.3% of test items (κ 0.94–0.97). Generic-initialised fine-tuned models are best described
  by non-strict comparisons and ignored scope restrictions; NLI-initialised ones by the reference rule up to the
  non-identifiable cross-reference dimension.
- Why it matters: accuracy 0.53 and "flip-pair accuracy 0.30" sound like partial competence; "agrees with a program
  that never reads a condition on 98% of items" is a different, more useful finding.

## RQ2. Do benchmarks hide what they cannot identify, and do counterfactual pairs exploit it?

*If a benchmark contains no item that distinguishes a heuristic from the intended rule, do fine-tuned models adopt
the heuristic, and does training on complete minimal pairs make this more likely than training on single sides?*

- Operationalisation: identifiability count per heuristic (items on which heuristic and rule disagree); probes that
  break the non-identified heuristic (cross-reference to Article 1 naming *another* category); false-flip rate.
- Falsified if: false-flip rates on the breaking probes are low (< 0.2) for fine-tuned models, or not higher after
  paired than after unpaired training across seeds.
- Evidence: [E] 0 of 2,560 test items distinguish "resolve the cross-reference" from "react to the digit 1";
  pairing's largest per-operator gain is on cross-references. [P] Pilot 2: reference-specific excess of false flips
  in 12/12 model×family cells; NLI-init paired > unpaired by +0.17 to +0.36; the pre-specified inline control failed
  in the pre-specified family (one seed; two families post hoc). See `PILOT_RESULTS.md`.
- Why it matters: counterfactual pairs are motivated as a cure for spurious features. If the minimal difference of
  an edit type has a single lexical realisation, the pair isolates that token perfectly and may *install* a shortcut.

## RQ3. Is reference resolution composed with exemption semantics when the test is fair?

*When training shows the cross-reference construction with some content (e.g. references that restrict scope) and
inline exemptions, but never cross-referenced exemptions, do models handle cross-referenced exemptions?*

- Operationalisation: a factorial generator (construction × content × distance × target article) with a held-out
  combination, satisfying Geiger et al.'s (2019) fairness condition.
- Falsified (in the "models compose" direction) if accuracy on the held-out combination is within a pre-specified
  margin of the in-distribution combinations; (in the "models do not compose" direction) if it is near the
  inline-exemption level.
- Evidence: [—] (the original hold-out is unfair; see audit §1).

## RQ4. Do evidence metrics certify partial programs?

*Do sentence-level evidence metrics assign high scores to programs that ignore the decisive clauses, and does a test
based on specification-derived expected label transitions, computed on a fixed item set, reject them?*

- Falsified if: the lazy program obtains a low hit@1, or the transition test fails to separate it from models that
  read conditions.
- Evidence [P]: the lazy program obtains hit@1 = 1.00 (300/300 top sentences are the obligation) while ignoring
  every condition. On a fixed item set, a single-input transition score also gives it 1.00 on decisive removals; the
  joint score (correct before and after removal) gives it 0.00, against 0.65–0.78 for NLI-init fine-tuned models.

## RQ5. How many items does it take to know?

*Can adaptive, information-maximising item selection identify a model's program with far fewer items than random
sampling?*

- Evidence [P]: 13–47 items instead of a median of 75–155 random items for six of seven models; no gain for one
  model that the lattice describes poorly (139 vs. 155).
- Falsified if: on new models and families, adaptive selection does not reduce the number of items needed by a
  pre-specified factor.
- Status: a by-product, useful for evaluating large models cheaply; not a standalone paper.

---

## Directions from the brief, re-assessed

- **Direction A (compositional generalization)** becomes RQ3, with a fair design. The original "0.04 on unseen
  cross-references" is not usable as evidence of non-compositionality (audit §1).
- **Direction B (evidence faithfulness)** becomes RQ4. Novelty is narrower than it first looked: OOD removal,
  metric gaming and ground-truth attribution tests exist; the new element is structural saturation by a
  universally necessary sentence and the lazy-program sanity check.
- **Direction C (neuro-symbolic)**: a symbolic reader trivially solves synthetic templates; as a contribution it is
  weak. It survives as a *control* (reference normalisation) inside RQ3, and the program lattice of RQ1 is itself a
  symbolic instrument.
- **Direction D (external validity)**: needed for any strong claim but not feasible as the main line now (see
  `NOVELTY_ASSESSMENT.md`, `PUBLICATION_ROADMAP.md`). A concrete, cheap version exists: test whether a lazy
  "obligation-spotting" heuristic explains model behaviour on a public real-text benchmark with a compatible label
  set (ContractNLI, CC BY 4.0).
