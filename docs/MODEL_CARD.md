# Model card: ClauseShift fine-tuned cross-encoders (research artifacts, weights not released)

## What
`cross-encoder/nli-deberta-v3-xsmall` (and, as an ablation, `microsoft/deberta-v3-xsmall`) fine-tuned for three-way
inference (`entailed` / `contradicted` / `insufficient`) on the ClauseShift v2 training families. Exact revisions,
hyperparameters, selected epochs and training logs are in `results/predictions/ft_*/meta.json`.

Weights are not published: the models exist to answer the research questions in `docs/PREREGISTRATION.md`, and
every number can be regenerated with `scripts/run_finetune_queue.sh` (CPU, about 25–45 minutes per run on a
6-core laptop CPU).

## Training
AdamW (weight decay 0.01), linear schedule with 10% warmup, batch size 16, max length 320 tokens, 3 epochs,
learning rate 3e-5 (5e-5 for the model without NLI pre-training), gradient clipping 1.0. Epoch selected on dev
macro-F1 (vehicles family). Seeds 0, 1, 2.

## Evaluation
Test families `enrollment` and `research_funding`, never used for training or model selection. Metrics, intervals
and per-operator results: `results/RESULTS.md`; error analysis: `results/ERROR_ANALYSIS.md`.

## Intended use
Research on sensitivity to minimal decisive edits. **Not for use on real documents**: the models were trained on
short fictional template text and have not been validated on real regulations, contracts or policies.

## Licenses
Base models: `cross-encoder/nli-deberta-v3-xsmall` (Apache-2.0), `microsoft/deberta-v3-xsmall` (MIT). See the
model pages for the authoritative terms.
