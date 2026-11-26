# Related-work matrix

Status tags as in `LITERATURE_REVIEW.md`: [FT-self] main body read in this session; [FT-partial] partly verbatim,
partly model-summarised; [ABS] abstract or snippet only; [PRIOR] from the original review, not re-read. Cells marked
"not stated" mean the part we read does not say; "–" means not applicable.

## A. Benchmarks and datasets

| Work | Status | Research question | Data | Controlled minimal pairs | Labels | Main result (as read) | Limitations (as read) | Overlap with ClauseShift |
|---|---|---|---|---|---|---|---|---|
| COMPACT / ACE (EACL 2026) | FT-self | Multi-clause compliance reasoning over contracts | 4,700 GPT-4o scenarios from 633 CUAD/ContractNLI contracts; LLM-validated; expert check 46/50 | No | compliant / non-compliant / non-applicable | Base 34–57% acc.; LoRA SFT on R1 traces +21.7–43.1 points | English; ~6k-token inputs; clauses assumed pre-identified | Same 3-way structure, exceptions, temporal conditions; no controlled edits, no shortcut or identifiability analysis |
| Better Call CLAUSE (Findings EACL 2026) | FT-partial | Do LLMs detect and justify contract discrepancies? | LLM-perturbed CUAD/ContractNLI, 7,514 contracts, 10 categories | No (several edits per file) | discrepancy yes/no; type; span | Gemini-2.5 F1 ≈ 63% on CUAD detection; legal citation weak | Counts in validation do not reconcile with Table 1 (our reading) | Perturbation of real contracts; no single-edit operators, no training study |
| ContractNLI (2021) | PRIOR | Document-level NLI on NDAs | 607 NDAs, 17 hypotheses, CC BY 4.0 | No | entailed / contradicted / not mentioned | – | Fixed hypotheses, NDAs only | Same label semantics; candidate external-validity target (Direction D) |
| ConditionalQA (2022) | PRIOR | QA with conditional answers | UK public-policy pages | No | answers + conditions | – | – | Conditions on unstated attributes |
| SARA (2020) | ABS | Statutory reasoning in tax law | 9 simplified IRC sections + hand-written cases + Prolog | No | entailment / numeric | – | Small | Rule texts with exact ground truth |
| RuleTaker; BoardgameQA (2023) | PRIOR / ABS | Reasoning over synthetic rules; conflicting rules with preferences | Synthetic | No | true/false/unknown | Fine-tuning helps but remains poor with conflicts (BoardgameQA) | Synthetic | Exceptions as rule preferences; closed vs. open world |
| RegOps-Bench / RefWalk (2026) | FT-partial | Complete citation sets for regulatory QA | 12 Korean regulations, 231 QA; HIPAA set | No | citation sets, claims | Full coverage at k=10 only for a minority of multi-hop queries | Korean formats | Cross-references as graph edges; no separation of reference vs. exception understanding |
| ComplianceNLP (2026) | FT-partial | KG-augmented RAG for regulatory gap detection | SEC/MiFID II/Basel III, 12,847 provisions | No | gap labels | Cross-reference failures 28% of sampled extraction errors (summarised part) | Data partly not releasable | Reference chains in real regulation |
| HANS (2019) | PRIOR | Do NLI models use syntactic heuristics? | Templates | Heuristic-targeted | entail / non-entail | Models adopt heuristics | – | Heuristics as explicit hypotheses — the template for program identification |
| ScoNe (2023) | ABS | Negation scope in NLI | Contrast sets of 6 | Yes | NLI | Fine-tuned RoBERTa/DeBERTa solve it; ICL struggles | – | Contrasts solving algorithms with flawed heuristics |
| CheckList (2020) | PRIOR | Behavioural testing | Templates | Invariance/directional tests | task | – | – | Invariance and directional expectations |

## B. Counterfactual training

