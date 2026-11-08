# Scopewright — advisory unknown-marker integration audit (2026-11-08)

**Status:** read-only code inspection and proposed acceptance tests. No application change, live model test, merge, deployment, or claim of validated accuracy.

## Files inspected
- `tools/unknowns_fixture_audit.py` — standalone marker finder and 10 fictional fixtures.
- `schema.py` — validates output structure; `repair()` can insert `open_questions: []`.
- `selftest.py` — offline schema and mocked HTTP tests; its `GOOD` fixture has an open question, but there is no source-notes-to-output unknown coverage assertion in the inspected section.
- Existing commercial launch issues #1 and #2 and Nov 6 pilot-conversion kit.

## Confirmed gaps and edge cases
1. **Not integrated:** `review_markers(notes)` is a standalone helper. Passing its fixtures is not evidence that the generate, review, or print workflow uses its output.
2. **Silent loss of unknowns:** `schema.repair()` may fill absent `open_questions` with an empty array, and `validate()` accepts it. Neither function receives original notes, so neither can verify that an explicit unresolved choice survives generation.
3. **Ordering bug:** the helper sorts matches by `notes.find(x["excerpt"])`. For repeated identical excerpts, both matches resolve to the first occurrence; it does not preserve actual match offsets. Fix by keeping `start` as an internal sort key.
4. **Sentence-boundary weakness:** excerpts end at the next period/newline; punctuation in abbreviations, decimal measurements, and multiple clauses can truncate context. Excerpts are advisory, not proof of full semantic coverage.
5. **False-positive examples:** `TBD` printed on an existing label (fixture U08) and `maybe` in a quoted statement may be detected without being an unresolved construction decision. The existing test expects U08 detection and therefore cannot claim precision.
6. **Question detection is narrow:** regex `\\b[\\w-]+\\?` may miss standalone punctuation, spaced questions, and implicit uncertainty such as `owner to select color` or `subfloor condition unknown`. No semantic recall guarantee.

## Minimal proposed implementation (separate reviewed PR)
- Return a **nonblocking, advisory** list of source-exact note excerpts with character offsets from `review_markers`; keep the original notes private and do not auto-insert text into scope fields.
- On generate and on opening a saved scope, show an explicit **Unresolved notes to compare** panel beside the generated `open_questions`. Do not equate keyword detection with validation or force a match for every marker.
- When `open_questions` is missing and repaired to `[]`, display a conspicuous repair warning and require contractor review; do not auto-certify the document.
- Preserve the existing review acknowledgement reset after regenerating/editing/reopening; test the actual UI and print path, not only helper functions.
- Never upload real client notes to GitHub or external model services without approved privacy/processing terms.

## Acceptance tests to implement and execute before merging
| ID | Fictional input | Expected reviewer behavior |
|---|---|---|
| A01 | `Guest bath tile TBD` | Exact source excerpt visible; unanswered tile choice remains for review |
| A02 | `Verify subfloor. Color TBD.` | Both distinct source spans shown in original order |
| A03 | `TBD. TBD.` | Two distinct offsets retained, no collapsed duplicate |
| A04 | `Label on storage bin reads TBD` | Advisory flag may appear but is **not** represented as confirmed missing decision |
| A05 | `Owner to select grout color` | Manual review can flag implicit unknown even if regex finds nothing |
| A06 | Output `open_questions=[]` despite `Tile TBD` | UI does not claim complete resolution; human review required |
| A07 | Saved scope reopened after acknowledgement | Review state reset and advisory markers still available |
| A08 | Malicious HTML in notes | Escaped in UI/print; no execution |
| A09 | Very long notes near size cap | Bounded processing, no UI hang, no unapproved external transfer |
| A10 | No explicit uncertainty markers | No unsupported “all facts verified” success message |

## Business decision
This is a **pilot safety blocker**, not a reason to buy infrastructure. Prioritize a small tested PR and permissioned real-job evaluations over new marketing spend. No new outreach or payments authorized. Proposed $99 contractor-reviewed simple-job pilot remains an unapproved pricing hypothesis; count paying pilots only after payment is verified from distinct contractors.

## Entity/accounting boundaries
ABSOL Technologies is a proposed ABSOL LLC operating brand. Track Scopewright receipts, fees, direct costs, labor hours and revisions separately from ABSOL Construction. Creature Codex is a planned TCG/collectibles/3D-printed-display ABSOL LLC operating brand with unverified DBA/eBay legal setup; track its inventory and net contribution separately, no speculative purchases. ABSOL LLC developed ForgeEPM; **Forge EMP LLC owns ForgeEPM**.
