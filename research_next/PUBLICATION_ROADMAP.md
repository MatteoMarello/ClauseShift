# Publication roadmap

No submission, preprint or upload will be made without the author's explicit approval. Nothing below promises
acceptance. Dates were checked on 2026-11-25 on the official pages cited; anything marked "not yet announced" must be
re-checked.

## 1. Verified venue facts

| Venue | Facts (source) | Fit |
|---|---|---|
| **ACL 2027**, Kyoto, Aug 17–22, 2027 (main conference Aug 20–22) | ARR submission deadline **January 4, 2027**; commitment and notification TBA (2027.aclweb.org, read 2026-11-25). A "Limitations" section is mandatory; preprints may not be posted in the month before submission (call as reported on LINGUIST List; re-check the official call) | Main/Findings: too early (see §3) |
| **ACL Rolling Review** | 2026 cycles: Mar 16, May 25, Aug 3, Oct 12. ACL 2027 is listed with final ARR submission "January, 2027"; no 2027 cycles published yet (aclrollingreview.org/dates, read 2026-11-25) | Later 2027 cycles (EMNLP 2027) not yet announced |
| **ACL 2027 Student Research Workshop** | Call not yet published. For reference, ACL 2026 SRW: direct submission March 18, 2026; pre-submission mentorship February 4, 2026 (acl2026-srw.github.io) | Plausible target if the 2027 call keeps similar dates — **unverified** |
| **EACL 2027 SRW** | Direct submission December 15, 2026; mentorship deadline November 6, 2026 (2027.eacl.org/calls/srw, search snippet; not opened in full) | Too soon for confirmatory results |
| **BlackboxNLP** | 2026 edition at EMNLP 2026 (Budapest, Oct 28, 2026), paper deadline July 17, 2026 (blackboxnlp.github.io/2026) — passed; 2027 edition not yet announced | Best topical fit for RQ1/RQ4 (analysis and interpretation) |
| **NLLP** (Natural Legal Language Processing) | 2026 edition at EMNLP 2026, submission August 11, 2026 (CfP on list.sigdial.org) — passed; 2027 not yet announced | Fit for the legal-text framing and external validity |
| Insights from Negative Results; GenBench | Not verified for 2027 | Possible venues for the null/fragile pairing results or the generalization design |
| arXiv technical report | Any time, with approval; respect ARR anonymity windows | Appropriate for the current, completed ClauseShift study |

## 2. What exists now vs. what each level needs

Verified now (exploratory unless stated): the registered ClauseShift study (preregistered, complete); lazy-reader
equivalence of zero-shot models; identifiability gap for cross-references; boundary errors are non-strict readings;
hit@1 saturation by a lazy program; adaptive identification efficiency; Pilot 2 probe results (`PILOT_RESULTS.md`).

| Level | Realistic? | Missing evidence |
|---|---|---|
| Technical report / preprint of ClauseShift v2 | **Yes, now** (after the author reviews it) | Human validation is pending and must be stated as such |
| Student Research Workshop paper (ACL 2027 SRW, if dates are similar) | **Plausible** within 3–4 months | Confirmatory replication on new families with new seeds (protocol ready); Part A–B human annotation; one focused claim (RQ1+RQ2 or RQ4) |
| Analysis workshop paper (BlackboxNLP 2027 / NLLP 2027) | **Plausible** within ~6–8 months | As above, plus: lattice fixed before confirmation; a real-text component or an explicit scope statement; LLM evaluation (open-weight 7–8B, needs a GPU) to show the finding is not specific to small encoders |
| Findings / main conference | **Uncertain**; not before mid-2027 | Everything above, plus: generalization beyond templates (a second, more natural generator or human-written minimal pairs), several model families incl. instruction-tuned LLMs, the fair compositional test (RQ3), and a convincing answer to "isn't this HANS/ScoNe for rules?" |

ACL 2027 (Jan 4, 2027) is not recommended: the confirmatory study, human validation and LLM evaluation cannot be done
properly in five weeks, and an under-powered submission would spend the result.

## 3. Candidate paper (only if the confirmatory study supports it)

**Working title.** *Which Program Is Your Model Running? Identifiability-Aware Evaluation of Rule Application with
Minimal Pairs*

**Preliminary abstract (hypothetical; bracketed claims are not yet confirmed).** Accuracy on minimal-pair benchmarks
tells us how often a model is right, not which procedure it follows. We describe models of rule application by the
program, from a lattice of partial and deviant rule readings, that best reproduces their item-level behaviour, and we
measure benchmark *identifiability*: how many items separate each program from the intended rule. On ClauseShift,
three off-the-shelf NLI models agree on 96–98% of items with a program that only checks whether the claimed
obligation is stated, while their aggregate scores suggest partial competence; fine-tuned models adopt non-strict
comparisons. A benchmark designed with near-miss controls still contains a dimension with zero identifying items,
and [fine-tuned models exploit it, more so after training on counterfactual pairs]. A sentence-level evidence metric
certifies the program that reads no condition. We release the lattice, the identifiability audit and adaptive
probes that identify a model's program with [~5×] fewer items.

**Contributions (to be kept only if confirmed).**
1. Behavioural program identification for rule application, selected on held-out data.
2. A benchmark identifiability audit, and the finding that a carefully controlled benchmark had an unidentified
   dimension.
3. Evidence on whether counterfactual pair training installs edit-token shortcuts.
4. A non-adversarial sanity check showing saturation of sentence-level evidence metrics.

**Structure.** 1 Introduction; 2 Related work (heuristics as hypotheses, causal abstraction, underspecification,
CAD, evidence metrics, legal benchmarks); 3 ClauseShift and the program lattice; 4 Identifiability; 5 Program
identification results; 6 Shortcut probes and pairing; 7 Evidence metrics; 8 Adaptive identification;
9 Limitations (mandatory); 10 Ethics and AI-assistance statement.

**Experimental plan.** `EXPERIMENT_PROTOCOL.md`.

## 4. AI assistance and authorship

Venues increasingly require a statement on AI-assisted writing and coding; check the policy of the chosen venue. The
current repository statement ("produced with substantial assistance from an AI coding assistant, working from the
author's instructions") must be kept accurate: the author's own contributions (decisions, annotation, analyses
re-derived by hand, writing) should be documented as they happen so that the statement can name them truthfully.
