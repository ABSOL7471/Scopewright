# Scopewright explicit-unknowns regression matrix — 2026-11-04

**Status:** New engineering acceptance fixtures, not executed tests or real-job evaluation results.  
**Purpose:** Turn [issue #3](https://github.com/ABSOL7471/Scopewright/issues/3)'s source-grounding concern into reproducible, non-PII checks before the first three paid, human-reviewed pilots. All notes below are **fictional**. They do **not** count toward the 20 real-job cases.

## What the source code establishes

On the current default branch, `schema.validate(scope)` checks JSON shape only, without the raw notes. `schema.repair(scope)` converts missing `open_questions` to `[]`. The existing `selftest.py` explicitly asserts this repair behavior. Thus a draft with `open_questions: []` can validate even when the original note says `TBD`. This is an **unexecuted static observation**, not a demonstrated live model failure.

## Proposed warning API and acceptance criteria (not implemented)

A small `review_unknowns(notes: str, scope: dict) -> list[dict]` helper, or equivalent, should produce **advisory warnings** with the original note excerpt, marker category and an instruction to manually verify coverage. Warnings must **never rewrite a generated scope, assert that the model definitely missed a semantic question, or mark a document approved**. No network service or new dependency is needed.

A warning should be visible to the operator **even if the JSON passes schema validation**. If a marker has a clear corresponding open question, it may be shown as *reviewed candidate* rather than silently cleared. Do not make claims of semantic matching from substring/regex alone.

### Deterministic fixtures for offline testing

| ID | Fictional source notes | Candidate generated `open_questions` | Expected reviewer behavior | Prohibited automatic inference |
|---|---|---|---|---|
| U01 | `Guest bath. Tile TBD. Keep tub.` | `[]` | Warning quotes `Tile TBD`; ask for tile selection | Choose tile, brand, cost or allowance amount |
| U02 | `Floor by doorway soft?` | `[]` | Warning quotes `soft?`; requires inspection/clarification | Claim subfloor replacement is authorized |
| U03 | `Verify framing before railing install.` | `[]` | Warning quotes `Verify framing` | Certify load capacity or code compliance |
| U04 | `Vanity stays maybe; paint color undecided.` | `[]` | Warn for both decisions | Assume vanity replacement or color |
| U05 | `12x16 deck, composite or cedar? Confirm with owner.` | `["Which decking material is selected?"]` | Show source/coverage for review; no missing-question certainty | Claim the entire draft is validated |
| U06 | `Replace 4 smoke alarms. Customer confirmed white.` | `[]` | No warning for explicit unknown markers; normal contractor review still required | Treat absence of warnings as accuracy guarantee |
| U07 | `Install TBD brand light, verify circuit.` | `["Which light brand?"]` | Keep warning for `verify circuit` despite a question about brand | Treat one open question as covering all unknowns |
| U08 | `Scope note: quote includes the literal label "TBD" printed on an existing storage bin.` | `[]` | May show low-confidence advisory; must not block or invent a selection | Automatically force a bogus material question |
| U09 | `Replace trim; material choice? Homeowner to confirm.` | `["Confirm trim material."]` | Show matched candidate and ask human to confirm; no forced new question | Duplicate a verified question as a fact |
| U10 | `Deck beam looks damaged. Engineer review needed.` | `[]` | Prominent unresolved structural risk; outside first-three simple-pilot fit | Say beam is safe or specify a repair design |

### Offline test contract

1. Construct each fixture with a **valid** schema-shaped `scope`; make the notes and questions independent variables.
2. Assert `schema.validate(scope)` may be true for U01–U04 and U07 despite missing source questions; the warning helper must still return nonempty review findings.
3. Assert returned excerpts are **literal substrings of source notes** (not invented text), stable, and reasonably short. Strip/escape HTML on UI rendering.
4. Assert no helper mutation of notes, scope, `assumptions`, `sections` or `open_questions`; no automatic generation of scope items.
5. Assert U06 has no marker-specific warning; still retain human review.
6. Assert U07 flags the **second** unknown rather than treating the mere presence of one open question as sufficient.
7. For U05 and U09, assert an explicit **human-check-needed** outcome even when a corresponding question appears.
8. U08 must not block rendering or be counted as a proven model miss; treat lexical matches as advisory.
9. U10 should trigger a separate high-risk pilot suitability flag, not a structural engineering conclusion.
10. Add integration checks for the browser's actual review-warning visibility and its behavior after regenerating/reopening a draft; keep the existing human sign-off gate.

**Release evidence required:** a recorded `python selftest.py` result on the relevant PR branch, UI smoke test, and later a separately permissioned 20-real-job eval with per-case source-note comparisons. Do not equate mocked/offline passes with Ollama accuracy.

## Pilot/business boundaries

- Pilot target remains **3 distinct paying contractors**; as of the last verified records, **0/3**, with 9 previously prepared unsent outreach drafts and 3 human-authored fictional demos.
- Introductory `$99` simple-job price is a **hypothesis**. Do not take money, collect customer notes or send outreach without owner-approved terms/privacy and a verified fulfillment process.
- ABSOL Technologies is a **proposed** ABSOL LLC operating brand, not a verified Oregon DBA. Scopewright commercial IP rights remain to be reviewed.
- Creature Codex is a planned ABSOL LLC TCG/collectibles and 3D-printed-display brand, with DBA/eBay seller setup unverified and separate class-level profitability tracking; no speculative inventory purchases.
- ABSOL LLC developed ForgeEPM; **Forge EMP LLC owns it**. No ForgeEPM IP or revenue counted as Scopewright or ABSOL Technologies property.
