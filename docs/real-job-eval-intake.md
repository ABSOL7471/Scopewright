# Real-job pilot evaluation intake — draft, no customer data

**Prepared:** 2026-10-28. **Purpose:** move Scopewright from an AI-written draft evaluation set to a contractor-authored, de-identified 20-job evaluation before claiming real-world reliability. This is an intake template, **not** 20 completed evaluations or a verified model test.

## Owner's five-minute first contribution

Choose **one past completed job** that you personally worked on. Write 4–8 raw walkthrough-note fragments in the same shorthand you would have typed at the job site. **Do not include** customer name, street address, phone/email, photos containing people or addresses, access codes, financial information, or confidential client details. Keep uncertainties exactly as they appeared (e.g. `tile TBD`, `soft floor?`, `verify vent routing`).

**Copy/paste template (case 01):**

```text
Job type: [bathroom / deck / water mitigation / kitchen / paint / punch list]
Rough notes (as originally written):
- ...
- ...
- ...
- ...
Known included work (what the contractor actually intended):
- ...
Explicitly excluded work (if known):
- ...
Unanswered decisions / measurements at walk-through:
- ...
Contractor review outcome: [leave blank until Scopewright output is tested]
```

Only add facts known at the original walkthrough. If you know how a hidden issue was resolved later, **don't leak that answer into the input**; it can be used to assess whether the draft should have asked a question.

## Proposed 20-case coverage matrix

These are **slots to fill**, not existing cases:

| Slot | Project class | Critical ambiguity to test |
|---|---|---|
| 01 | Bathroom refresh | fixture selection TBD |
| 02 | Tub/shower conversion | concealed wall condition |
| 03 | Bathroom tile | waterproofing system / layout undecided |
| 04 | Accessibility bathroom | final clearance / site measurements |
| 05 | Deck resurfacing | underlying framing unknown |
| 06 | Deck framing | footing and permit determination |
| 07 | Deck hot-tub support | loads / engineering not verified |
| 08 | Deck stairs and rails | code and dimensions not verified |
| 09 | Water damage | moisture extent unknown |
| 10 | Flood-cut restoration | hazardous materials / hidden damage |
| 11 | Flooring after leak | substrate condition unknown |
| 12 | Kitchen remodel | appliance selections and circuit capacity |
| 13 | Kitchen cabinetry | field measurements and lead times |
| 14 | Kitchen backsplash | substrate / tile selections |
| 15 | Interior paint | surface prep exclusions |
| 16 | Drywall patch | texture matching / moisture source |
| 17 | Exterior trim paint | rot discovered after prep |
| 18 | Handyman punch list | owner vs contractor-supplied fixtures |
| 19 | Door/window repair | structural damage and replacement size |
| 20 | Mixed property maintenance | ambiguous trade boundaries |

## Evaluation rubric — record for every real case

| Field | Record |
|---|---|
| Source permission / de-identification confirmed | yes / no |
| Draft output generated with actual model | model + date, or NOT RUN |
| Source notes fully represented | missing / present items |
| Open questions correctly retained | list of critical misses |
| Unsupported facts / assumptions introduced | exact quote and source mismatch |
| Exclusions appropriate and consistent with scope | missing / wrong / acceptable |
| Contractor revision time | minutes |
| Ready for customer after human review | yes / no, reason |
| Paid pilot / revenue | actual collected amount only; otherwise $0 |

**Stop and review** if the model invents quantities, brands, code compliance, work authorizations, prices, or treats an unresolved safety/structural issue as settled. A passing JSON schema alone is **not** a semantic accuracy test. No model output goes to a client without contractor review.

## Privacy and commercialization

- Use invented notes or permissioned, de-identified past jobs for public demos. Never commit actual customer notes or photos to this public repository.
- A done-for-you pilot service requires explicit agreement on what data the contractor shares, where it is processed, how long it is kept, and how revisions are handled. Local-first software does **not** mean an operator-provided service has no data transfer.
- Introductory $99–$199 per-scope prices remain hypotheses; do not count any prospect or case as a paying customer until payment is received.
- Keep ABSOL LLC and Forge EMP LLC finances separate. ForgeEPM is owned by Forge EMP LLC, although developed by ABSOL LLC. Creature Codex is a proposed separate brand under ABSOL LLC, with legal/eBay setup unverified.

## Next action after the first case is supplied

Convert the notes to a **private** golden case, define the expected unknowns and forbidden inventions, run against the installed model, log output and manual corrections, then add an anonymized case to the test suite only if permission allows.
