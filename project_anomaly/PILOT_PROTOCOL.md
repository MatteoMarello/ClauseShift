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

## Addendum (written after Pilot 1 had run, before Pilot 1b; declared post hoc)

**Pilot 3 is not run.** It requires a new fine-tuning run, and the standing instruction is "no new fine-tuning without
authorisation". Its code path (re-running the registered recipe with periodic evaluation) is left as a proposal that
needs explicit approval. The third pilot slot is used instead by an inference-only follow-up of Pilot 1, chosen
*after* seeing Pilot 1, and therefore exploratory in a stronger sense than Pilots 1–2.

### Pilot 1b — the comparison as a psychophysical observer (post hoc)

Motivation from Pilot 1: errors at the boundary are not caused by string identity; instead, accuracy at one unit
*below* the cutoff is as low as at the cutoff (thresholds), and for dates errors sit one day *above* the cutoff.
This suggests a comparison with limited resolution and a bias, which psychophysics describes with a psychometric
function: the probability of the "satisfied" reading as a function of the signed distance Δ between case value and
cutoff, summarised by its point of subjective equality (PSE, where the curve crosses 0.5) and its resolution.

**Items** (`scripts/make_psychometric_probes.py`): the Pilot 1 base cases (same documents, same seeds), `same` form
only. Signed distances: thresholds Δ = r × cutoff for r ∈ {−0.5, −0.25, −0.1, −0.05, −0.02, 0, +0.02, +0.05, +0.1,
+0.25, +0.5}, rounded to the family's unit and at least one unit away from the cutoff when r ≠ 0, plus Δ = ±1 unit;
dates Δ ∈ {−365, −90, −30, −7, −2, −1, 0, +1, +2, +7, +30, +90, +365} days. Labels from `gold_label`. Same four
checkpoints.

**Quantity.** "Satisfied reading" = the prediction equals the label the item would have if the condition held.
P_sat(Δ) per model, family and condition type, with bootstrap CIs over base cases. Resolution on each side = the
smallest |Δ| from which P_sat stays ≤ 0.1 (below) or ≥ 0.9 (above) at all larger distances on that side.

**Predictions fixed now.**
- P1b-1 (resolution, not identity): for NLI-init models P_sat is monotone in Δ on both sides, and the below-cutoff
  resolution for thresholds is larger than one unit.
- P1b-2 (late bias for dates): for NLI-init models the date PSE lies strictly above 0 (P_sat(+1 day) < 0.5 and
  P_sat(+7 days) < P_sat(+365 days)).
- P1b-3 (relative scale, Weber-like): for thresholds, P_sat at the same *relative* distance differs by less between
  enrollment (small integers) and research_funding (large amounts) than P_sat at the same *absolute* number of units
  (±1 unit). Tested descriptively; with 30 base cases per family it is a pointer, not a test.
- Generic-init models: P_sat ≈ 1 at every Δ (they ignore the condition), as Pilot 1 suggests; if not, the Pilot 1
  reading of these models is wrong.

## Addendum 2 (written after Pilot 1b, before looking at any test-set breakdown of this kind; declared post hoc)

Pilot 1b showed non-monotone psychometric curves for the NLI-init models. Exploring the Pilot 1b items (dev family
vehicles and the probe items for enrollment and research_funding; not the registered test split), two surface
heuristics fit the deviations:

- **H_lex (digit-string order for amounts).** In research_funding, case values *below* the cutoff that have fewer
  digits but a larger leading digit (e.g. €720,000 vs a cutoff of €1,440,000) were read as satisfied in 0.97 / 0.93
  of cases (paired / unpaired), against 0.57 / 0.51 for below-cutoff values with the same number of digits.
  No clear effect for small integers (enrollment, vehicles).
- **H_md (year-blind dates).** Dates *before* the cutoff whose month-and-day is later than the cutoff's (an earlier
  year) were read as satisfied in 0.54 / 0.36 of cases, against 0.09 / 0.00 when the month-and-day is earlier.

Because these hypotheses were formed on the probe data, they are tested on **independent items**: the registered
test split (2,560 items; enrollment and research_funding), using the **stored predictions** of all registered NLI-init
fine-tuned runs (paired, unpaired, operator hold-out; seeds 0–2; nine runs). No new inference and no model or epoch
selection are involved. Script: `scripts/lexical_comparison_test.py`.

**Items.** Every test item whose spec has a threshold (resp. date) condition and whose case states the value, and
for which the condition is *decisive*: setting the value just above the cutoff and at the cutoff gives different gold
labels (other conditions held as they are). `sat_label` = the label with the condition satisfied. "Satisfied
reading" = prediction equals `sat_label`. Only items with the value **below or at** the cutoff are used (that is where
both heuristics predict false "satisfied" readings).

**Contrasts, fixed now.**
- H_lex: among research_funding threshold items below the cutoff, P_sat(lex-greater) − P_sat(other), where
  lex-greater = fewer digits and a larger leading digit than the cutoff. Distance control: the same contrast
  restricted to items whose value lies between 0.3 and 0.9 of the cutoff (both groups occur there).
- H_md: among date items before the cutoff, P_sat(month-day later) − P_sat(month-day earlier). Distance control:
  restricted to items 1–365 days before the cutoff.

**Predictions.** Each heuristic is *supported on independent data* if the pooled contrast (nine runs) is ≥ 0.15 with a
95% cluster-bootstrap CI (over minimal pairs) excluding 0, the distance-controlled contrast has the same sign with
point estimate ≥ 0.10, and at least 7 of 9 runs show a positive contrast. If a group has fewer than 10 items the
contrast is reported as not testable. Generic-init runs are reported for reference only (Pilot 1b suggests they
ignore isolated conditions entirely). Whatever the outcome, it is reported.
