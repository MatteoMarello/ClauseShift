# Annotator recruitment and blind annotation procedure

For the coordinator (the project author). Implements `HUMAN_VALIDATION_PROTOCOL.md`. No annotation has been done.
The assistant must not annotate, simulate annotators or fill packets.

## 1. Who to recruit

- **At least three** independent annotators (four recommended, so that one dropout leaves three).
- Fluent readers of English; no legal training needed (fictional rules, explicit conditions).
- Not involved in the project; must not have seen the generator, labels, LLM annotations or model outputs.
- The coordinator does not annotate items whose labels they have seen; they adjudicate instead.
- Check your university's rules on unpaid peer annotation of synthetic text (ethics approval is usually not
  required, but this is your responsibility). If you offer compensation, offer it equally to all.

## 2. Recruitment message (template; adapt and translate as needed)

> Subject: Help with a short reading-comprehension annotation (≈ 3 hours)
>
> Hi, I am running a small study on how language models read rule-like documents. I am looking for three or four
> people to label short fictional rules (e.g. eligibility conditions for a made-up scholarship) as "entailed",
> "contradicted" or "insufficient". No legal knowledge is needed. It takes about three hours in total and can be done
> in several sessions over one week. Your labels will be used only to check the quality of the dataset; your name
> will not be published unless you ask to be acknowledged. Would you be willing to help?

## 3. Information and consent (give before the packet)

- Purpose: checking whether the dataset's labels match careful human readings.
- Task: read each item, choose one label, optionally flag ambiguity and comment.
- Time: about 3 hours (Part A ≈ 1 h; Parts B and C later, after the confirmatory data exist).
- Data: only your labels, comments and an anonymous ID (A01, A02, …) are stored. No personal data.
- Voluntary: you can stop at any time; incomplete packets are discarded, not used partially.
- Acknowledgement: optional, by name, in any report or paper, only with your written agreement.
- Independence: please do not discuss items with other annotators until everyone has submitted.

## 4. Procedure

1. **Prepare packets** (coordinator):
   `python research_next/scripts/make_annotation_packets.py review/annotation_sheet.csv <private_dir> 3`
   Each annotator receives only `packet_A0x.csv` and the instructions below. Keep `coordinator_map.csv` private.
   Do not send `review/annotation_key.csv`, `review/clauseshift_llm_*` or anything from `results/`.
2. **Calibration**: the first two rows of every packet are calibration items (the two open-world cases flagged by the
   LLM audit). Discuss them with each annotator individually after they label them, using the convention in the
   instructions; they are excluded from agreement statistics.
3. **Annotation**: one week; annotators return the completed CSV to the coordinator only.
4. **Scoring** (only when all packets are complete):
   `python research_next/scripts/score_human_annotations.py <private_dir> review/annotation_key.csv`
5. **Adjudication**: for items without a majority, or where the majority disagrees with the generator, meet with the
   annotators, record the final decision and the reason per item. Report pre-adjudication statistics as primary.
6. **Archive**: commit the anonymised packets and `human_agreement.json` under `review/human/`; never commit names.
7. **Report**: the human results go in a section separate from the LLM audit.

## 5. Instructions to annotators (verbatim)

> You will read short fictional rule documents (numbered articles) and facts about one case, followed by a claim.
> Decide whether the claim is **entailed** (the document and facts make it true), **contradicted** (they make it
> false), or **insufficient** (they do not settle it). Use only what is written; do not use knowledge of real law.
> Read conditions literally: "only if", "only to", "unless" restrict the rule. If the document does not mention the
> obligation in the claim, answer **insufficient**. If an item seems ambiguous, choose the label a careful reader
> would choose, write "yes" in the *ambiguous* column and explain why in one sentence.
> Work alone. Do not look anything up. Take breaks; you may stop and resume.

Worked examples (show before the packet; none of them appears in the packets) — prepare six, one per construction
(obligation stated/not stated, threshold, date, exemption, cross-reference, unstated attribute), written by the
coordinator from the templates, with the answer and a one-line justification.

## 6. Parts B and C

Parts B (strict boundaries) and C (cross-reference probes) use items from the confirmatory sets, which do not exist
yet. Use the same procedure once they are generated; Part B must include the same comparison templates as the model
evaluation so that the human baseline is comparable.

## 7. Checklist before sending packets

- [ ] Packets contain no ids, operators, labels or model outputs (open one and check).
- [ ] Each annotator's order differs (packets are shuffled independently).
- [ ] The coordinator map is stored privately.
- [ ] Consent text sent and acknowledged.
- [ ] Worked examples prepared and checked by a second person.
