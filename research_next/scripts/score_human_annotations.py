"""Score completed human annotation packets (run only on real annotations; never on simulated ones).

Usage: python score_human_annotations.py <packet_dir> <key.csv>
Reads packet_<ID>.csv files and coordinator_map.csv from <packet_dir>, and the generator key (review/annotation_key.csv)
only AFTER all packets are complete. Reports, excluding calibration items:
  - inter-annotator agreement: Fleiss' kappa and Krippendorff's alpha (nominal), with 95% bootstrap intervals over items;
  - majority label vs. generator label: raw agreement and Cohen's kappa, overall and per operator;
  - pair level: share of minimal pairs whose two sides both match the generator by majority;
  - items without a majority, and items where the majority disagrees with the generator (for adjudication).
Output: <packet_dir>/human_agreement.json
"""

import collections
import csv
import json
import sys
from pathlib import Path

import numpy as np

LABS = ["entailed", "contradicted", "insufficient"]
d, keyf = Path(sys.argv[1]), sys.argv[2]
mp = list(csv.DictReader(open(d / "coordinator_map.csv", encoding="utf-8")))
key = {r["row"]: r for r in csv.DictReader(open(keyf, encoding="utf-8"))}
ann = collections.defaultdict(dict)                         # sheet_row -> annotator -> label
for f in sorted(d.glob("packet_*.csv")):
    a = f.stem.split("_", 1)[1]
    pos2row = {m["position"]: (m["sheet_row"], m["calibration"]) for m in mp if m["annotator"] == a}
    for r in csv.DictReader(open(f, encoding="utf-8")):
        row, cal = pos2row[r["position"]]
        lab = r["label (entailed/contradicted/insufficient)"].strip().lower()
        if cal == "no":
            if lab not in LABS:
                sys.exit(f"incomplete or invalid label in {f.name}, position {r['position']}: '{lab}'")
            ann[row][a] = lab
rows = sorted(ann, key=int)
A = sorted({a for r in rows for a in ann[r]})
M = np.array([[sum(ann[r][a] == l for a in A) for l in LABS] for r in rows])   # items x labels counts
n = M.sum(1)[0]


def fleiss(Mx):
    p = Mx.sum(0) / Mx.sum()
    Pi = ((Mx ** 2).sum(1) - n) / (n * (n - 1))
    return (Pi.mean() - (p ** 2).sum()) / (1 - (p ** 2).sum())


def kalpha(Mx):
    tot = Mx.sum()
    Do = sum((Mx[i].sum() ** 2 - (Mx[i] ** 2).sum()) / (Mx[i].sum() - 1) for i in range(len(Mx))) / tot
    nc = Mx.sum(0)
    De = (tot ** 2 - (nc ** 2).sum()) / (tot * (tot - 1))
    return 1 - Do / De


rng = np.random.default_rng(0)
bs = [rng.integers(0, len(rows), len(rows)) for _ in range(2000)]
res = {"annotators": A, "items": len(rows),
       "fleiss_kappa": float(fleiss(M)), "fleiss_ci": [float(np.percentile([fleiss(M[b]) for b in bs], q)) for q in (2.5, 97.5)],
       "krippendorff_alpha": float(kalpha(M)),
       "alpha_ci": [float(np.percentile([kalpha(M[b]) for b in bs], q)) for q in (2.5, 97.5)]}
maj = {}
for i, r in enumerate(rows):
    top = M[i].max()
    maj[r] = LABS[int(M[i].argmax())] if (M[i] == top).sum() == 1 and top > n / 2 else None
gen = {r: key[r]["generator_label"] for r in rows}
ok = [r for r in rows if maj[r]]
po = np.mean([maj[r] == gen[r] for r in ok])
h = collections.Counter(maj[r] for r in ok)
g = collections.Counter(gen[r] for r in ok)
pe = sum(h[l] * g[l] for l in LABS) / len(ok) ** 2
res.update({"items_with_majority": len(ok), "majority_vs_generator_agreement": float(po),
            "majority_vs_generator_kappa": float((po - pe) / (1 - pe)),
            "no_majority_items": [key[r]["id"] for r in rows if not maj[r]],
            "majority_disagrees_with_generator": [key[r]["id"] for r in ok if maj[r] != gen[r]]})
byop = collections.defaultdict(list)
for r in ok:
    byop[key[r]["operator"]].append(maj[r] == gen[r])
res["by_operator"] = {k: float(np.mean(v)) for k, v in sorted(byop.items())}
pairs = collections.defaultdict(list)
for r in ok:
    pairs[key[r]["id"].rsplit("-", 1)[0]].append(maj[r] == gen[r])
res["pairs_both_sides_match"] = float(np.mean([all(v) for v in pairs.values() if len(v) == 2]))
(d / "human_agreement.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1))
