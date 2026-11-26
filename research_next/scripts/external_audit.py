"""Identifiability audit of external benchmarks (HANS, ScoNe-NLI). Plan: research_next/EXTERNAL_AUDIT_PLAN.md.

Usage: python external_audit.py <path to tommccoy1/hans clone> <path to selenashe/ScoNe clone>
Outputs: research_next/results/external/EXTERNAL_AUDIT.md and external_audit.json.

For each benchmark: heuristic programs H (fixed in the plan), the intended rule (gold labels), and
  - separation matrix D[x, h] = 1[h(x) != gold(x)], coverage c(h) = mean_x D[x, h];
  - pairwise distinguishability n(h, h') = #{x : h(x) != h'(x)}, including the gold rule as a hypothesis;
  - an exact minimum discriminating set: the smallest set of items that separates every distinguishable pair of
    hypotheses (minimum hitting set, solved exactly over item "signatures" = vectors of hypothesis predictions);
  - model identification: item agreement of each model with each hypothesis; ties reported as equivalence classes.
"""

import collections
import csv
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research_next/results/external"
OUT.mkdir(parents=True, exist_ok=True)
HANS, SCONE = Path(sys.argv[1]), Path(sys.argv[2])


# ---------------------------------------------------------------------------------------------- generic audit
def audit(name: str, items: list[dict], hyps: dict, models: dict[str, dict]) -> tuple[dict, list[str]]:
    """items: dicts with 'id', 'gold', 'group'; hyps: name -> {id: label}; models: name -> {id: label}."""
    H = {"GOLD": {it["id"]: it["gold"] for it in items}, **hyps}
    names = list(H)
    ids = [it["id"] for it in items]
    res, L = {"n_items": len(ids)}, [f"## {name}", "", f"{len(ids)} items. Hypotheses: {', '.join(names)}.", ""]

    # coverage
    groups = sorted({it["group"] for it in items})
    L += ["**Coverage**: share of items on which a heuristic disagrees with the gold label, overall and by group.", "",
          "| Heuristic | Overall | " + " | ".join(groups) + " |", "|---|---|" + "---|" * len(groups)]
    res["coverage"] = {}
    for h in names[1:]:
        tot = sum(H[h][i] != H["GOLD"][i] for i in ids) / len(ids)
        byg = []
        for g in groups:
            gi = [it["id"] for it in items if it["group"] == g]
            byg.append(sum(H[h][i] != H["GOLD"][i] for i in gi) / len(gi))
        res["coverage"][h] = {"overall": tot, "by_group": dict(zip(groups, byg))}
        L.append(f"| {h} | {tot:.3f} | " + " | ".join(f"{v:.2f}" for v in byg) + " |")

    # pairwise distinguishability
    L += ["", "**Pairwise distinguishability**: number of items on which two hypotheses disagree (0 = indistinguishable).", "",
          "| | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    pw = {}
    for a in names:
        row = []
        for b in names:
            n = sum(H[a][i] != H[b][i] for i in ids)
            pw[(a, b)] = n
            row.append(str(n))
        L.append(f"| {a} | " + " | ".join(row) + " |")
    indist = [(a, b) for a, b in itertools.combinations(names, 2) if pw[(a, b)] == 0]
    res["pairwise"] = {f"{a}|{b}": n for (a, b), n in pw.items()}
    res["indistinguishable_pairs"] = indist
    L += ["", "Indistinguishable pairs: " + (", ".join(f"{a} ≡ {b}" for a, b in indist) if indist else "none"), ""]

    # minimum discriminating set (exact, over signatures)
    sig = collections.defaultdict(list)
    for i in ids:
        sig[tuple(H[h][i] for h in names)].append(i)
    targets = [(a, b) for a, b in itertools.combinations(range(len(names)), 2) if pw[(names[a], names[b])] > 0]
    best = None
    sigs = list(sig)
    for k in range(1, len(sigs) + 1):
        for combo in itertools.combinations(sigs, k):
            if all(any(s[a] != s[b] for s in combo) for a, b in targets):
                best = combo
                break
        if best:
            break
    res["min_discriminating_set_size"] = len(best) if best else None
    res["n_signatures"] = len(sigs)
    examples = [sig[s][0] for s in best] if best else []
    res["min_discriminating_examples"] = examples
    grp = {it["id"]: it["group"] for it in items}
    L += [f"**Minimum discriminating set**: {len(best) if best else 'n/a'} items suffice to separate all "
          f"{len(targets)} distinguishable pairs of hypotheses (exact; {len(sigs)} distinct item signatures). "
          "One choice: " + ", ".join(f"{e} ({grp[e]})" for e in examples) + ".", ""]

    # model identification
    if models:
        L += ["**Model identification** (item agreement with each hypothesis; best in bold; ties are equivalence classes).", "",
              "| Model | " + " | ".join(names) + " | Best (ties) |", "|---|" + "---|" * (len(names) + 1)]
        res["models"] = {}
        for m, P in models.items():
            ag = {h: sum(P[i] == H[h][i] for i in ids) / len(ids) for h in names}
            top = max(ag.values())
            best_h = [h for h in names if abs(ag[h] - top) < 1e-12]
            res["models"][m] = {"agreement": ag, "best": best_h}
            L.append(f"| {m} | " + " | ".join((f"**{ag[h]:.3f}**" if h in best_h else f"{ag[h]:.3f}") for h in names)
                     + f" | {' ≡ '.join(best_h)} |")
        L.append("")
    return res, L


# ---------------------------------------------------------------------------------------------- HANS
def norm(s: str) -> list[str]:
    return [t for t in s.lower().replace(" .", "").split() if t != "."]


def subtree_yields(parse: str) -> set[tuple]:
    toks = re.findall(r"\(|\)|[^\s()]+", parse)
    stack, yields = [], set()
    i = 0
    while i < len(toks):
        t = toks[i]
        if t == "(":
            stack.append([])
            i += 2 if i + 1 < len(toks) and toks[i + 1] not in "()" else 1  # skip label
            continue
        if t == ")":
            words = stack.pop()
            if words:
                yields.add(tuple(w.lower() for w in words if w != "."))
            if stack:
                stack[-1].extend(words)
        else:
            stack[-1].append(t)
        i += 1
    return yields


hans = [json.loads(l) for l in open(HANS / "heuristics_evaluation_set.jsonl")]
items, hyp = [], {"LO": {}, "SUB": {}, "CONST": {}, "ALL_E": {}, "ALL_N": {}}
E, N = "entailment", "non-entailment"
for r in hans:
    p, h = norm(r["sentence1"]), norm(r["sentence2"])
    i = r["pairID"]
    items.append({"id": i, "gold": r["gold_label"], "group": r["heuristic"]})
    hyp["LO"][i] = E if set(h) <= set(p) else N
    hyp["SUB"][i] = E if any(p[k:k + len(h)] == h for k in range(len(p) - len(h) + 1)) else N
    hyp["CONST"][i] = E if tuple(h) in subtree_yields(r["sentence1_parse"]) else N
    hyp["ALL_E"][i], hyp["ALL_N"][i] = E, N
models = {}
for fn, name in (("bert_preds.txt", "BERT"), ("esim_heur_preds.txt", "ESIM"),
                 ("decomp_attn_heur_preds.txt", "DecompAttn"), ("spinn_preds_heur.txt", "SPINN")):
    rows = list(csv.reader(open(HANS / fn)))[1:]
    models[name] = {r[0]: (E if r[1].strip() == "entailment" else N) for r in rows}
# sanity: each heuristic must predict entailment on the items of its own subset (definition check)
check = {h: sum(hyp[h][it["id"]] == E for it in items if it["group"] == g) / 10000
         for h, g in (("LO", "lexical_overlap"), ("SUB", "subsequence"), ("CONST", "constituent"))}
hans_res, hans_L = audit("HANS (evaluation set)", items, hyp, models)
hans_res["definition_check_entailment_rate_on_own_subset"] = check
hans_L.insert(3, f"Definition check (share of a heuristic's own subset on which it predicts entailment; should be "
                 f"1.0): {', '.join(f'{k} {v:.3f}' for k, v in check.items())}.")
hans_L.insert(4, "")

# ---------------------------------------------------------------------------------------------- ScoNe
SPLITS = {"no_negation": (0, 0), "one_not_scoped": (1, 0), "one_scoped": (1, 1),
          "one_scoped_one_not_scoped": (2, 1), "two_not_scoped": (2, 0), "two_scoped": (2, 2)}
base = {}
rows = {}
for sp in SPLITS:
    rows[sp] = list(csv.DictReader(open(SCONE / "scone_nli/test" / f"{sp}.csv")))
for i, r in enumerate(rows["no_negation"]):
    base[i] = r["gold_label_edited"]
flip = {"entailment": "neutral", "neutral": "entailment"}
rules = {"RULE": lambda n, s: s % 2 == 1, "IGNORE": lambda n, s: False, "PRESENCE": lambda n, s: n >= 1,
         "PARITY_ALL": lambda n, s: n % 2 == 1, "ANY_SCOPE": lambda n, s: s >= 1, "ONE_SCOPE": lambda n, s: s == 1}
items, hyp = [], {k: {} for k in list(rules) + ["ALL_E", "ALL_N"]}
mismatch = 0
for sp, (n, s) in SPLITS.items():
    for i, r in enumerate(rows[sp]):
        g = r.get("gold_label_edited") or r["gold_label"]
        iid = f"{sp}:{i}"
        items.append({"id": iid, "gold": g, "group": sp})
        for k, f in rules.items():
            hyp[k][iid] = flip[base[i]] if f(n, s) else base[i]
        hyp["ALL_E"][iid], hyp["ALL_N"][iid] = "entailment", "neutral"
        mismatch += hyp["RULE"][iid] != g
models = {}
pf = OUT / "scone_predictions.jsonl"
if pf.exists():
    for r in map(json.loads, open(pf)):
        models.setdefault(r["model"].replace("zeroshot_", ""), {})[f"{r['split']}:{r['row']}"] = r["pred"]
scone_res, scone_L = audit("ScoNe-NLI (test)", items, hyp, models)
scone_res["rule_vs_gold_mismatches"] = mismatch
scone_L.insert(3, f"Check: the intended rule (flip iff an odd number of negations scope over the lexical item) "
                  f"disagrees with the gold label on {mismatch} of {len(items)} items.")
scone_L.insert(4, "")

L = ["# External identifiability audit (generated by research_next/scripts/external_audit.py)", "",
     "Plan and heuristic definitions: `research_next/EXTERNAL_AUDIT_PLAN.md`. Licences: HANS MIT; ScoNe CC0 1.0.", ""]
(OUT / "external_audit.json").write_text(json.dumps({"HANS": hans_res, "ScoNe": scone_res}, indent=1, default=str))
(OUT / "EXTERNAL_AUDIT.md").write_text("\n".join(L + hans_L + scone_L) + "\n")
print("\n".join(L + hans_L + scone_L))
