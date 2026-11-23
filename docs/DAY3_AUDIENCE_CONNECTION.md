# Day 3 — audience connection and storytelling

## Purpose
Day 2 improves visual execution. Day 3 improves whether the audience recognises the message, emotionally follows it, and receives a useful next step.

## Implemented
- Added deterministic editorial guidance for a four-scene emotional arc: recognition, tension, reframe, action.
- Added explicit rules for concrete everyday experiences, coherent story progression, dignity, agency, and practical payoffs.
- Integrated these instructions into the editorial-plan prompt. This is prompt guidance, not a guarantee that provider output will satisfy it.

## Safeguards
- No shame, guilt, fear, humiliating language, fabricated statistics, exaggerated promises, or manipulative cliffhangers.
- Do not describe viewers as broken or force a Nūr mention into every scene.
- Do not claim app features that have not been verified.
- No new providers, credentials, dependencies, costs, publishing actions, or generation calls.

## Tests
Local deterministic tests verify that the direction has four distinct beats and contains the expected user-agency and non-shaming constraints. The full repository test suite remains the CI verification gate.
