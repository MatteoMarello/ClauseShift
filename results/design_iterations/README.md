# Design iterations (before any neural model was run)

## v1 → v2 (2026-11-25)
The preregistered shortcut control, TF-IDF + logistic regression on the hypothesis alone, reached 0.604 dev accuracy
on data v1 (majority: about 0.44). Diagnosis: in near-miss pairs (and in about 60% of invariant pairs) the shared
label was "required", so the claim's polarity ("is required" / "is not required") predicted entailed vs. contradicted.
Pair-level metrics were not affected (hypothesis-only flip-pair accuracy was 0.0 by construction).

Fix: `PairBuilder.mix_label` draws near-miss and invariant pairs whose shared label is entailed, contradicted or
insufficient with equal probability. Data v2 hypothesis-only dev accuracy: 0.431 (majority 0.360).
v1 predictions are kept in `v1_predictions/` for transparency. v1 data can be regenerated from commit 8bed406.
