# Golden cases — ALL DRAFT

These 12 cases were AI-drafted to bootstrap the eval harness. They are
being replaced case-by-case with real examples from a working GC — real
job-walk notes (anonymized) and expectations checked by someone who has
actually written the scope for that job.

Until a case has been through that review, treat its scores as a smoke
test of the pipeline, not a measure of scope quality.

Each case directory contains:

- `notes.txt` — messy field notes, the pipeline input
- `expected.json` —
  - `expected_elements`: phrases that must appear somewhere in the scope
  - `expected_exclusions`: phrases that must appear in the exclusions
  - `forbidden_inventions`: things a hallucinating model might add
    (dollar amounts, brands, dimensions not in the notes) — any hit
    counts as a hallucination
  - `expected_open_questions`: unknowns that should land in
    open_questions instead of being silently resolved
