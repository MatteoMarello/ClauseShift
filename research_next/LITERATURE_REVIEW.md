# Literature review for the next ClauseShift contribution

Date of search: 2026-11-25. Sources: ACL Anthology, arXiv, NeurIPS/ICLR/ICML proceedings, authors' project pages.
This review extends `docs/LITERATURE_REVIEW.md` (which covers contrast sets, CAD, HANS, CheckList, ContractNLI,
LegalBench, ConditionalQA, RuleTaker, ShARC, ERASER and annotation artefacts) and focuses on the hypotheses that
emerged from the audit and pilots (`SCIENTIFIC_AUDIT.md`, `PILOT_RESULTS.md`).

## Reading status (honest accounting)

Every entry in `RELATED_WORK_MATRIX.md` carries one of these tags.

- **[FT-self]** full text of the main body read directly in this session (appendices not read unless stated).
- **[FT-partial]** full text read by an automated reader in this session, with only part of the text extracted
  verbatim and the remainder summarised by a model. Numbers from the summarised part are not used here.
- **[ABS]** abstract, landing page or search snippet only. No claim beyond the abstract is made.
- **[PRIOR]** cited in the original `docs/LITERATURE_REVIEW.md`; not re-read in this session.

| Work | Status in this session |
|---|---|
| Singh et al., COMPACT (EACL 2026) | [FT-self], pp. 1–10 (main body, results, limitations); appendices not read |
| Choudhury et al., Better Call CLAUSE (Findings EACL 2026; arXiv 2511.00340v2) | [FT-partial] (~35% verbatim, incl. category list, generation prompts, validation, Eval_1 table) |
| Joshi & He, (In)effectiveness of CAD (ACL 2022) | [FT-partial] (verbatim through Section 6; appendices summarised) |
| Huang, Liu & Bowman, CAD-SNLI (Insights 2020) | [FT-partial] (full HTML rendering read) |
| Hsia et al., Goodhart's Law and explanation benchmarks (Findings EACL 2024) | [FT-self], pp. 1–4 only (introduction, related work, ERASER attack definition) |
| Kamahi & Yaghoobzadeh, counterfactual faithfulness evaluation (BlackboxNLP 2024) | [FT-partial] (verbatim through Sec. 5.1, Tables 1–3) |
| Hase, Xie & Bansal, OOD problem in explainability (NeurIPS 2021) | [FT-partial] (verbatim Sections 1–5) |
| Geiger, Cases, Karttunen & Potts, fair generalization tasks (EMNLP 2019) | [FT-partial] (verbatim ~57%, incl. definitions) |
| Ju & Lee, citation-closure retrieval / RegOps-Bench (arXiv 2605.29742) | [FT-partial] |
| Guo, Wu & Yiu, ComplianceNLP (arXiv 2604.23585, ACL 2026 Industry per arXiv comment) | [FT-partial] |
| Apaolaza Larraya et al., logical coherence via fine-grained NLI (LREC 2026) | [ABS] (PDF not extractable) |
| Mahendra et al., numeracy as NLI (Findings NAACL 2025) | [ABS] |
| Zhou, Booth, Ribeiro & Shah, do attribution methods attribute correctly? (AAAI 2022) | [ABS] |
| Abraham et al., CEBaB (NeurIPS 2022) | [ABS] |
| She, Potts, Bowman & Geiger, ScoNe (ACL 2023) | [ABS] |
| Geiger et al., causal abstractions of neural networks (NeurIPS 2021) | [ABS] |
| Feng, Wallace & Boyd-Graber, partial-input baselines (ACL 2019) | [ABS] |
| D'Amour et al., underspecification (JMLR 2022) | [ABS] |
| Polo et al., tinyBenchmarks (2024) | [ABS] |
| Khashabi, Khot & Sabharwal, natural perturbations (EMNLP 2020) | [ABS] |
| Teney, Abbasnejad & van den Hengel, gradient supervision from counterfactual pairs (ECCV 2020) | [ABS] |
| Kazemi et al., BoardgameQA (NeurIPS 2023 D&B) | [ABS] |
| Holzenberger, Blair-Stanek & Van Durme, SARA statutory reasoning (2020) | [ABS] |
| UNMASK (arXiv 2608.09209, 2026); "Catching Shortcuts" (ACL 2025); TruthfulQA leakage audit (arXiv 2609.13003, 2026); shortcut-learning analysis (Findings EMNLP 2024) | [ABS] (search summaries only; identified late, must be read) |
| McCoy et al. HANS; Gardner et al. contrast sets; Kaushik et al. CAD; ContractNLI; LegalBench; ConditionalQA; RuleTaker; CheckList; ERASER; Poliak et al.; Gururangan et al. | [PRIOR] |

