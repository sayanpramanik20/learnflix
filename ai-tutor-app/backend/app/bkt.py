"""
Bayesian Knowledge Tracing (BKT).

This is the "does the student actually know this concept yet" model.
The pitch deck names a PyTorch Deep Knowledge Tracing model as the
long-term plan -- that needs a trained dataset you won't have by tomorrow.
BKT is the standard, well-understood lightweight substitute: four
per-topic parameters, one closed-form Bayesian update per attempt, no
training data required. It is a legitimate, published technique (Corbett
& Anderson, 1994), not just a placeholder -- and it's honest to describe
it to judges as "BKT now, DKT (PyTorch) as the trained-model upgrade path."

p_know        -- P(student has mastered the skill) right now
p_transit     -- P(student learns the skill during this attempt, if they
                  didn't already know it) -- models learning-by-doing
p_slip        -- P(student knows it but answers wrong anyway) -- carelessness
p_guess       -- P(student doesn't know it but answers right anyway) -- luck
"""
from dataclasses import dataclass


@dataclass
class BKTParams:
    p_transit: float
    p_slip: float
    p_guess: float


def update_mastery(p_know: float, correct: bool, params: BKTParams) -> float:
    """
    One Bayesian update step. Returns the new P(know).

    Step 1: Bayes' rule to get P(knew it already | observed answer).
    Step 2: Add the chance they learned it just now during this attempt
             (the "transit" / learning step), since even a student who
             didn't know it beforehand may know it after trying.
    """
    p_slip, p_guess, p_transit = params.p_slip, params.p_guess, params.p_transit

    if correct:
        numerator = p_know * (1 - p_slip)
        denominator = numerator + (1 - p_know) * p_guess
    else:
        numerator = p_know * p_slip
        denominator = numerator + (1 - p_know) * (1 - p_guess)

    # Guard against a degenerate 0/0 (only happens with p_know at exactly 0 or 1
    # combined with extreme slip/guess params)
    p_know_given_obs = numerator / denominator if denominator > 0 else p_know

    p_know_new = p_know_given_obs + (1 - p_know_given_obs) * p_transit
    return min(max(p_know_new, 0.0), 1.0)


def mastery_status(p_know: float) -> str:
    if p_know < 0.4:
        return "struggling"
    if p_know < 0.75:
        return "developing"
    return "mastered"
