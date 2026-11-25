"""Agreement between human annotations (review/annotation_sheet.csv) and generator labels."""

import collections
import csv

sheet = {r["row"]: r for r in csv.DictReader(open("review/annotation_sheet.csv", encoding="utf-8"))}
key = {r["row"]: r for r in csv.DictReader(open("review/annotation_key.csv", encoding="utf-8"))}
col = "human_label (entailed/contradicted/insufficient)"
done = [r for r in sheet if sheet[r][col].strip()]
if not done:
    raise SystemExit("No annotations yet.")
agree = [sheet[r][col].strip().lower() == key[r]["generator_label"] for r in done]
labs = ["entailed", "contradicted", "insufficient"]
h = collections.Counter(sheet[r][col].strip().lower() for r in done)
g = collections.Counter(key[r]["generator_label"] for r in done)
po = sum(agree) / len(done)
pe = sum(h[l] * g[l] for l in labs) / len(done) ** 2
print(f"annotated {len(done)}; raw agreement {po:.3f}; Cohen's kappa {(po - pe) / (1 - pe):.3f}")
for r in done:
    if sheet[r][col].strip().lower() != key[r]["generator_label"]:
        print("disagreement:", key[r]["id"], key[r]["operator"], "human", sheet[r][col], "generator", key[r]["generator_label"])
