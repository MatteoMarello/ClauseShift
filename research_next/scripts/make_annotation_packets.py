"""Create blind, independently shuffled annotation packets for several annotators (HUMAN_VALIDATION_PROTOCOL.md).

Usage: python make_annotation_packets.py <sheet.csv> <out_dir> <n_annotators> [--calibration 24,78] [--seed 2027]
- Each annotator gets `packet_<ID>.csv` with its own random item order, empty label/comment/ambiguity columns, and no
  item ids, operators, generator labels or LLM annotations.
- Calibration rows (default: 24 and 78, flagged by the LLM audit) are moved to the top and marked; they are excluded
  from agreement statistics by `score_human_annotations.py`.
- The coordinator keeps `coordinator_map.csv` (packet position -> sheet row). Do not send it to annotators.
Never writes into review/; never reads the key file.
"""

import argparse
import csv
import random
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("sheet")
ap.add_argument("out_dir")
ap.add_argument("n", type=int)
ap.add_argument("--calibration", default="24,78")
ap.add_argument("--seed", type=int, default=2027)
a = ap.parse_args()
rows = list(csv.DictReader(open(a.sheet, encoding="utf-8")))
calib = {c.strip() for c in a.calibration.split(",") if c.strip()}
out = Path(a.out_dir)
out.mkdir(parents=True, exist_ok=True)
rng = random.Random(a.seed)
ids = [f"A{i + 1:02d}" for i in range(a.n)]
with open(out / "coordinator_map.csv", "w", newline="", encoding="utf-8") as fm:
    wm = csv.writer(fm)
    wm.writerow(["annotator", "position", "sheet_row", "calibration"])
    for ann in ids:
        body = [r for r in rows if r["row"] not in calib]
        rng.shuffle(body)
        ordered = [r for r in rows if r["row"] in calib] + body
        with open(out / f"packet_{ann}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["position", "calibration", "document", "hypothesis", "label (entailed/contradicted/insufficient)",
                        "ambiguous (yes/no)", "comment"])
            for pos, r in enumerate(ordered):
                is_cal = r["row"] in calib
                w.writerow([pos, "yes" if is_cal else "no", r["document"], r["hypothesis"], "", "", ""])
                wm.writerow([ann, pos, r["row"], "yes" if is_cal else "no"])
print(f"wrote {a.n} packets of {len(rows)} items ({len(calib)} calibration) to {out}")
