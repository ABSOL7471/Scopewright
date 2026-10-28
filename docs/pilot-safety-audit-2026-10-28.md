# Scopewright pilot-safety static audit — 2026-10-28

**Scope:** read-only review of `schema.py`, `llm.py`, `scopewright_server.py`, `selftest.py`, `prompt.py`, and `eval/EVAL.md`. **No live Ollama run or local test suite execution was performed** in this review; findings below follow directly from the current source.

## Finding A — shape validation is not evidence that generated content matches notes (priority: high)

- `schema.validate(obj)` validates data types, required fields, and section shape. It **does not accept original notes**, so it cannot verify whether a quantity, price, brand, assumption, exclusion, or completed work item was supported by the notes.
- `llm.generate_scope(notes)` returns when `schema.validate(obj)` succeeds; it does not compare output content with the notes. Therefore the README's implication that schema validation itself guarantees non-invention is stronger than the code proves.
- The existing offline `selftest.py` checks schema shapes and mocked HTTP behavior. It cannot establish real-world hallucination rates or contractor safety.

**Reproduction to run locally (expected under current code, not executed here):**

```python
import copy, schema
scope = {
    "project_title": "Deck repair",
    "client_summary": "Repair deck.",
    "sections": [{"name": "Repair", "items": [
        {"description": "Install premium Brand-X composite decking",
         "quantity": "800", "unit": "sq ft", "notes": "$15,000"}]}],
    "exclusions": [],
    "allowances": [],
    "assumptions": ["Footings are code compliant"],
    "change_order_terms": "Changes require a signed change order.",
    "open_questions": []
}
print(schema.validate(scope))  # Expected: (True, [])
```

The fixture above is **deliberately fabricated to demonstrate the limitation**, not an actual model output. With original notes of `"deck feels soft; measure later; decking TBD"`, accepting this JSON would not establish accuracy.

## Finding B — unresolved questions can disappear while the JSON remains valid (priority: high)

- `schema.repair` fills a missing `open_questions` list with `[]`; `selftest.py` explicitly expects this behavior.
- `schema.validate` accepts an empty `open_questions` list.
- A job note containing `TBD`, `verify`, `?`, or `check` can therefore receive a structurally valid draft with no recorded questions if the model misses them.
- The last stored draft-set eval reports **61–65%** unknowns routed to open questions (Aug. 25, 2026). These are not real-contractor performance numbers.

## Finding C — printable render endpoint checks only top-level object (priority: medium)

`POST /api/render` checks `isinstance(scope, dict)` and then calls `render_proposal(scope)` without `schema.validate`. Nested malformed input may cause a server exception rather than a clean 400. The server is loopback-only by default, reducing exposure, but the client should not interpret a rendered document as validated.

## Safe, focused fix proposal for Codex / Venom

1. Add an **advisory review-warning function** receiving both raw notes and the generated scope. Flag explicit uncertainty markers and show their source excerpts when `open_questions` is empty or possibly incomplete. Do not pretend a regex proves semantic coverage.
2. Keep the human review gate prominent in the UI; never auto-add invented decisions to the scope.
3. Add offline tests for notes `tile TBD`, `soft floor?`, `verify framing` and no `open_questions`, plus no false certainty when ambiguous text appears.
4. Add a schema check to `/api/render` and return 400 on invalid nested shape; test it. This is a separate, small hardening patch.
5. Update README marketing wording to say schema validation enforces **structure**, while prompt/evals/manual review address **factual fidelity**.
6. Run `python selftest.py` and actual Ollama evaluation on a private, contractor-authored test set before reporting results. Don't count this static audit as tests passing.

## Commercial release gate

No broad "never hallucinates" claim based solely on the 12 AI-drafted cases. Paid done-for-you pilot work must include explicit contractor approval and documented human review of quantities, selections, exclusions, unknowns, and changes. Pilot target remains **three paid jobs**; no paid jobs were verified by this audit.
