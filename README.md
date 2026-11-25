# ClauseShift

**Do NLI models notice the one sentence that changes the answer?** ClauseShift evaluates three-way inference
(`entailed` / `contradicted` / `insufficient`) over short rule-like documents with **minimal pairs**: two documents
that differ by one edit (an exemption, a threshold, a cutoff date, a cross-reference, a negation…) and share the
same hypothesis about a case. A model passes a pair only if it answers both sides correctly.

> **Status: work in progress.** Data, tests, baselines and zero-shot evaluation are complete. The preregistered
> fine-tuning experiments (paired vs. unpaired counterfactual training, operator hold-out, no-NLI-pretraining
> ablation) have **not been run yet**. Labels are generator-derived; human validation is pending.

## Data
8,320 synthetic items in 4,160 minimal pairs from 8 fictional rule families, 14 edit operators (8 that change the
label, 3 near misses, 3 surface invariances). Train, dev and test use **disjoint families**, and the test set adds
template phrasings never seen in training. See [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md).

A preregistered hypothesis-only control exposed a construction shortcut in the first data version (0.60 dev
accuracy without reading the document). It was fixed before any neural model was run; v2 reaches 0.43 (majority
0.36). Details: [`results/design_iterations/`](results/design_iterations/README.md).

## Results so far (test set, 1,280 pairs; 95% bootstrap intervals over pairs)

| System | Accuracy | Pair accuracy | Flip-pair accuracy |
|---|---|---|---|
| Majority class | 0.390 [0.371, 0.407] | 0.141 [0.121, 0.158] | 0.000 |
| TF-IDF + LR, hypothesis only | 0.415 [0.398, 0.431] | 0.124 [0.108, 0.141] | 0.000 |
| TF-IDF + LR, document + hypothesis | 0.413 [0.394, 0.434] | 0.170 [0.150, 0.190] | 0.083 [0.066, 0.101] |
| DeBERTa-v3-xsmall NLI, zero-shot | 0.399 [0.381, 0.420] | 0.181 [0.160, 0.202] | 0.129 [0.106, 0.153] |
| DeBERTa-v3-base NLI, zero-shot | 0.504 [0.483, 0.523] | 0.281 [0.256, 0.305] | 0.263 [0.231, 0.292] |
| DeBERTa-v3-base MNLI-FEVER-ANLI, zero-shot | 0.531 [0.511, 0.551] | 0.316 [0.292, 0.341] | 0.304 [0.272, 0.335] |
| RoBERTa-large-MNLI, zero-shot | 0.378 [0.361, 0.398] | 0.150 [0.133, 0.170] | 0.070 [0.054, 0.090] |

Flip-pair accuracy by edit for the three DeBERTa models (zero-shot): negation 0.33–0.88 and replaced obligation
0.42–0.81, but numeric thresholds and dates ≤ 0.04, cross-references ≤ 0.11, and conditions on an unstated attribute
≤ 0.04. RoBERTa-large-MNLI scores 0.00 on every operator except the replaced obligation (0.35). Full tables: [`results/RESULTS.md`](results/RESULTS.md); error analysis:
[`results/ERROR_ANALYSIS.md`](results/ERROR_ANALYSIS.md).

Caveat: RoBERTa-large-MNLI never predicts "entailed". In this input format the case facts are part of the
hypothesis, which MNLI-trained models may treat as unsupported new information. A variant with the facts moved into
the premise is implemented (`run_zero_shot.py --format facts_in_premise`) but not yet run, so zero-shot numbers
partly reflect format mismatch, not only edit sensitivity.

## Positioning
Closest prior work: contrast sets (Gardner et al., 2020), counterfactually augmented data (Kaushik et al., 2020;
Huang et al., 2020; Joshi & He, 2022), and CLAUSE (Choudhury et al., Findings of EACL 2026), which perturbs real
contracts. ClauseShift is a controlled diagnostic, not a new paradigm: exact single-edit operators with
generator-derived labels, insufficient-evidence edits, near-miss controls, and a size-matched test of training on
pairs. See [`docs/LITERATURE_REVIEW.md`](docs/LITERATURE_REVIEW.md) and
[`docs/PREREGISTRATION.md`](docs/PREREGISTRATION.md).

## Reproduce
```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
pip install -r requirements.txt
python -m pytest -q
python scripts/build_data.py          # regenerates identical data (hashes in data/manifest.json)
python scripts/run_baselines.py
python scripts/run_zero_shot.py
bash scripts/run_finetune_queue.sh    # not yet run; ~6 h on CPU
python scripts/analyze.py && python scripts/error_analysis.py
```
What remains and how to resume: [`CLOUD_RESUME.md`](CLOUD_RESUME.md).

## Limitations
Synthetic template text (documents of about 100 tokens); labels derived from a rule specification and not yet
human-validated; CPU-sized models; no instruction-tuned LLMs evaluated. Not a measure of legal competence.

MIT license. Code and documentation drafted with Claude Code under my direction.