Not found despite searching: a paper that evaluates whether models resolve legal cross-references separately from
understanding the referenced exception; a paper that measures how many benchmark items distinguish a family of
plausible heuristics from the intended rule. Absence in our searches is not proof of absence (Section 6).

## 1. Rule-like and legal documents: what exists

**COMPACT / ACE (Singh et al., EACL 2026) [FT-self]** is the closest recent work in topic. It builds clause graphs
from 633 CUAD/ContractNLI contracts (edge types DEFINES, COMPLEMENTS, EXCEPTIONS, DEPENDS_ON, CONFLICTS, SEQUENCE)
and generates 4,700 compliance scenarios with GPT-4o, validated by Claude Sonnet 4; labels are compliant /
non-compliant / non-applicable (the same three-way structure as ClauseShift). A legal expert judged 46/50 labels
correct (92%). Base models reach 34–57% accuracy; LoRA fine-tuning on DeepSeek-R1 reasoning traces gives +21.7 to
+43.1 accuracy points on ACE (Table 6). There are no controlled minimal pairs, no per-operator analysis, no shortcut
or identifiability analysis, and no evidence evaluation. The non-applicable class is built by pairing scenarios with
clauses written for other provisions ("cross-matching"); whether a topic-matching heuristic solves that class is not
examined — a question ClauseShift's lazy-reader result makes concrete.

**Better Call CLAUSE (Choudhury et al.) [FT-partial]** perturbs CUAD/ContractNLI contracts with an LLM along 5
contradiction types × 2 dimensions (in-text vs. legal); a 25% sample was checked by three NLP experts (κ ≈ 0.97–0.99).
Tasks are discrepancy detection, type classification and span/explanation. Files contain several perturbations, so the
design is not a controlled single-edit minimal pair; there are no exemption, boundary or cross-reference operators
as such (cross-reference disruption is one sub-case of "structural flaws"), and no training study.

**Regulatory cross-references.** RegOps-Bench (Ju & Lee, 2026) [FT-partial] and ComplianceNLP (Guo et al., 2026)
[FT-partial] treat cross-references as edges for retrieval or extraction. ComplianceNLP reports that grounding
accuracy falls with the number of references (97.1% with none to 84.6% with three or more; from the summarised part,
unverified) and that cross-reference failures are 28% of sampled extraction errors. Neither separates "understands
the exception" from "resolves the reference". SARA (Holzenberger et al., 2020) [ABS] provides statutes with a
Prolog ground truth; LegalBench includes it.

**Older diagnostics** [PRIOR]: ContractNLI (document-level NLI over NDAs), ConditionalQA (answers with conditions),
ShARC (rule interpretation), RuleTaker and BoardgameQA (synthetic rules; BoardgameQA adds exceptions as rule
preferences).

## 2. Counterfactual training data

Joshi & He (2022) [FT-partial] show, with a linear-Gaussian argument and RoBERTa experiments on SNLI-CAD and
BoolQ-CAD (5 seeds), that CAD helps on the perturbed feature types ("aligned" test sets) but can prevent learning of
robust features that were never perturbed, and can amplify negation and word-overlap biases. Huang et al. (2020)
[FT-partial] find no out-of-domain gain of CAD-SNLI over size-matched SNLI with roberta-base (20 runs per setting)
and note that CAD has about 70% of the distinct n-grams of an equally large unaugmented set. Neither varies
initialisation (NLI-intermediate vs. generic pre-training), neither reports whether the two sides of a pair share a
batch, and neither examines whether the *edit token itself* becomes a shortcut when every pair of an edit type
differs by the same lexical item. Khashabi et al. (2020) [ABS] study the cost-effectiveness of natural perturbations;
Teney et al. (2020) [ABS] use pairs for gradient supervision.

