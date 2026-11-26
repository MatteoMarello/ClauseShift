"""Label check of the critical year-blindness test items by specification logic (no human judgement involved).

Critical items: date-decisive test items whose case date lies in an earlier calendar year than the cutoff but later
in the calendar (month, day), i.e. the cell `cross / not_after` of YEAR_BLINDNESS.md.

Three independent routes must agree for every item:
  1. the stored gold label (generator's `gold_label`);
  2. the reference program of research_next (`program_fingerprint.run(REFERENCE, ...)`, a separate implementation);
  3. a text-only derivation: parse the cutoff date from the premise and the case date from the hypothesis, check that
     the date condition fails (event not strictly after the cutoff), check that the claimed obligation is the one the
     conditions attach to (Article 1), read the claim polarity from the claim wording, and derive the label
     (a failing condition => the obligation does not apply => "required" claims are contradicted, "not required"
     claims are entailed). A failing condition decides the label whatever the other conditions say.
This is a consistency check of generator-derived labels, not a human validation.
Output: project_anomaly/results/critical_label_check.json and CRITICAL_LABEL_CHECK.md
"""

import contextlib
import datetime as dt
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research_next/scripts"))
with contextlib.redirect_stdout(io.StringIO()):
    from program_fingerprint import REFERENCE, SPECS, run  # noqa: E402

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import CONTRADICTED, ENTAILED, fmt_date  # noqa: E402
from year_blindness import date_items  # noqa: E402

DATE_RE = re.compile(r"\b(\d{1,2}) (January|February|March|April|May|June|July|August|September|October|November|"
                     r"December) (\d{4})\b")
NEG_CLAIM = re.compile(r" is not required to | does not have to | has no obligation to ")


def parse(s: str) -> list[dt.date]:
    return [dt.datetime.strptime(" ".join(m), "%d %B %Y").date() for m in DATE_RE.findall(s)]


def main():
    test = {r["id"]: r for r in map(json.loads, open(ROOT / "data/test.jsonl"))}
    critical = [r for r in date_items("test") if r["cell"] == ("cross", "not_after")]
    rows, problems = [], []
    for c in critical:
        it = test[c["id"]]
        spec, case = SPECS[it["id"]]
        dom = DOMAINS[it["family"]]
        # route 3: text only
        cond_sents = [s for s in it["sentences"] if " after " in s and DATE_RE.search(s)]
        cut_text = parse(cond_sents[0]) if len(cond_sents) == 1 else []
        case_sents = [s for s in it["hypothesis"].split(". ") if DATE_RE.search(s)]
        case_text = parse(case_sents[0]) if len(case_sents) == 1 else []
        claim = it["hypothesis"].split(". ")[-1]
        neg = bool(NEG_CLAIM.search(" " + claim))
        obligation_in_article1 = dom["obligation"] in it["sentences"][0]
        text_label = None
        if len(cut_text) == 1 and len(case_text) == 1 and obligation_in_article1 and not case_text[0] > cut_text[0]:
            text_label = ENTAILED if neg else CONTRADICTED
        r = {"id": it["id"], "family": it["family"], "operator": it["operator"], "gold": it["label"],
             "reference_program": run(REFERENCE, spec, case), "text_derived": text_label,
             "cutoff_text": str(cut_text[0]) if cut_text else None, "case_date_text": str(case_text[0]) if case_text else None,
             "spec_matches_text": bool(cut_text and case_text and cut_text[0] == spec.date_cutoff
                                       and case_text[0] == case.date and fmt_date(spec.date_cutoff) in cond_sents[0]),
             "earlier_year_later_monthday": bool(case.date.year < spec.date_cutoff.year and
                                                 (case.date.month, case.date.day) >
                                                 (spec.date_cutoff.month, spec.date_cutoff.day)),
             "claim_negative": neg, "other_conditions": [k for k, v in (("threshold", spec.threshold),
                                                                         ("scope", spec.scope_loc),
                                                                         ("exception", spec.exception_cat),
                                                                         ("xref", spec.xref)) if v is not None],
             "premise": it["premise"], "hypothesis": it["hypothesis"]}
        r["all_agree"] = r["gold"] == r["reference_program"] == r["text_derived"] and r["spec_matches_text"] \
            and r["earlier_year_later_monthday"]
        if not r["all_agree"]:
            problems.append(r["id"])
        rows.append(r)
    out = {"n": len(rows), "all_agree": len(rows) - len(problems), "problems": problems, "items": rows}
    json.dump(out, open(ROOT / "project_anomaly/results/critical_label_check.json", "w", newline="\n"), indent=2)
    L = ["# Label check of the 35 critical items (generated by `project_anomaly/scripts/check_critical_labels.py`)", "",
         "Consistency check by specification logic, **not a human validation**. Routes: stored gold label; the "
         "independently implemented reference program of `research_next`; a text-only derivation from the premise "
         "and hypothesis strings (see the script docstring).", "",
         f"Items: {len(rows)}. All three routes agree, text matches the specification, and the item is in the "
         f"critical cell: **{len(rows) - len(problems)} / {len(rows)}**.", "",
         "| id | gold | cutoff | case date | claim | other conditions |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['id']} | {r['gold']} | {r['cutoff_text']} | {r['case_date_text']} | "
                 f"{'negative' if r['claim_negative'] else 'positive'} | {', '.join(r['other_conditions']) or '–'} |")
    (ROOT / "project_anomaly/results/CRITICAL_LABEL_CHECK.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:6]))
    print("problems:", problems)


if __name__ == "__main__":
    main()
