#!/usr/bin/env bash
# Preregistered fine-tuning runs, sequential (CPU). Each run logs to logs/<system>.log.
set -u
PY=${PY:-python}
run() { name="$1"; shift; echo "$(date -u +%FT%TZ) start $name"; "$PY" scripts/finetune.py "$@" > "logs/$name.log" 2>&1; echo "$(date -u +%FT%TZ) end $name rc=$?"; }
for s in 0 1 2; do
  run paired_s$s   --condition paired   --seed $s
  run unpaired_s$s --condition unpaired --seed $s
done
for s in 0 1 2; do
  run op_holdout_s$s --condition op_holdout --seed $s
done
run raw_paired_s0 --model microsoft/deberta-v3-xsmall --condition paired --seed 0 --lr 5e-5
run raw_unpaired_s0 --model microsoft/deberta-v3-xsmall --condition unpaired --seed 0 --lr 5e-5
