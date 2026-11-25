# Cloud resume guide

## State (2026-11-25, branch `research/finetune-and-facts-in-premise`)
| Step | Status | Output |
|---|---|---|
| Data v2 + integrity checks + tests | done; re-verified (`scripts/verify_integrity.py`) | `data/`, `tests/`, `results/INTEGRITY.md` |
| Baselines | done | `results/predictions/{majority,tfidf_*}` |
| Zero-shot, 4 NLI models, standard format | done; reproduction check passed | `results/predictions/zeroshot_*`, `results/reproduction_check.json` |
| Zero-shot `facts_in_premise` (exploratory), 4 models | done | `results/predictions/zeroshot_*_factsinpremise` |
| Fine-tuning paired / unpaired, seeds 0–2 (H3) | done | `results/predictions/ft_nli-deberta-v3-xsmall_{paired,unpaired}_s*` |
| Occlusion evidence, zero-shot models | done | `evidence_test` in `meta.json`, `evidence_test.jsonl` |
| Operator hold-out, seed 0 | running | `results/predictions/ft_nli-deberta-v3-xsmall_op_holdout_s0` |
| No-NLI-pre-training ablation, paired + unpaired, seed 0 | queued | `results/predictions/ft_deberta-v3-xsmall_*` |
| Operator hold-out, seeds 1–2 | queued (lowest priority) | — |
| Extended analysis, figures | done for completed runs; re-run after each run | `results/EXTENDED_ANALYSIS.md`, `results/figures/fig*.png` |
| Report §5–6, README, study guide | written for completed runs; ablation section pending | `docs/REPORT.md`, `README.md`, `docs/STUDY_GUIDE.md` |
| Human annotation of `review/annotation_sheet.csv` | **not done** (requires a human annotator) | — |

The status column of this table is updated by hand when a step finishes; the per-run commits in `git log` are the
authoritative record.

## Environment
```bash
python -m venv .venv && source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
pip install -r requirements.txt
python -m pytest -q
python scripts/verify_integrity.py
```
Hardware used for the fine-tuning runs: 4-core Intel Xeon CPU, no GPU (detected and stored in each `meta.json`).
Measured cost: about 20 minutes per paired/unpaired run, about 35 minutes per operator hold-out run.

## Resume
`scripts/run_cloud_queue.sh` skips every step whose outputs exist, so it can simply be restarted:
```bash
PY=$(which python) nohup bash scripts/run_cloud_queue.sh > logs/cloud_queue.log 2>&1 &
```
After each run it executes the tests, `analyze.py`, `error_analysis.py` and `verify_integrity.py`, then commits and
pushes `results/` and `logs/`. Afterwards run `python scripts/analyze_extended.py` and update the report sections
that depend on new runs. Never edit generated tables by hand; never regenerate `data/`.

## Resume prompt for an AI coding assistant
> Read CLAUDE.md and CLOUD_RESUME.md. Verify the environment, run `pytest` and `scripts/verify_integrity.py`.
> Restart `scripts/run_cloud_queue.sh` (it skips completed runs). When runs finish, run `analyze.py`,
> `analyze_extended.py` and `error_analysis.py`, update `docs/REPORT.md` §5.7 and the README findings strictly from
> `results/RESULTS.md` and `results/EXTENDED_ANALYSIS.md`, and update the state table above. Do not regenerate data.
> Do not describe labels as human-validated.
