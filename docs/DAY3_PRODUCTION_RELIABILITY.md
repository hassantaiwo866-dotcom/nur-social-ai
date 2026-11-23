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
