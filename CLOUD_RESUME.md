# Cloud resume guide

## State (2026-11-25)
| Step | Status | Output |
|---|---|---|
| Data v2 + integrity checks + tests (26) | done | `data/`, `tests/` |
| Baselines | done | `results/predictions/{majority,tfidf_*}` |
| Zero-shot, 4 NLI models, standard format | done | `results/predictions/zeroshot_*` |
| Analysis tables (zero-shot only) | done | `results/RESULTS.md`, `results/summary.json` |
| Fine-tuning queue (11 runs, preregistered) | **not run** | — |
| Occlusion evidence for zero-shot models | **not run** | — |
| Zero-shot `facts_in_premise` (exploratory) | **not run** | — |
| Report §5–6, README results | **not written** | `docs/REPORT.md` |

## Environment
```bash
python -m venv .venv && source .venv/bin/activate
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1   # or a CUDA build on a GPU machine
pip install -r requirements.txt
python -m pytest -q
```
On a GPU, `scripts/finetune.py` runs unchanged on CPU threads; to use CUDA add `model.to("cuda")` and move batches
(small, optional change — record it in the commit message). CPU estimate: ~25–45 min per run, ~6 h total.

## Run only what is missing (each step skips nothing; check `results/predictions/` first)
```bash
bash scripts/run_finetune_queue.sh            # 11 runs; each writes results/predictions/ft_*/ and logs/<run>.log
python scripts/run_evidence_zero_shot.py      # adds evidence_test to zeroshot_*/meta.json
python scripts/run_zero_shot.py --format facts_in_premise   # exploratory, optional
python scripts/analyze.py && python scripts/error_analysis.py
```
To resume a partially completed queue, comment out the runs whose `results/predictions/ft_*/test.jsonl` exists.

## Resume prompt for an AI coding assistant
> Read CLAUDE.md and CLOUD_RESUME.md. Verify the environment and that `pytest` passes. Run only the experiments
> marked "not run", in the order given, committing after each completed run (predictions + logs, no weights).
> Then run analyze.py and error_analysis.py, write docs/REPORT.md §5–6 and the README results section strictly
> from results/RESULTS.md and results/ERROR_ANALYSIS.md, state which preregistered hypotheses (H1–H5) are
> supported, and list limitations. Do not regenerate data. Do not describe labels as human-validated.
