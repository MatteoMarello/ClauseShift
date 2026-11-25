# ClauseShift — instructions for Claude Code

- Research repo. All public text in English. Never invent results: every number must come from a file in
  `results/` produced by a script in `scripts/`.
- `data/` (v2) is frozen: do not regenerate or edit it. Hashes in `data/manifest.json` must not change.
  `docs/PREREGISTRATION.md` lists the preregistered analyses; anything else is reported as exploratory.
- Test split = families `enrollment`, `research_funding`. Never use test for model or epoch selection.
- Labels are generator-derived. The [blinded LLM audit](review/clauseshift_llm_audit.md) matched 112/112 sampled
  labels. Reserve claims of human validation for an independent human annotation pass.
- Before committing: `python -m pytest -q` must pass; regenerate tables with `python scripts/analyze.py` and
  `python scripts/error_analysis.py` (never edit `results/RESULTS.md` by hand).
- Read `CLOUD_RESUME.md` for what has been run and what remains.
- Do not commit model weights or checkpoints (`.gitignore`).
