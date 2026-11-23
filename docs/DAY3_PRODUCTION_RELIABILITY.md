# Production run manifest and failure tracking

## Purpose
Persist a lightweight stage ledger so a failed production run leaves diagnostic information in its output directory.

## Implemented
- Manifest records run ID, overall status, current stage, timestamps, stage history, output references, and a bounded error message.
- Writes use a temporary file followed by replacement to reduce partial-write risk.
- Failures are recorded as structured data.
- The manifest explicitly retains a human-review-required flag.

## Limitations
This is observability, not automatic recovery. It does not retry provider calls, resume interrupted runs, guarantee outputs survive disk or process failure, or prevent sensitive provider details from appearing in exception text. Review error messages before sharing logs. Existing temporary media remains subject to the pipeline's temporary-directory cleanup.

## Tests
Deterministic tests cover stage updates, failure recording, and atomic file replacement behavior.


## Day 9 — rendered output validation

- Added `output_validation.py` to inspect poster image integrity and dimensions, rendered video metadata via ffprobe, portrait dimensions, frame rate, duration, and presence of an audio stream.
- QA now records validated media metadata in the package report. Failed validation stops packaging and publishing eligibility.
- Added mocked ffprobe and temporary-image tests for valid output and malformed/missing/incorrect media cases.
- Tests do not call external generation providers or create billable requests. A real render remains necessary for visual/audio human review.


## Day 10 — final production integration review

- Added integration tests for the QA gate: validated metadata is included, invalid media blocks QA, and basic shaming-language checks block review readiness.
- Added regression cases for invalid frame rate and FFprobe non-zero exit.
- Corrected validation error messages to render line breaks rather than literal escape sequences.
- Tests remain local/mock-based and do not trigger AI generation or provider charges.
- Final real-world production run, visual/audio inspection, and phone review remain outstanding.


## Day 10 fix — test syntax

- Corrected malformed test context-manager closures and moved test methods into the test class before the `unittest.main()` guard.
- This ensures the validation regression tests compile and are discoverable by unittest.
