# Pilot protocol (written and committed before any pilot was run)

All pilots are exploratory; they use existing families (vehicles = dev; enrollment, research_funding = test) and the
four locally saved checkpoints that reproduce registered runs exactly (NLI-init and generic-init, paired and unpaired,
seed 0). Nothing here is confirmatory. Compute budget for all pilots: ≤ 2 hours CPU; planned ≈ 45 minutes.
Hardware verified: 4 CPU cores, 15 GB RAM, no GPU.

## Pilot 1 — Copy is not compare (C1)

**Items** (`scripts/make_boundary_probes.py`, generator functions reused, `data/` untouched). Per family, 60 base cases
with exactly one condition, half numeric thresholds ("more than t"), half date cutoffs ("after d"); random claim
polarity. Each base case is rendered at three positions × three surface forms of the *case value* (the rule is never
changed):

- Positions: `eq` (case value = cutoff; condition fails), `minus` (one unit/day below; fails), `plus` (one unit/day
  above; satisfied).
- Forms: `same` (the generator's format, so at `eq` the case value is a verbatim copy of the cutoff string);
  `reorder` (dates: "December 15, 2025"; numbers: digits without thousands separator, e.g. "€85000"; for integers
  without separators this form is identical to `same` and is not used); `words` (dates: ordinal day,
  "15th December 2025"; numbers: written in words, e.g. "forty-eight credits"; money: "85 thousand euros").

**Hypotheses** (mutually exclusive accounts of the boundary errors):
- H_span (span identity): errors arise because the value appears verbatim in the condition.
- H_token (token identity): errors arise because the value's tokens appear in the condition.
- H_strict (semantics): the model reads "more than / after" as non-strict.
- H_approx (approximate comparison): the model is unreliable near the cutoff on both sides.

**Primary quantity** for each model: equality accuracy by form, and the difference-in-differences
DiD(form) = [acc(eq, form) − acc(eq, same)] − [acc(plus, form) − acc(plus, same)], which removes a general effect of the
unusual surface form.

**Predictions fixed now.**
- H_span: acc(eq, same) is low (< 0.6) and DiD(reorder) ≥ 0.20 and DiD(words) ≥ 0.20.
- H_token: DiD(words) ≥ 0.20 but DiD(reorder) < 0.10 for dates (reordering keeps all tokens).
- H_strict: DiD(reorder) and DiD(words) both < 0.10, with acc(minus) and acc(plus) high (≥ 0.8) in every form.
- H_approx: acc(minus, same) also low (< 0.7).
**Validity condition**: a form is interpretable only if acc(plus, form) ≥ 0.70 and acc(minus, form) ≥ 0.70 (the
model still compares values written that way); otherwise that form's result is reported as uninterpretable.
Uncertainty: bootstrap over base cases, 2,000 resamples, per model; families pooled and reported separately.

## Pilot 2 — Errors that respect the symmetry (C2)

**Items**: for every test item, the same document and case with the claim polarity flipped ("is required to" ↔ "is
not required to", same template index), generated from the specification; the label maps by σ: entailed ↔
contradicted, insufficient fixed (checked against `gold_label` for every item).

**Quantities** (per model; original predictions are the stored ones, which the checkpoints reproduce exactly):
- Symmetry consistency: P(pred(flip) = σ(pred(orig))).
- Covariant error share: among items wrong on the original, the share whose flipped prediction equals σ(original
  prediction) — the same wrong reading applied consistently.
- Symmetrised decoding: p_sym(y) ∝ p_orig(y) · p_flip(σ(y)); accuracy change vs. original.

**Predictions fixed now** (competing): H_prog — errors are program-like: covariant share ≥ 0.70 for fine-tuned models,
and symmetrised decoding changes accuracy by < 0.02. H_noise — covariant share < 0.50 and symmetrisation gains
≥ 0.03. For zero-shot MNLI models we predict *lower* symmetry consistency than for fine-tuned ones because of their
known weakness with negated hypotheses; if instead they are as consistent as fine-tuned models, their errors are a
consistent misreading (as the lazy-program result suggests).
Models: the four checkpoints; zero-shot DeBERTa-v3-base NLI and DeBERTa-v3-base MNLI-FEVER-ANLI (standard format).

## Pilot 3 — Strategy trajectory during fine-tuning (C3), run only if Pilots 1–2 used < 1 hour

Re-run the registered NLI-init paired seed-0 configuration (identical recipe; its endpoint reproduces the stored
model) with evaluation every 25 steps on a fixed diagnostic set of **dev** items chosen by a greedy multicover of the
648-program lattice (each distinguishable program pair separated by ≥ 5 items where possible). At each evaluation:
best-fitting program (agreement), its agreement, the runner-up, and dev accuracy on the diagnostic set.
**Prediction fixed now**: H_steps — the best-fitting program changes at most 5 times over 18 evaluations, and
dimensions are acquired in the order negation/topic → exemptions/scope → thresholds/dates (boundary strictness never).
H_smooth — agreement with the reference rule increases monotonically with no plateau longer than 3 evaluations and
the best program changes at most twice. An abrupt change is called a "transition" only if agreement with the
best program jumps by ≥ 0.15 between consecutive evaluations; no "phase transition" language is used.

## Reporting rules

All outcomes are reported, including failed predictions and uninterpretable forms. No pilot is repeated to obtain a
different result. Any change to this protocol after a pilot has run is listed in PILOT_RESULTS.md as a deviation.
