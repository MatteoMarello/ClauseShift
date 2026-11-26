# Research study guide: from a benchmark to a research question

Audience: the project author (MSc Data Science and Engineering, Deep NLP). Goal: be able to explain, criticise and
extend this work without the AI assistant. Read `SCIENTIFIC_AUDIT.md` and `RESEARCH_QUESTIONS.md` first.

---

## 1. The research questions in plain words

1. **Which program does the model run? (RQ1)** Instead of "the model is 53% accurate", ask "which simple procedure
   produces the same answers as the model?". We wrote 648 small procedures ("ignore thresholds", "treat *more than*
   as *at least*", "treat any exemption as applying", …) and found, for each model, the one that agrees with it most
   often. Zero-shot NLI models turned out to agree on ~98% of items with a procedure that only checks whether the
   claimed obligation is mentioned.
2. **What can a benchmark tell apart? (RQ2)** A benchmark can only detect a wrong procedure if some item makes that
   procedure fail. We counted these items for each procedure. For cross-references the count is **zero**: every
   cross-reference in ClauseShift names the case's own category, so "react to *Article 1*" and "resolve the reference"
   always give the same answer. Pilot 2 asks which one the models actually learned, and whether training on pairs
   (which differ only in that digit) makes the shortcut more likely.
3. **Is the cross-reference test fair? (RQ3)** The original hold-out never showed the model any cross-reference. A fair
   test shows the construction with other content and withholds only a combination.
4. **Do evidence metrics notice? (RQ4)** A procedure that reads no condition gets a perfect evidence score.
5. **How few items do we need? (RQ5)** Choosing items adaptively identifies the procedure with ~5× fewer items.

---

## 2. Reading list (in order, with what to look for)

1. McCoy, Pavlick & Linzen (ACL 2019), *Right for the Wrong Reasons* (HANS). Heuristics as explicit hypotheses; why
   in-distribution accuracy cannot reveal them.
2. Geiger, Cases, Karttunen & Potts (EMNLP 2019), *Posing Fair Generalization Tasks for NLI*. The fairness
   definition; why a test that never exposes a construction is not evidence of non-compositionality.
3. Gardner et al. (Findings EMNLP 2020), *Contrast sets*; Kaushik, Hovy & Lipton (ICLR 2020), *CAD*. Minimal pairs for
   evaluation and training.
4. Huang, Liu & Bowman (Insights 2020) and Joshi & He (ACL 2022). Why counterfactual data often does not help at equal
   size; the linear-Gaussian argument about unperturbed robust features.
5. D'Amour et al. (JMLR 2022), *Underspecification*. Many predictors fit the test set; they differ elsewhere.
6. Feng, Wallace & Boyd-Graber (ACL 2019), *Misleading failures of partial-input baselines*.
7. DeYoung et al. (ACL 2020), ERASER; Hase, Xie & Bansal (NeurIPS 2021); Hsia et al. (Findings EACL 2024). How evidence
   metrics work and how they fail.
8. She et al. (ACL 2023), *ScoNe*; Geiger et al. (NeurIPS 2021), *Causal abstractions*. Behavioural vs. mechanistic
   tests of "does the model implement algorithm X?".
9. Singh et al. (EACL 2026), *COMPACT*; Choudhury et al. (Findings EACL 2026), *Better Call CLAUSE*. The closest
   recent legal-domain benchmarks; compare their construction with ours.
10. Polo et al. (2024), *tinyBenchmarks*. Item response theory for efficient evaluation; contrast with our goal.

For each paper write five lines: question, data, method, main number, the one design choice you would change.

---

## 3. Mathematical and methodological guide

### 3.1 Programs and agreement
Let x be an item, y(x) its gold label, m(x) the model's prediction, and P a set of programs p: x → label. Agreement
A(m, p) = (1/N) Σ 1[m(x) = p(x)]. Accuracy is A(m, p*) for the reference program p*. Cohen's κ corrects agreement for
chance: κ = (A − A_e)/(1 − A_e), A_e = Σ_l P_m(l) P_p(l) from the two label marginals.
**Selection bias:** choosing argmax_p A(m, p) over 648 programs on the same data overstates the fit. We therefore
select on dev and report on test. Exercise 2 asks you to quantify the optimism.

### 3.2 Identifiability
For a heuristic h and the reference p*, the distinguishing set is D(h) = {x : h(x) ≠ p*(x)}. If |D(h)| = 0 on a
benchmark, no accuracy number on that benchmark can tell a model using h from one using p*. This is
*underspecification at the level of the benchmark design*. For minimal pairs: a pair distinguishes h if h and p*
disagree on at least one side. Good benchmark design maximises min_h |D(h)| over plausible heuristics.

### 3.3 Bayesian adaptive identification
Prior w(p) uniform over programs. Noise model: P(m(x) = p(x)) = 1 − ε, otherwise one of the other two labels with
ε/2 each. After observing answers on items S, w(p) ∝ Π_{x∈S} P(m(x) | p). Choose the next item maximising expected
information gain, which under this symmetric noise is equivalent to maximising the entropy of the predictive
distribution q(l | x) = Σ_p w(p) P(l | p, x). This is classic Bayesian experimental design / "twenty questions".

