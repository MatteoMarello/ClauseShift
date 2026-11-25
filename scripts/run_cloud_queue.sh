#!/usr/bin/env bash
# Prioritised experiment queue for a 4-core CPU cloud container (see docs/PREREGISTRATION.md, "Deviations").
# Every step is skipped if its outputs already exist, so the queue can be restarted at any time.
# After every completed step: tests, analysis tables, integrity check, then commit + push of results/ and logs/
# (never weights; checkpoints are not written to disk by finetune.py).
#
# Priority order (most informative first):
#   0  reproduction check of a stored zero-shot system
#   1  zero-shot facts_in_premise format, 4 models (exploratory; tests the format-mismatch explanation)
#   2  paired vs. unpaired fine-tuning, seeds 0-2, interleaved by seed (H3, preregistered)
#   3  occlusion evidence for the zero-shot models (preregistered metric)
#   4  operator hold-out, seed 0 (preregistered with 3 seeds; reduced)
#   5  no-NLI-pretraining ablation, paired + unpaired, seed 0 (as preregistered)
#   6  operator hold-out, seeds 1-2 (restores the preregistered scope if budget allows)
set -u
PY=${PY:-python}
BRANCH=$(git rev-parse --abbrev-ref HEAD)
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
mkdir -p logs

checkpoint() {
  local msg="$1"
  "$PY" -m pytest -q > /dev/null 2>&1 || { echo "tests failed, not committing ($msg)"; return; }
  "$PY" scripts/analyze.py > /dev/null 2>&1 || echo "analyze.py failed"
  "$PY" scripts/error_analysis.py > /dev/null 2>&1 || echo "error_analysis.py failed"
  "$PY" scripts/verify_integrity.py > /dev/null 2>&1 || echo "integrity check reported failures (see results/INTEGRITY.md)"
  git add results/ logs/
  if ! git diff --cached --quiet; then
    git commit -q -m "Results: $msg" -m "Automated checkpoint from scripts/run_cloud_queue.sh (tests passed, tables regenerated)." \
      -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GGpeb3aQtBq4JH6BHTfvnv"
    for i in 1 2 3 4; do git push -q -u origin "$BRANCH" && break; sleep $((2 ** i)); done
  fi
  echo "$(date -u +%FT%TZ) checkpoint: $msg"
}

ft() {  # ft <name> <system dir> <args...>
  local name="$1" system="$2"; shift 2
  if [ -f "results/predictions/$system/test.jsonl" ]; then echo "skip $name"; return; fi
  echo "$(date -u +%FT%TZ) start $name"
  "$PY" scripts/finetune.py "$@" > "logs/$name.log" 2>&1
  echo "$(date -u +%FT%TZ) end $name rc=$?"
  checkpoint "fine-tuning run $name"
}

M=nli-deberta-v3-xsmall
R=deberta-v3-xsmall

# 0
if [ ! -f results/reproduction_check.json ]; then
  "$PY" scripts/check_reproduction.py > logs/reproduction_check.log 2>&1
  checkpoint "reproduction check of stored zero-shot predictions"
fi

# 1
for m in cross-encoder/nli-deberta-v3-xsmall cross-encoder/nli-deberta-v3-base \
         MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli FacebookAI/roberta-large-mnli; do
  sys="zeroshot_${m##*/}_factsinpremise"
  if [ -f "results/predictions/$sys/test.jsonl" ]; then echo "skip $sys"; continue; fi
  echo "$(date -u +%FT%TZ) start $sys"
  "$PY" scripts/run_zero_shot.py --format facts_in_premise --models "$m" >> logs/zero_shot_factsinpremise.log 2>&1
  checkpoint "zero-shot facts_in_premise, ${m##*/}"
done

# 2
for s in 0 1 2; do
  ft paired_s$s   ft_${M}_paired_s$s   --condition paired   --seed $s
  ft unpaired_s$s ft_${M}_unpaired_s$s --condition unpaired --seed $s
done

# 3
if grep -L '"evidence_test"' results/predictions/zeroshot_*/meta.json | grep -vq factsinpremise; then
  echo "$(date -u +%FT%TZ) start zero-shot evidence"
  "$PY" scripts/run_evidence_zero_shot.py > logs/evidence_zero_shot.log 2>&1
  checkpoint "occlusion evidence for zero-shot models"
fi

# 4
ft op_holdout_s0 ft_${M}_op_holdout_s0 --condition op_holdout --seed 0

# 5
ft raw_paired_s0   ft_${R}_paired_s0   --model microsoft/deberta-v3-xsmall --condition paired   --seed 0 --lr 5e-5
ft raw_unpaired_s0 ft_${R}_unpaired_s0 --model microsoft/deberta-v3-xsmall --condition unpaired --seed 0 --lr 5e-5

# 6
for s in 1 2; do
  ft op_holdout_s$s ft_${M}_op_holdout_s$s --condition op_holdout --seed $s
done
echo "$(date -u +%FT%TZ) queue finished"
