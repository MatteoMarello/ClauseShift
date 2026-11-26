# research_next — towards a publishable contribution

Exploratory research phase that follows the completed, preregistered ClauseShift v2 study. Nothing here modifies the
original data, predictions or results. Three layers are kept apart: **original** (`docs/`, `results/`),
**exploratory** (this folder: audit and pilots), **confirmatory** (`EXPERIMENT_PROTOCOL.md`, draft, not run).

Start with [`DECISION_MEMO.md`](DECISION_MEMO.md).

| File | Content |
|---|---|
| `DECISION_MEMO.md` | Recommended direction, evidence for and against, needs, CONDITIONAL GO |
| `LITERATURE_REVIEW.md`, `RELATED_WORK_MATRIX.md` | Literature with explicit reading status |
| `SCIENTIFIC_AUDIT.md` | Audit of the existing results (confounds, artefacts, metric problems) |
| `RESEARCH_QUESTIONS.md` | Five falsifiable questions and their evidence |
| `NOVELTY_ASSESSMENT.md` | What is already known, what may be new |
| `PILOT_PLAN.md` | Pilot predictions, committed before the pilots ran |
| `PILOT_RESULTS.md` | Pilot results, verdicts on the fixed predictions, deviations |
| `EXPERIMENT_PROTOCOL.md` | Confirmatory protocol draft (to be frozen by the author) |
| `HUMAN_VALIDATION_PROTOCOL.md` | Blind annotation protocol (not yet run) |
| `PUBLICATION_ROADMAP.md` | Venues (verified dates), what each level needs, candidate paper |
| `RESEARCH_STUDY_GUIDE.md` | Reading list, maths, exercises, interview and reviewer questions |
| `scripts/` | Audit, lazy reader, program identification, probes, adaptive identification, transition tests |
| `results/` | Generated tables and JSON (never edited by hand) |

Reproduce (CPU): `python research_next/scripts/audit_saved_predictions.py`, `lazy_reader.py`, `lazy_agreement.py`,
`program_fingerprint.py`, `adaptive_identification.py` need only saved predictions. `retrain_for_probes.sh` re-trains
four registered configurations (~65 min) and keeps weights in the gitignored `checkpoints/`; `make_probes.py`,
`eval_probes.py`, `probe_paired_tests.py` and `fixed_set_transitions.py` then evaluate them.