### 3.4 False-flip rate (Pilot 2)
For base cases answered correctly, add a sentence that should not change the label; the false-flip rate is the share
of predictions that change. It measures sensitivity to an irrelevant edit, conditioned on competence on the base.
Conditioning matters: without it, a model that is wrong on the base could "flip to correct".

### 3.5 Statistics you must be able to defend
- Bootstrap over the independent unit (pairs or base cases, not items).
- Paired comparisons by shared resampling.
- Seeds: pair bootstraps treat seeds as fixed; with 3 seeds report per-seed values and a seed-level t-interval.
- Multiplicity: per-operator tables are descriptive; confirmatory hypotheses are few and fixed in advance.
- Pilot vs. confirmation: anything computed after looking is exploratory, however clean it looks.

---

## 4. Why the experiments are designed the way they are

| Decision | Reason | What a critic could say |
|---|---|---|
| Program lattice from the reference rule | Each dimension is a plausible misreading suggested by the audit | The lattice is chosen by us; a model could run a program outside it (agreement 0.88–0.92 for strong models shows unexplained residue) |
| Select on dev, report on test | Avoids fitting 648 programs to the evaluation data | Dev is one family; selection could still be noisy |
| Probes in a family different from test | Keeps the test set clean for confirmation | Pilot uses the dev family, which also selected the epoch |
| Re-train with the registered recipe and seed | Reproduction check; same model as the reported one | One seed per condition in the pilot |
| Lazy reader as a negative control | A known-bad program should fail any valid metric | It is a synthetic-template reader; on real text it would need a parser |
| New families for confirmation | Avoids re-using analysed data | New families are written by us and may differ in difficulty |

---

## 5. Exercises

1. Reproduce `research_next/results/lazy_reader.json` by hand for five test items: write the lazy reader's prediction
   and the gold label, and explain each disagreement.
2. Quantify selection optimism: run `program_fingerprint.py` with selection on test and compare the agreement with the
   dev-selected program. What does the difference tell you?
3. Pick a heuristic not in the lattice (e.g. "reads only the first condition sentence"). Add it, count |D(h)| on test,
   and fingerprint the models again.
4. For the boundary finding, compute exact binomial 95% intervals for the share of errors that copy the satisfied
   label, per group. How many boundary items would you need to estimate it within ±0.05?
5. Write the generator change that produces cross-references to another category (`make_probes.py` does it outside
   the frozen generator). Which other operator lacks a near-miss twin?
6. Derive, for the symmetric noise model, why expected information gain reduces to predictive entropy minus a
   constant.
7. Read Joshi & He's Proposition 1 and explain in your own words why an incomplete edit can make a robust feature
   look spurious. Relate it to the cross-reference digit.

---

## 6. Questions you should expect in an interview or viva

1. "Your zero-shot models agree with a trivial program on 98% of items. Isn't that just a format artefact?" (Answer:
   it holds in the facts-in-premise format, which removed the format artefact; in the standard format agreement is
   0.92 for DeBERTa-base NLI. Know both numbers.)
2. "Why should we believe your lattice is the right hypothesis space?"
3. "Isn't identifiability just HANS?" (HANS builds a test set for given heuristics; identifiability counts, for an
   existing benchmark, how many items separate each heuristic from the rule, and finds zero for one dimension of a
   benchmark that was designed with near-miss controls.)
4. "How do you know the probe labels are right?" (Generator-derived; human check planned in Part C.)
5. "Isn't the cross-reference shortcut your own design bug?" (Yes; the contribution is the method that found it and
   the evidence on whether pairing exploits it. The bug is reported, not hidden.)
6. "Three seeds — is anything here robust?"
7. "Would any of this hold for LLMs or real contracts?"

## 7. Reviewer objections to prepare for

- Synthetic templates; results may not transfer (needs a real-text component or a clearly scoped claim).
- Small models only.
- The lattice is post hoc (fix it in the protocol before confirmation; report programs outside the lattice as
  residue).
- Probe labels and boundary conventions not human-validated.
- Novelty: heuristics-as-hypotheses (HANS, ScoNe) and causal abstraction exist; state exactly what is new.

## 8. Decisions that need *your* judgment (not the assistant's)

1. Which research question becomes the paper (the memo recommends one; you must agree after reading the evidence).
2. Whether to target a workshop / SRW first or a Findings-level paper later (time vs. ambition).
3. Who annotates, and whether you annotate yourself (you may not, if you have seen the labels).
4. Whether to spend compute on more seeds (confirmatory) or on a real-text component.
5. How to describe AI assistance in any submission, following the venue's policy.
6. Whether to release the probe generator and program lattice as a tool.

## 9. What you should do yourself to own the work

- Re-derive the lazy-reader and boundary numbers (Exercises 1, 4) before trusting them.
- Write the lattice extension (Exercise 3) and the generator change (Exercise 5) yourself.
- Annotate the calibration items and run the human study logistics.
- Draft the introduction and the limitations section of any paper in your own words.
- Present the findings to someone who will argue with you; record the objections.
