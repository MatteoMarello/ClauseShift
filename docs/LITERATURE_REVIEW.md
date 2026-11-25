# Literature review and positioning

Scope: work on (a) minimal-edit / contrast evaluation, (b) counterfactually augmented training data, (c) annotation
artifacts in NLI, (d) inference over rules, conditions and exceptions, (e) contract and legal NLI. Entries marked
*(abstract only)* were checked through their abstract or project page, not read in full.

## Related-work matrix

| Work | Data | Minimal pairs | 3-way incl. "not enough info" | Conditions / exceptions | Held-out shift | Studies training on pairs |
|---|---|---|---|---|---|---|
| Contrast sets (Gardner et al., Findings EMNLP 2020) | expert edits of 10 existing test sets | yes | task-dependent | no | no | no |
| CAD (Kaushik et al., ICLR 2020) | crowd-edited SNLI / IMDb | yes | yes (SNLI) | no | yes | yes |
| CAD-SNLI negative result (Huang, Liu & Bowman, Insights 2020) | CAD-SNLI | yes | yes | no | challenge sets | yes: no gain at equal size |
| (In)effectiveness of CAD (Joshi & He, ACL 2022) | CAD + toy model | yes | yes | no | yes | yes: gains limited by edit diversity |
| HANS (McCoy et al., ACL 2019) | templates | no | binary | no | heuristic-targeted | no |
| Hypothesis-only baselines (Poliak et al., *SEM 2018; Gururangan et al., NAACL 2018) | SNLI/MNLI | no | yes | no | no | no |
| CheckList (Ribeiro et al., ACL 2020) | templates | invariance/directional tests | task-dependent | partly | no | no |
| ShARC (Saeidi et al., EMNLP 2018) | rule texts + dialogues | no | yes / no / irrelevant + follow-up | yes | no | no |
| ConditionalQA (Sun, Cohen & Salakhutdinov, ACL 2022) | UK public-policy documents | no | not-answerable questions | yes, answers with conditions | no | no |
| RuleTaker (Clark et al., IJCAI 2020) | synthetic rule bases | no | closed / open world | negation as failure | depth | no |
| ContractNLI (Koreeda & Manning, Findings EMNLP 2021) | 607 NDAs, 17 hypotheses | no | entailed / contradicted / not mentioned | implicit | no | no |
| LegalBench (Guha et al., NeurIPS 2023 D&B) | 162 legal tasks | no | task-dependent | some tasks | no | no |
| CLAUSE (Choudhury et al., Findings EACL 2026) *(abstract only)* | 7,500+ perturbed CUAD/ContractNLI contracts | perturbed vs. original | discrepancy detection | yes (e.g. thresholds, inserted exceptions) | no | no |
| **ClauseShift (this work)** | synthetic rules, 8 fictional families | **exact single-edit pairs, 14 operators** | **yes** | **yes, incl. cross-references and boundaries** | **family + template** | **yes, size-matched** |

Further context: negation in NLI benchmarks (Hossain et al., EMNLP 2020); defeasible inference (Rudinger et al.,
Findings EMNLP 2020); evidence and rationale evaluation (DeYoung et al., ERASER, ACL 2020); selective prediction under
shift (Kamath, Jia & Liang, ACL 2020).

## Positioning and claimed contribution

ClauseShift is **not** the first benchmark of minimal edits, nor of perturbed legal-style text. Contrast sets and
CAD established paired evaluation; CLAUSE (2026) applies perturbations such as changed thresholds and inserted
exceptions to real contracts and evaluates LLMs on detecting the resulting discrepancies. That is the closest prior
work found, and it overlaps with the framing "small edits to clauses that change meaning".

What ClauseShift adds is narrower and methodological:

1. **Exact counterfactual control.** Each pair differs by one specified operator, and the gold label is computed from
   a rule specification. This allows clean per-operator attribution: exception scope, cross-reference resolution,
   numeric and date boundaries, scope restriction, missing attributes, and negation.
2. **Contradiction vs. insufficient evidence** as a first-class distinction, with edits that move a case from
   decided to undecided (`condition_unknown`, `topic_swap`).
3. **Near-miss controls**: lexical edits that do not change the label for the case at hand. They separate
   sensitivity to the edit location from understanding of the edit.
