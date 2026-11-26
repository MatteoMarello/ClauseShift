# Guided exercise: designing the new ClauseShift families yourself

Goal: write the new fictional rule families for the confirmatory study (`EXPERIMENT_PROTOCOL_v2.md`, preferably four
small families). This is your intellectual contribution to the study; the assistant must not write the final
families. Work through Parts 1–4, fill in `family_template.yaml` (Part 5), then run the validator (Part 6).
Budget: about 30–45 minutes per family, plus one review pass.

Look at one existing family first (`src/clauseshift/domains.py`, e.g. `enrollment`) and at how the generator uses
each field (`render_document`, `render_hypothesis`, `PairBuilder` in `src/clauseshift/generator.py`).

---

## Part 1 — What you must define, and why

| Field | What it is | Why it is needed | What can go wrong |
|---|---|---|---|
| `subj`, `subj_pl` | Who the rule applies to ("applicant(s)") | Every sentence of the rule mentions them; templates need singular and plural | Irregular plurals, articles ("a"/"an") breaking templates |
| `obligation` | The claimed obligation, as a verb phrase ("submit an English language certificate") | The hypothesis claims the case must / need not do this; `topic_swap` replaces it | A phrase that also appears inside `other_obligations` or distractors creates accidental topic matches (the lazy reader would exploit it) |
| `other_obligations` (3) | Obligations of other articles | Article 2 and `topic_swap` documents | Too similar to the claimed obligation → ambiguous topic; too different → trivially detectable topic swap |
| `categories` (4 × singular/plural) | Mutually exclusive subtypes of the subject ("transfer applicant") | Exemptions and cross-references name a category; the case belongs to one | **The main confound found so far**: categories differing in one word (vehicles: electric/hybrid/diesel/petrol cars) made category matching hard for every model. Make them lexically distinct (Part 2) |
| `loc_rel`, `locations` (6) | Relation and places for scope conditions ("educated in" + countries) | `scope_restrict` / `scope_near_miss` | Locations that are substrings of each other; real places with legal connotations are fine but keep them neutral |
| `num_rule`, `num_rule_fmt`, `case_num`, `num_range` | The numeric attribute in the rule and in the case | Threshold conditions; boundary items | Units that change tokenisation (€, thousands separators) are allowed but must be recorded; `num_range = [lo, hi, step]` must leave room above and below thresholds |
| `date_events`, `case_date` | The date attribute | Date cutoffs | Event wording that makes "after" ambiguous (e.g. "received on" vs. "starting"); the audit found a family difference on dates we could not explain — record your wording choice |
| `distractors` (5) | Unrelated articles | Distractor invariance; document length | Distractors mentioning a category, a place, a number or a date create spurious cues |
| `names` (≥ 15) | Case names | Hypotheses | Names reused from other families (leakage check); names that look like categories |

## Part 2 — How to avoid spurious correlations

1. **Lexical distinctness of categories.** For every pair of categories in a family, compute the token Jaccard
   similarity of the plural phrases (shared tokens / all tokens). Keep it ≤ 0.34 (the validator checks). Example of
   what to avoid: "owners of electric cars" vs. "owners of diesel cars" (Jaccard 0.50 after removing function words; a shared head noun alone, as in "transfer applicants" vs. "graduate applicants", gives 0.33 and passes).
2. **One planned similar pair.** In *one* family, deliberately include one pair of similar categories and mark it
   in the template (`similar_pair`). This turns the vehicles confound into a measured stratum.
3. **No category words elsewhere.** Category tokens must not appear in obligations, distractors or locations.
4. **Obligation uniqueness.** The claimed obligation's content words should not appear in other obligations.
5. **Balanced lengths.** Keep the four category phrases within ±2 tokens of each other, so that length does not
   identify the case category.
6. **No real-world legal facts.** Fictional rules only; avoid real regulations, institutions or persons.
7. **No overlap with existing families.** Different vocabulary from the eight existing families (the validator checks
   names, categories, obligations and locations).

## Part 3 — How to build discriminating cases

The confirmatory study needs items on which wrong programs and the intended rule disagree (FORMALIZATION §2–5).
For each family, check that your vocabulary makes these possible:

| Program to expose | Item that exposes it | What your family must allow |
|---|---|---|
| Lazy reader (ignores conditions) | Any decided item with a failing condition | At least one natural numeric and one date attribute |
| Non-strict comparison | Case value exactly at the cutoff | `num_range` step compatible with equality; dates as calendar days |
| Approximate comparison | Value at cutoff + 1 unit | Integer steps; avoid huge numbers where +1 looks like the same value |
| Article-token shortcut | Cross-reference to the obligation article naming *another* category; renumbered articles | Four categories; articles can be re-ordered |
| Exemption presence | Exemption for a category not in the family (nonce) | A plausible nonce category phrase |
| String matching | Exemption that paraphrases the case category | A synonym/paraphrase for each category (fill `category_paraphrases`) |

## Part 4 — How to verify logical correctness

1. **Mutual exclusivity**: can a case belong to two of your categories at once? It must not.
2. **Restrictive reading**: read each template with your vocabulary ("This requirement applies only if the number
   of credits … is more than 9 credits") — is the restriction unambiguous?
3. **Paraphrase faithfulness**: for each category paraphrase, would a careful reader treat it as the same category?
4. **Hand-label ten items**: after the validator passes, ask the assistant to *render* ten items with your family
   (rendering only, no labels shown), label them yourself, then compare with the generator's labels. Any
   disagreement is a template or vocabulary problem to fix before the freeze.
5. **Record decisions**: every choice you made for a reason (e.g. date wording) goes into `design_notes`.

## Part 5 — Template to fill in (copy to `research_next/families/<family_id>.yaml`)

```yaml
family_id: ""            # snake_case, new
subj: ""                 # singular
subj_pl: ""              # plural
obligation: ""           # verb phrase, no final period
other_obligations: ["", "", ""]
categories:              # [singular with article, plural]
  - ["", ""]
  - ["", ""]
  - ["", ""]
  - ["", ""]
category_paraphrases: ["", "", "", ""]   # one paraphrase of each plural phrase, same meaning
similar_pair: []         # optional: indices of the one deliberately similar pair, e.g. [0, 1]
nonce_category: ["", ""] # a category that does not exist in this family
loc_rel: ""              # e.g. "registered in"
locations: ["", "", "", "", "", ""]
case_loc: "{name} ... {loc}."
num_rule: ""             # e.g. "the length of the boat"
num_rule_fmt: "{v} ..."  # e.g. "{v} metres"
case_num: "{name} ... {v} ..."
num_range: [0, 0, 1]     # [lo, hi, step]
date_events: ""          # e.g. "moorings booked"
case_date: "{name} ... {d}."
distractors: ["", "", "", "", ""]
names: ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
design_notes: ""         # why you chose the wording you chose
```

## Part 6 — Validate

```bash
python research_next/scripts/validate_family.py research_next/families/<family_id>.yaml
```

The validator checks structure, placeholders, category distinctness (Jaccard), cross-field leakage, overlap with the
existing families, numeric range sanity and name uniqueness. It reports problems; it does not fix them and does not
generate any content. When all families pass, commit them **together with the frozen protocol** (one commit), and
only then generate the confirmatory data.