## 3. Generalization tests and their fairness

Geiger et al. (2019) [FT-partial] define a training set as *fair* for a function F if a baseline learner can recover
F from it, and give a sufficient condition: every intermediate function of a composition tree must see all of its
possible inputs in training. Under this definition the original ClauseShift operator hold-out (no cross-reference
sentence ever appears in training) is not a fair test of cross-reference understanding: the reference-resolution
node never receives any input. A fair version must show the cross-reference construction with other content and
hold out a *combination*. HANS (McCoy et al., 2019) [PRIOR] is the template for heuristics as explicit hypotheses;
ScoNe (She et al., 2023) [ABS] contrasts solving algorithms with flawed heuristics for negation scope; causal
abstraction (Geiger et al., 2021) [ABS] tests whether a network implements a high-level algorithm through
interventions on internal representations. D'Amour et al. (2022) [ABS] describe underspecification: many predictors
with equal test performance that behave differently off-distribution.

## 4. Evidence and explanation evaluation

ERASER metrics (comprehensiveness, sufficiency) [PRIOR] remove tokens or sentences and measure the change in model
confidence. Hase et al. (2021) [FT-partial] show that removal produces out-of-distribution inputs, that the choice of
replacement function changes results by up to several points, and propose counterfactual training. Hsia et al.
(2024) [FT-self, pp. 1–4] show that a wrapper which detects masked inputs can inflate ERASER scores to near their
maximum without changing predictions or explanations on real inputs. Kamahi & Yaghoobzadeh (2024) [FT-partial] replace
masking with in-distribution counterfactual editors and argue that faithfulness datasets should *not* have gold
attributions. Zhou et al. (2022) [ABS] build semi-synthetic datasets with known ground-truth attributions and find
that popular methods mostly fail; CEBaB (Abraham et al., 2022) [ABS] uses human-written concept counterfactuals to
evaluate concept-based explanations. None of these (as far as read) studies the case where one input unit is
necessary for *every* label, so that any removal-based top-1 metric is saturated by construction, nor uses
specification-derived expected label transitions with an "insufficient" outcome.

## 5. Numeric and temporal comparison

EQUATE (Ravichander et al., 2019) [ABS, search snippet] and the numeracy-as-NLI study of Mahendra et
al. (2025) [ABS] report weak quantitative reasoning in NLI models. We could not verify whether either isolates strict
vs. non-strict comparisons at the exact boundary. ClauseShift's audit shows that 100% of fine-tuned boundary errors
reproduce the non-strict reading; whether this is known should be checked in the full texts before any claim.

## 6. What the literature already covers, and what appears open

Already covered (do not claim): minimal pairs and contrast sets; counterfactual augmentation and its mixed effect;
heuristics as hypotheses about model behaviour (HANS, ScoNe); mechanistic tests of algorithm implementation (causal
abstraction); OOD problems of removal-based explanations; gaming of explanation metrics; ground-truth attribution
benchmarks; multi-clause legal benchmarks (COMPACT, CLAUSE); cross-references as retrieval edges.

Apparently open (to be re-verified before writing; our searches can miss work):
1. **Benchmark identifiability** with respect to an explicit lattice of plausible partial rule readings: counting, for
   each heuristic, the items that distinguish it from the intended rule, and showing that a benchmark designed with
   near-miss controls still contains a dimension with zero such items.
2. **Behavioural program identification across training regimes** (zero-shot vs. NLI-initialised vs. generic
   initialisation; paired vs. unpaired) on rule documents, with selection on dev and evaluation on test, and with
   predictions about new probes.
3. **A non-adversarial sanity check for sentence-level evidence metrics**: a reader that ignores every condition
   obtains perfect hit@1 because one sentence is necessary for every label.
4. **Counterfactual pairs as installers of edit-token shortcuts** when an edit type has a single lexical realization
   (pending Pilot 2).
5. **Adaptive item selection for program identification** (related to IRT-based efficient evaluation such as
   tinyBenchmarks [ABS] and active testing, which estimate accuracy rather than identify an algorithm).
