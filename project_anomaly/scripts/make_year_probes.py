"""Year-blindness replication probes (YEAR_PROBE_PROTOCOL.md). Fresh seed; generator functions reused; data/ untouched.

One date condition per document ("after c"). Factors:
  MAIN  direction {before, after} x year relation {same, cross} x distance bin {1-30, 31-120, 121-300 days}
        x format {G "15 October 2024", US "October 15, 2024", ISO "2024-10-15"}; 20 base cases per family and cell.
        Month-day relation is implied: same-year cells are month-day consistent, cross-year cells month-day misleading.
  YEAR  same month and day, case year = cutoff year + k, k in {-2, -1, +1, +2}; 15 per family and k; format G.
  DAYMONTH same year: day-only (same month, 1-15 days) and month-only (same day, 1-5 months), before/after;
        15 per family and cell; format G.
Claim polarity alternates (balanced labels). Every label is checked against an independent implementation.
Output: project_anomaly/results/year_probes.jsonl
"""

import contextlib
import dataclasses
import datetime as dt
import io
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "research_next/scripts"))
with contextlib.redirect_stdout(io.StringIO()):
    from program_fingerprint import REFERENCE, run  # noqa: E402

from clauseshift.domains import DOMAINS  # noqa: E402
from clauseshift.generator import PairBuilder, Spec, document_text, fmt_date, gold_label, render_document, render_hypothesis  # noqa: E402

SEED = 20261201
FAMILIES = ("vehicles", "enrollment", "research_funding")
BINS = {"d001-030": (1, 30), "d031-120": (31, 120), "d121-300": (121, 300)}
YEARS = (2023, 2024, 2025, 2026)
N_MAIN, N_SMALL = 20, 15


def fmt(d: dt.date, form: str) -> str:
    return {"G": fmt_date(d), "US": f"{d.strftime('%B')} {d.day}, {d.year}", "ISO": d.isoformat()}[form]


def doy_date(year: int, doy: int) -> dt.date:
    return dt.date(year, 1, 1) + dt.timedelta(days=doy - 1)


def year_len(y: int) -> int:
    return (dt.date(y + 1, 1, 1) - dt.date(y, 1, 1)).days


def main_pair(rng, direction: str, rel: str, d: int):
    """Return (cutoff, case date) with |case - cutoff| = d days and the requested year relation."""
    y = rng.choice(YEARS)
    n = year_len(y)
    if direction == "before":           # case = cutoff - d
        doy = rng.randint(1, d) if rel == "cross" else rng.randint(d + 1, n)
        cut = doy_date(y, doy)
        return cut, cut - dt.timedelta(days=d)
    doy = rng.randint(n - d + 1, n) if rel == "cross" else rng.randint(1, n - d)   # case = cutoff + d
    cut = doy_date(y, doy)
    return cut, cut + dt.timedelta(days=d)


def safe_md(rng):
    m = rng.randint(1, 12)
    return m, rng.randint(1, 28)


def build():
    out = []
    for family in FAMILIES:
        rng = random.Random(f"{SEED}-{family}")
        b = PairBuilder(family, rng, allow_reserved=False)
        dom = DOMAINS[family]
        k = 0

        def emit(block, cell, cut, val, forms):
            nonlocal k
            case = b.case()
            case = dataclasses.replace(case, date=val, claim_polarity=1 if k % 2 == 0 else -1)
            surf = b.surface()
            spec = Spec(date_cutoff=cut)
            label = gold_label(spec, case)[0]
            assert label == run(REFERENCE, spec, case)
            sat_label = gold_label(spec, dataclasses.replace(case, date=cut + dt.timedelta(days=1)))[0]
            prem = document_text(render_document(dom, spec, surf))
            hyp = render_hypothesis(dom, case)
            assert prem.count(fmt_date(cut)) == 1 and hyp.count(fmt_date(val)) == 1
            base = f"{family}-{block}-{k:03d}"
            for form in forms:
                out.append({"id": f"{base}-{form}", "base": base, "family": family, "block": block, **cell,
                            "format": form, "cutoff": cut.isoformat(), "case_date": val.isoformat(),
                            "days": (val - cut).days, "premise": prem.replace(fmt_date(cut), fmt(cut, form)),
                            "hypothesis": hyp.replace(fmt_date(val), fmt(val, form)), "label": label,
                            "sat_label": sat_label, "truth_after": val > cut,
                            "md_after": (val.month, val.day) > (cut.month, cut.day)})
            k += 1

        for direction in ("before", "after"):
            for rel in ("same", "cross"):
                for bin_name, (lo, hi) in BINS.items():
                    for _ in range(N_MAIN):
                        cut, val = main_pair(rng, direction, rel, rng.randint(lo, hi))
                        assert (val.year == cut.year) == (rel == "same")
                        emit("main", {"direction": direction, "year_rel": rel, "bin": bin_name}, cut, val,
                             ("G", "US", "ISO"))
        for kk in (-2, -1, 1, 2):
            for _ in range(N_SMALL):
                m, dd = safe_md(rng)
                y = rng.choice(YEARS)
                emit("year", {"direction": "after" if kk > 0 else "before", "year_offset": kk},
                     dt.date(y, m, dd), dt.date(y + kk, m, dd), ("G",))
        for kind in ("day_only", "month_only"):
            for direction in ("before", "after"):
                for _ in range(N_SMALL):
                    y = rng.choice(YEARS)
                    if kind == "day_only":
                        m, delta = rng.randint(1, 12), rng.randint(1, 15)
                        d1 = rng.randint(1, 28 - delta)
                        a, c = dt.date(y, m, d1), dt.date(y, m, d1 + delta)
                    else:
                        dd, delta = rng.randint(1, 28), rng.randint(1, 5)
                        m1 = rng.randint(1, 12 - delta)
                        a, c = dt.date(y, m1, dd), dt.date(y, m1 + delta, dd)
                    cut, val = (c, a) if direction == "before" else (a, c)
                    emit("daymonth", {"direction": direction, "kind": kind}, cut, val, ("G",))
    return out


def main():
    out = build()
    with open(ROOT / "project_anomaly/results/year_probes.jsonl", "w", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(len(out), "items")


if __name__ == "__main__":
    main()
