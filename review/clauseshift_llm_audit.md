# ClauseShift independent LLM annotation audit

## Scope and method

One LLM annotator (ChatGPT) read all 112 document–hypothesis items from `review/annotation_sheet.csv` at commit `b896a772a35fb76b04c4ea2a8532eadd7f0ba05b`. The sample contains 56 minimal pairs across two fictional rule families (enrollment and research funding), with four pairs per edit operator. Each row received an entailment label and a short rationale. The annotator used only the rule text and the case facts stated in the item. Missing facts or silence about the relevant obligation were treated as insufficient evidence. Explicit scope restrictions, exemptions, and negations could settle the claim, including a claim about the absence of an obligation.

The [annotation CSV](clauseshift_llm_annotations.csv) was written and hashed before the generator key was opened. Its SHA-256 is `32c2c1a1bfc4042428f7a7ce4dbc2ed3532a0e66022470c8a99e7a7c37007f96`. The comparison joined unique row IDs and checked that all 112 IDs occurred in both inputs. Human annotation fields were left empty. The [metrics file](clauseshift_llm_metrics.json) records the source hashes, marginal counts implied by the confusion matrix, pair agreement, operator breakdown, and flagged rows.

## Agreement

Raw agreement was **112/112 (100%)**, with **Cohen’s κ = 1.000**. Both items matched the generator in all 56 pairs. Each of the 14 edit operators had 8/8 matches.

| Generator label | LLM entailed | LLM contradicted | LLM insufficient |
|---|---:|---:|---:|
| Entailed | 49 | 0 | 0 |
| Contradicted | 0 | 43 | 0 |
| Insufficient | 0 | 0 | 20 |

Raw agreement is the diagonal sum divided by 112. Chance agreement from the two label marginals is `(49² + 43² + 20²) / 112² = 0.370695`. Cohen’s κ is `(observed − expected) / (1 − expected)`.

## Disagreements and wording

There were zero disagreements and no systematic label error was observed in this sample. Rows **24 and 78** were flagged for the same potential ambiguity. Each claims that a project is exempt from a data-management-plan obligation after the relevant article is changed to concern a different kind of report. The label is `insufficient` under an open-world reading. If a reader interprets the excerpt as an exhaustive list of obligations, they could read the negative hypothesis as supported. Give human reviewers an explicit convention about omitted obligations and retain both examples as calibration cases.

## Interpretation

This is a single-annotator consistency audit of a structured synthetic sample. The paired items share their case facts, and the sample covers only two of the eight fictional families. Perfect observed agreement therefore establishes neither human agreement nor label accuracy across the full dataset. Keep the original blinded sheet for human review, and withhold these annotations and the generator key from those reviewers until they submit their labels.
