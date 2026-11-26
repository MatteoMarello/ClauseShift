# ClauseShift: identifiability-aware evaluation of rule reading in NLI

*Research summary for a prospective supervisor (two pages). Repository: github.com/MatteoMarello/ClauseShift.*

## 1. Question

When an NLI model reads a short rule document ("applicants must submit X; only applications received after 1 March
are covered"), does it notice the one clause that changes the answer? And can a benchmark tell a model that reads the
rule correctly from one that follows a plausible shortcut? The second question is the main research direction.

## 2. Completed, preregistered study (original results)

ClauseShift is a controlled diagnostic: 8,320 synthetic items in 4,160 minimal pairs from 8 fictional rule families.
Fourteen edit operators produce the pairs (exemptions, thresholds, date cutoffs, cross-references, negation, scope,
unstated attributes; near misses; surface invariances). Gold labels are computed from a rule specification. Train, dev
and test use disjoint families, and the test set adds unseen templates. Hypotheses, metrics and decision rules were
preregistered; all registered runs are complete (CPU only, DeBERTa-v3-xsmall fine-tuned with three seeds per
condition; four zero-shot NLI cross-encoders).

| Hypothesis (preregistered) | Outcome |
|---|---|
| H1: item accuracy overstates flip-pair accuracy by ≥ 10 points | **Supported** for all zero-shot models (gap 0.32–0.36; zero-shot flip-pair accuracy 0.07–0.30); failures are mostly insensitivity (61–77% of flip pairs answered identically) |
| H2: exception and boundary edits harder than negation | **Supported** for the three DeBERTa models; thresholds and dates ≤ 0.04 zero-shot |
| H3: training on complete pairs beats unpaired training | **Supported by the registered rule but fragile**: +0.021 [+0.006, +0.036]; a seed-level interval includes 0; reversed without NLI pre-training |
| H4: accuracy drops under vocabulary/template shift | **Not supported** (family difficulty confounds the split) |
| H5: hypothesis-only model near zero on flip pairs | Holds by construction |

Fine-tuning reaches flip-pair accuracy 0.80–0.82, with thresholds, dates and scope as the remaining failures.
Labels are generator-derived; a blinded LLM audit agreed on 112/112 sampled items. **No human validation yet.**

## 3. Main direction: benchmarks as test suites (exploratory results)

Idea: treat a benchmark as a test suite and plausible wrong readings of the task as *mutants* of the intended rule.
Report, for each mutant, how many items can tell it apart from the rule; group indistinguishable readings into
equivalence classes; compute minimum discriminating item sets; identify a model by item-level agreement with the
candidate readings under an explicit noise model. The components are known (mutation analysis in software testing,
outcome-based strategy classification in cognitive psychology); we did not find their combination applied to NLI
benchmarks. Everything below is **exploratory** (no confirmatory run yet).

- **ClauseShift:** 0 of 2,560 test items distinguish cross-reference resolution from an "article number" shortcut;
  only 23 and 17 items separate strict from non-strict threshold and date comparisons. Off-the-shelf NLI models agree
  with a three-line "topic + negation only" program on 96.6–98.3% of items (facts-in-premise format).
- **HANS:** lexical overlap is indistinguishable from "always entailment" (0 of 30,000 items); 3 items suffice to
  separate all distinguishable heuristic pairs. MNLI dev does separate them (9,579 items), but only 27 items
  contradict the overlap heuristic.
- **ScoNe:** the intended rule is indistinguishable from "exactly one scoped negation" (0 of 1,200); four zero-shot
  NLI models are identified as ignoring negation (agreement 0.92–0.98).
- **Evaluation metrics:** a single-input evidence criterion gives a perfect score to 432 of 648 candidate programs,
  including the lazy one; a joint (contrastive) criterion excludes the lazy program but still ties 24 programs with
  the rule on the pilot items. We state and prove the general reason: deleting a decisive clause moves the input into
  the region where the shortcut is correct.

## 4. Status of each claim

| Category | Claims |
|---|---|
| **Original results (preregistered)** | H1, H2, the fragile H3 effect, H4 not supported, on a new controlled benchmark |
| **Exploratory results** | Identifiability gaps in ClauseShift, HANS and ScoNe; program identification of models; metric audit; input-format effect (facts in the premise raise accuracy but lower accuracy on condition-dependent items, model-dependent); probes of cross-reference handling (one seed) |
| **Falsified or closed** | H4; "copy is not compare" (boundary errors are not caused by the value being a verbatim copy of the cutoff); "errors are program-like" and "errors are noise" (neither held under the negation symmetry); "year blindness" (a frozen replication did not meet its decision rule; direction closed) |
| **To be demonstrated** | That the test-suite view is useful beyond a transfer of known methods; a confirmatory study on newly built families (protocol v2 drafted, not frozen); human validation of labels; effect of counterfactual training on shortcut programs (weakest line, needs a seed-variance pilot first); behaviour of larger instruction-tuned models |

## 5. Limitations

Synthetic text and small encoders (DeBERTa-v3-xsmall fine-tuned on CPU); no human annotation; heuristic spaces are hand-written
and small; one benchmark (ScoNe) gave a null result for hidden gaps; several exploratory analyses use one seed.

## 6. Proposed next steps (3–6 months)

1. Independently written heuristic spaces for HANS, ScoNe and a third benchmark (no training).
2. Freeze the confirmatory protocol v2 and build new rule families; human validation of a label sample.
3. Seed-variance pilot, then decide whether the counterfactual-training question is testable.
4. Extend identification to an open-weight instruction-tuned model.

*Development was AI-assisted: code, analyses and drafts were produced with an AI coding assistant under the author's
direction, as disclosed in the repository. Personal contributions of the author: [to be completed by the author].*