| Work | Status | Size-matched | Pair placement | Initialisation varied | Seeds | Finding | Relation to ClauseShift |
|---|---|---|---|---|---|---|---|
| Kaushik et al. (2020) | PRIOR | partly | not stated | no | – | CAD improves OOD in some settings | Origin of the paired-training question |
| Huang, Liu & Bowman (2020) | FT-partial | yes (8.3k) | not stated | no (roberta-base) | 20 runs/setting | No MNLI gain over size-matched SNLI; worse on negation diagnostics | Same null at equal size; our +0.021 is within that range |
| Joshi & He (2022) | FT-partial | yes | not stated | BERT vs RoBERTa only | 5 | CAD helps aligned perturbations; can hurt unperturbed robust features; amplifies biases | Predicts gain concentrated on perturbed types — consistent with pairing helping cross-references |
| Khashabi et al. (2020) | ABS | cost-matched | – | no | – | Perturbations pay off if < ~60% of the cost of new items | Cost framing |
| Teney et al. (2020) | ABS | – | pairs used jointly (gradient supervision) | – | – | Pair-based gradient supervision improves OOD | Mechanism by which pairs isolate the changed feature |

## C. Generalization and algorithm identification

| Work | Status | Question | Method | Relation |
|---|---|---|---|---|
| Geiger et al. (2019) | FT-partial | When is a generalization test fair? | Composition trees; every node must see all inputs | The original cross-reference hold-out is not fair; a fair compositional hold-out is required |
| Geiger et al. (2021), causal abstraction | ABS | Does a network implement a given algorithm? | Interchange interventions on internal states | Mechanistic counterpart of behavioural program identification |
| D'Amour et al. (2022) | ABS | Underspecification | Many equally good predictors differ OOD | Identifiability is underspecification at the benchmark-design level |
| Feng, Wallace & Boyd-Graber (2019) | ABS | Limits of partial-input baselines | Artificial datasets | A partial-input baseline failing does not prove absence of artefacts; our lazy reader is a full-input, rule-subset baseline |
| Polo et al. (2024), tinyBenchmarks | ABS | Evaluate with fewer items | IRT | Adaptive selection for accuracy estimation; ours targets algorithm identification |

## D. Evidence and faithfulness

| Work | Status | Granularity | Ground truth | Finding | Relation |
|---|---|---|---|---|---|
| ERASER (2020) | PRIOR | token/sentence | human rationales | comprehensiveness/sufficiency | ClauseShift's hit@1 is a top-1 comprehensiveness variant |
| Hase et al. (2021) | FT-partial | token | none | Removal is OOD; replacement choice matters; counterfactual training | Our removal variants also drop headers (documented) |
| Hsia et al. (2024) | FT-self (pp. 1–4) | token | none | ERASER scores can be inflated by a wrapper without changing predictions | Ours: a *non-adversarial* naive reader saturates hit@1 by data structure |
| Kamahi & Yaghoobzadeh (2024) | FT-partial | token | none by design | In-distribution counterfactual editors stabilise method rankings | Ours uses specification-derived expected transitions instead |
| Zhou et al. (2022) | ABS | token/region | constructed | Methods mostly fail ground-truth unit tests | Closest "known ground truth" design |
| CEBaB (2022) | ABS | concept | human counterfactuals | Concept explanation methods rarely beat a simple baseline | Counterfactual effects as evaluation target |
| Apaolaza Larraya et al. (LREC 2026) | ABS | phrase pairs | – | Predictions unstable under reversed inference direction | Coherence across controlled variants |

## E. Which ClauseShift contributions are already in the literature

| ClauseShift element | Already present? | Where |
|---|---|---|
| Minimal pairs / pair accuracy | Yes | Contrast sets, CAD, ScoNe |
| Rule documents with exceptions and conditions | Yes (real or LLM-generated) | COMPACT, CLAUSE, ConditionalQA, BoardgameQA |
| Exact single-edit operators with spec-derived labels | Partly (synthetic rule sets exist; not with these operators) | RuleTaker, SARA |
| Paired vs. unpaired at equal size | Yes (NLI, QA) | Huang et al., Joshi & He |
| Hold-out of an edit type | Yes as a design; fairness criteria exist | Geiger et al. (2019) |
| Occlusion evidence problems (OOD, gaming) | Yes | Hase et al., Hsia et al. |
| Lazy-reader saturation of hit@1 | Not found | – |
| Benchmark identifiability against a heuristic lattice | Not found | – |
| Behavioural program identification across training regimes | Partly (heuristic hypotheses: HANS, ScoNe; mechanistic: causal abstraction) | – |
| Pairs installing an edit-token shortcut | Not found (related: Joshi & He on aligned perturbations) | – |
