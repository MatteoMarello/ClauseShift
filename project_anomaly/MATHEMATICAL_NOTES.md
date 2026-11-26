# Mathematical notes

Three short, self-contained results used by the pilots. They are elementary; the point is to state precisely what
each measurement can and cannot show. Notation follows `research_next/FORMALIZATION.md`: an item is x = (d, h) with
document d and hypothesis h; R is the reference rule (`gold_label`); a *system* is a map f from items to labels
L = {E, C, I} (entailed, contradicted, insufficient), possibly through a probability vector p(· | x).

## 1. Single-input evidence criteria cannot see the clause they remove (C14)

Let T be an edit that removes sentences from d (e.g. the decisive condition). An evidence criterion is
**single-input** if it scores a system on each edited item separately,
S₁(f) = E_x[ 1{ f(Tx) = R(Tx) } ], and **joint** if it requires both sides of a decisive pair,
S₂(f) = E_x[ 1{ f(x) = R(x) ∧ f(Tx) = R(Tx) } ] over items with R(x) ≠ R(Tx).

Let g be the lazy program, which reads only whether the obligation is stated and the claim polarity, and let T_all
remove every condition sentence (threshold, date, scope, exemption, cross-reference).

**Proposition 1.** R(T_all x) = g(T_all x) for every x. Hence g attains the maximum of S₁ for T = T_all, and more
generally for any T whose image lies in the set A = {x : R(x) = g(x)} on which the rule and the lazy program agree.

*Proof.* With no condition sentence left, the rule's label is determined by whether the obligation is stated, its
topic and its polarity, which are exactly g's inputs. ∎

**Proposition 2.** If a system f is insensitive to the removed sentences, i.e. f(x) = f(Tx), then f scores 0 on
every item counted by S₂, because R(x) ≠ R(Tx) cannot be matched by a single label.

*Consequence.* Removing a decisive clause moves an item *into* the region where the degenerate program is right.
Any criterion that only looks at the edited input therefore rewards ignoring the clause. Only criteria that tie the
edited and unedited predictions together (S₂, or flip-pair accuracy) are sensitive to it. This is the general reason
behind the observed v1 → v2 change in `research_next` (the lazy reader scores 1.000 under single-input scoring and
0.000 under joint scoring). It applies to deletion-based faithfulness tests in general: if deleting evidence makes
the input fall into a region where a shortcut is correct, deletion tests measure the shortcut.

## 2. Symmetry under claim negation and what symmetrised decoding can gain (C2)

Let ν be claim negation (same template index, polarity flipped) and σ the label permutation E ↔ C, I ↦ I. The task
is exactly **equivariant**: R(νx) = σ R(x) for every x (verified for all 2,560 test items by
`make_negation_probes.py`). A system is equivariant on x if f(νx) = σ f(x); the *symmetry consistency* is
P_x[f(νx) = σ f(x)].

Symmetrised decoding combines the two views: p_sym(y | x) ∝ p(y | x) · p(σy | νx).

**Proposition 3 (equivariance by construction).** p_sym(y | νx) = p_sym(σy | x), since σ is an involution:
p_sym(y | νx) ∝ p(y | νx) p(σy | x), which is the expression for p_sym(σy | x) with its factors swapped. ∎

**Proposition 4 (no gain without inconsistency).** If f(νx) = σ f(x) (arg-max consistent), symmetrised decoding
returns the same label as the original prediction: both factors y ↦ p(y | x) and y ↦ p(σy | νx) are maximised at
y = f(x), so their product is too. Hence, for accuracy on the original items,

  |acc(p_sym) − acc(p)| ≤ 1 − consistency,

and the change comes entirely from inconsistent items (fixes − breaks among them). ∎

*Coding-theory reading.* The pair (x, νx) is a repetition code of length 2 for the label (up to σ). Decoding gains
only from views whose errors are not perfectly correlated. A system whose errors are a consistent wrong reading
(a program) is a channel that repeats the same symbol twice: the second view carries no information about its
errors. A system whose errors are view-specific noise gains. Proposition 4 is the exact, finite-sample version of
this statement for arg-max decisions. If the two views were conditionally independent given y and calibrated, the
Bayes combination would be p(y|x) p(σy|νx) / p(y), so with balanced labels (as here) p_sym is the right decoder.

*Covariant error share.* Among items where f(x) ≠ R(x), the share with f(νx) = σ f(x). Under independence of the
two predictions given that the original is wrong, the expected share is Σ_k P(σf(x)=k) P(f(νx)=k), which
`analyze_pilot2.py` reports as a baseline; the share is only informative relative to it.

## 3. A psychometric model of strict comparison (Pilot 1b)

For a condition "value > c" (or "after c"), let Δ = value − c. An ideal reader has P_sat(Δ) = 1{Δ > 0}. A noisy
comparator with bias μ and resolution s is modelled as

  P_sat(Δ) = γ + (1 − γ − λ) Φ((Δ − μ) / s),

with guess rate γ and lapse rate λ (the standard psychophysical form). Strict vs non-strict reading corresponds to
whether the transition sits just above or just below Δ = 0, i.e. to μ relative to 0 at a resolution s ≪ 1 unit.

**Proposition 5 (identifiability of strictness).** From behaviour at Δ ∈ {−1, 0, +1} unit the strict and
non-strict programs are distinguishable only through P_sat(0). If s is not small compared with one unit, a low
P_sat(0) and a low P_sat(−1) are produced by the same curve, and attributing the error at Δ = 0 to "non-strict
semantics" is not supported: the model does not resolve the cutoff in the first place. The lattice dimension
"threshold = strict / non-strict" in `program_fingerprint.py` implicitly assumes s ≪ 1 unit; Pilot 1b measures
whether it holds.

This is why Pilot 1's validity condition (accuracy ≥ 0.70 at ±1 unit) matters: when it fails, every statement about
the boundary itself is a statement about a comparator that does not resolve that distance.
