"""Pilot 3 (exploratory): how many items are needed to identify a model's program?

Bayesian adaptive testing over the 648-program lattice of program_fingerprint.py. A model's saved test predictions
act as the oracle. Likelihood: the model agrees with a program's label with probability 1-eps, otherwise it outputs
one of the two other labels uniformly. Items are chosen to maximise the entropy of the posterior predictive label
distribution (expected information gain under this symmetric noise model), and compared with random item order.

Target: the programs whose agreement on all 2,560 test items is within 0.01 of the best program ("full-data
programs"). Success at step k: at least 90% of the posterior mass lies on these programs from step k onwards (a
posterior-mode criterion would be biased by tie-breaking under the uniform prior).
Outputs research_next/results/adaptive_identification.json.
"""

import contextlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    import program_fingerprint as pf  # noqa: E402  (re-generates specs and program predictions)

EPS, MAXK, N_RANDOM = 0.1, 300, 20
LAB = {"entailed": 0, "contradicted": 1, "insufficient": 2}
PP = np.vectorize(LAB.get)(pf.prog_preds["test"])          # programs x items
n_prog, n_items = PP.shape
onehot = np.stack([(PP == l) for l in range(3)], axis=-1).astype(float)   # P x I x 3


def run(oracle: np.ndarray, order: str, rng) -> list[int]:
    logw = np.zeros(n_prog)
    asked = np.zeros(n_items, bool)
    full_agree = (PP == oracle).mean(1)
    target = full_agree.max()
    hits = []
    for k in range(MAXK):
        w = np.exp(logw - logw.max())
        w /= w.sum()
        if order == "adaptive":
            pred = EPS / 2 + (1 - 1.5 * EPS) * np.einsum("p,pil->il", w, onehot)
            ent = -(pred * np.log(pred)).sum(1)
            ent[asked] = -1
            i = int(ent.argmax())
        else:
            i = int(rng.choice(np.flatnonzero(~asked)))
        asked[i] = True
        logw += np.where(PP[:, i] == oracle[i], np.log(1 - EPS), np.log(EPS / 2))
        w = np.exp(logw - logw.max())
        w /= w.sum()
        hits.append(int(w[full_agree >= target - 0.01].sum() >= 0.9))
    return hits


def first_stable(h: list[int]) -> int | None:
    for k in range(len(h)):
        if all(h[k:]):
            return k + 1
    return None


systems = ["zeroshot_nli-deberta-v3-base_factsinpremise", "zeroshot_roberta-large-mnli_factsinpremise",
           "zeroshot_DeBERTa-v3-base-mnli-fever-anli", "ft_nli-deberta-v3-xsmall_paired_s1",
           "ft_nli-deberta-v3-xsmall_unpaired_s0", "ft_deberta-v3-xsmall_unpaired_s0", "ft_deberta-v3-xsmall_paired_s0"]
res = {}
for s in systems:
    P = {r["id"]: r["pred"] for r in map(json.loads, open(ROOT / "results/predictions" / s / "test.jsonl"))}
    oracle = np.array([LAB[P[i["id"]]] for i in pf.items["test"]])
    a = first_stable(run(oracle, "adaptive", None))
    rnd = [first_stable(run(oracle, "random", np.random.default_rng(r))) for r in range(N_RANDOM)]
    rnd_ok = [x for x in rnd if x is not None]
    res[s] = {"adaptive_items": a, "random_items_median": float(np.median(rnd_ok)) if rnd_ok else None,
              "random_runs_not_identified_within_max": sum(x is None for x in rnd), "max_items": MAXK}
    print(s, res[s], flush=True)
(ROOT / "research_next/results/adaptive_identification.json").write_text(json.dumps(res, indent=1))
