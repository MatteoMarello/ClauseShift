#!/usr/bin/env bash
# Re-train four registered configurations (seed 0) with weights kept locally for the Pilot-2 probes.
# Predictions go to research_next/results/predictions (not results/), weights to checkpoints/ (gitignored).
set -u
PY=${PY:-python}
export HF_HUB_DISABLE_PROGRESS_BARS=1 TOKENIZERS_PARALLELISM=false
OUT=research_next/results/predictions
run() { name="$1"; shift; echo "$(date -u +%FT%TZ) start $name"
  "$PY" scripts/finetune.py "$@" --seed 0 --out-root $OUT --save-dir checkpoints > research_next/logs/$name.log 2>&1
  echo "$(date -u +%FT%TZ) end $name rc=$?"; }
run nli_paired_s0   --condition paired
run nli_unpaired_s0 --condition unpaired
run raw_paired_s0   --model microsoft/deberta-v3-xsmall --condition paired   --lr 5e-5
run raw_unpaired_s0 --model microsoft/deberta-v3-xsmall --condition unpaired --lr 5e-5
echo "$(date -u +%FT%TZ) retrain finished"