4. **A size-matched test of counterfactual training** (paired vs. unpaired, same number of items) on held-out
   families and templates. This revisits the mixed CAD findings in a setting where edit diversity is controlled by
   design.

Limitations that bound these claims: the text is template-generated and fictional, so results show what models do
on controlled rule language, not on real contracts; labels are generator-derived until the human review is
complete; the encoder experiments run on CPU-sized models.

## References

- Clark, P., Tafjord, O., Richardson, K. (2020). Transformers as Soft Reasoners over Language. IJCAI.
- Choudhury, M. et al. (2026). Better Call CLAUSE: A Discrepancy Benchmark for Auditing LLMs Legal Reasoning
  Capabilities. Findings of EACL. https://aclanthology.org/2026.findings-eacl.305/
- DeYoung, J. et al. (2020). ERASER: A Benchmark to Evaluate Rationalized NLP Models. ACL.
- Gardner, M. et al. (2020). Evaluating Models' Local Decision Boundaries via Contrast Sets. Findings of EMNLP.
  https://aclanthology.org/2020.findings-emnlp.117
- Guha, N. et al. (2023). LegalBench: A Collaboratively Built Benchmark for Measuring Legal Reasoning in Large
  Language Models. NeurIPS Datasets and Benchmarks.
- Gururangan, S. et al. (2018). Annotation Artifacts in Natural Language Inference Data. NAACL.
- Hossain, M. M. et al. (2020). An Analysis of Natural Language Inference Benchmarks through the Lens of Negation. EMNLP.
- Huang, W., Liu, H., Bowman, S. R. (2020). Counterfactually-Augmented SNLI Training Data Does Not Yield Better
  Generalization Than Unaugmented Data. Workshop on Insights from Negative Results in NLP.
  https://aclanthology.org/2020.insights-1.13/
- Joshi, N., He, H. (2022). An Investigation of the (In)effectiveness of Counterfactually Augmented Data. ACL.
  https://aclanthology.org/2022.acl-long.256/
- Kamath, A., Jia, R., Liang, P. (2020). Selective Question Answering under Domain Shift. ACL.
- Kaushik, D., Hovy, E., Lipton, Z. C. (2020). Learning the Difference that Makes a Difference with
  Counterfactually-Augmented Data. ICLR.
- Koreeda, Y., Manning, C. D. (2021). ContractNLI: A Dataset for Document-level Natural Language Inference for
  Contracts. Findings of EMNLP. https://aclanthology.org/2021.findings-emnlp.164/
- McCoy, R. T., Pavlick, E., Linzen, T. (2019). Right for the Wrong Reasons: Diagnosing Syntactic Heuristics in
  Natural Language Inference. ACL.
- Poliak, A. et al. (2018). Hypothesis Only Baselines in Natural Language Inference. *SEM.
- Ribeiro, M. T. et al. (2020). Beyond Accuracy: Behavioral Testing of NLP Models with CheckList. ACL.
- Rudinger, R. et al. (2020). Thinking Like a Skeptic: Defeasible Inference in Natural Language. Findings of EMNLP.
- Saeidi, M. et al. (2018). Interpretation of Natural Language Rules in Conversational Machine Reading. EMNLP.
- Sun, H., Cohen, W. W., Salakhutdinov, R. (2022). ConditionalQA: A Complex Reading Comprehension Dataset with
  Conditional Answers. ACL. https://aclanthology.org/2022.acl-long.253

### Models and methods used
- Efron, B., Tibshirani, R. J. (1993). An Introduction to the Bootstrap. Chapman & Hall.
- He, P., Liu, X., Gao, J., Chen, W. (2021). DeBERTa: Decoding-enhanced BERT with Disentangled Attention. ICLR.
- He, P., Gao, J., Chen, W. (2023). DeBERTaV3: Improving DeBERTa using ELECTRA-Style Pre-Training with
  Gradient-Disentangled Embedding Sharing. ICLR.
- Liu, Y. et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach. arXiv:1907.11692.
- Loshchilov, I., Hutter, F. (2019). Decoupled Weight Decay Regularization. ICLR.
- Williams, A., Nangia, N., Bowman, S. R. (2018). A Broad-Coverage Challenge Corpus for Sentence Understanding
  through Inference. NAACL.
