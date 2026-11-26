# Project Anomaly

Exploratory search for a small, surprising and well-supported result in ClauseShift, on a separate branch.
Nothing here changes the registered study, `data/`, or `research_next/`. All results are exploratory.

**Outcome in one paragraph.** Our own hypothesis — that boundary errors come from the value being a verbatim copy of
the cutoff — is false. Psychometric probes show instead that the models' comparisons are non-monotone and that
generic-init models ignore isolated threshold and date conditions altogether. Following the probes, we found that
fine-tuned models trained with date edits fail on dates in an earlier year but later in the calendar than the cutoff
(26–51% accuracy in six runs), while runs trained without date edits are perfect there (three runs). This is post hoc
and confounded with training-set size; a small preregistered training check is proposed (needs approval).

| File | Content |
|---|---|
| `ANOMALY_LOG.md` | Anomalies A1–A14 with competing explanations |
| `UNCONVENTIONAL_IDEAS.md` | Conventional ideas we avoided; ideas from other disciplines |
| `DISCOVERY_TOURNAMENT.md` | 16 candidates, scores, selection, outcome |
| `PILOT_PROTOCOL.md` | Predictions fixed before each pilot (with two declared addenda) |
| `PILOT_RESULTS.md` | All outcomes, including failed predictions; deviations; compute used |
| `MATHEMATICAL_NOTES.md` | Propositions on single-input criteria, symmetrised decoding, psychometric identifiability |
| `NOVELTY_MATRIX.md` | What is known, transferred, observed or candidate-new |
| `ADVERSARIAL_REVIEW.md` | Objections and what would settle them |
| `RESEARCH_DECISION.md` | The ten questions; CONDITIONAL GO for one check |
| `AUTHOR_STUDY_GUIDE.md` | Exercises, tasks and open questions for the researcher |
| `scripts/`, `results/`, `figures/`, `configs/` | Code, raw predictions and tables (tests in `tests/test_project_anomaly.py`) |

Reproduce (CPU, ≈ 30 minutes; the four fine-tuned checkpoints are not in the repository and must be re-trained with
the registered recipe, see `CLOUD_RESUME.md`):

```bash
python project_anomaly/scripts/make_boundary_probes.py
python project_anomaly/scripts/run_models.py project_anomaly/results/boundary_probes.jsonl pilot1
python project_anomaly/scripts/analyze_pilot1.py
python project_anomaly/scripts/make_negation_probes.py
python project_anomaly/scripts/run_models.py project_anomaly/results/negation_probes.jsonl pilot2 --zero-shot
python project_anomaly/scripts/analyze_pilot2.py
python project_anomaly/scripts/make_psychometric_probes.py
python project_anomaly/scripts/run_models.py project_anomaly/results/psychometric_probes.jsonl pilot1b
python project_anomaly/scripts/analyze_pilot1b.py
python project_anomaly/scripts/lexical_comparison_test.py
python project_anomaly/scripts/year_blindness.py
```

AI-assisted work: produced by an AI coding assistant under the researcher's direction; no human annotations or
human-run experiments are reported.
