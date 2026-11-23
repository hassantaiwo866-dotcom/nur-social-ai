# Day 3 — editorial quality diagnostics

## Purpose
Provide transparent, deterministic checks for structural completeness and common content weaknesses before human review.

## Checks and weights
- Four-scene structure — 20 points
- Scene narration completeness — 20 points
- Distinct visual prompts — 15 points
- Correct story arc order — 15 points
- Practical payoff cue — 15 points
- Video caption present — 15 points

## Behavior
The evaluator returns a 0–100 advisory score, per-check results, and warnings. It is not a prediction of views, engagement, emotional impact, or audience response. The payoff cue uses a small phrase list and can miss valid actions or mistakenly identify vague language; treat it as a reminder, not proof. The evaluator does not block generation or publication and does not alter the plan.

## Safeguards
- Human review remains mandatory.
- A score is not a substitute for checking factual accuracy, emotional sensitivity, visual relevance, rights, audio, or product claims.
- No provider calls, paid services, dependencies, or publishing actions are introduced.
