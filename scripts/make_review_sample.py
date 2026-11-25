"""Draw a blind, operator-stratified sample of test pairs for human annotation.

review/annotation_sheet.csv  : document, hypothesis, empty `human_label` column (no gold shown)
review/annotation_key.csv    : gold labels (do not open before annotating)
Then run scripts/score_review.py to compute agreement with the generator labels.
"""

import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from clauseshift.data import load  # noqa: E402
from clauseshift.generator import OPERATORS  # noqa: E402

PER_OPERATOR = 4   # 14 operators x 4 pairs x 2 sides = 112 items
rng = random.Random(2027)
test = load("test")
pairs = {}
for it in test:
    pairs.setdefault((it["operator"], it["pair_id"]), []).append(it)
rows = []
for op in OPERATORS:
    ids = sorted(pid for (o, pid) in pairs if o == op)
    for pid in rng.sample(ids, PER_OPERATOR):
        rows += sorted(pairs[(op, pid)], key=lambda x: x["side"])
order = list(range(len(rows)))
rng.shuffle(order)                         # sides of a pair are not adjacent in the sheet
Path("review").mkdir(exist_ok=True)
with open("review/annotation_sheet.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["row", "document", "hypothesis", "human_label (entailed/contradicted/insufficient)", "comment"])
    for r, i in enumerate(order):
        w.writerow([r, rows[i]["premise"], rows[i]["hypothesis"], "", ""])
with open("review/annotation_key.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["row", "id", "operator", "generator_label"])
    for r, i in enumerate(order):
        w.writerow([r, rows[i]["id"], rows[i]["operator"], rows[i]["label"]])
print(len(rows), "items written")
