# Scopewright render-endpoint input-validation audit — 2026-11-12

**Status:** Read-only inspection of current default-branch source. Reproduction is reasoned from code paths, **not an executed HTTP test**. No customer data, production changes, merges, deployments, outreach or purchases.

## Concrete issue: `POST /api/render` skips schema validation

In `scopewright_server.py`, `do_POST` checks only `isinstance(scope, dict)` for `/api/render` and immediately calls `render_proposal(scope)`. Unlike `POST /api/scopes`, it never invokes `schema.validate(scope)`. In `render_proposal`, `html.escape(scope.get("project_title", ""))` assumes a string, and iteration of `sections`, `exclusions`, etc. assumes validated lists/objects.

**Reproduction to execute on an isolated local checkout:**
```bash
python scopewright_server.py
curl -i -X POST http://127.0.0.1:8431/api/render \
  -H 'Content-Type: application/json' \
  --data '{"scope":{"project_title":42,"sections":[]}}'
```
**Expected:** a controlled HTTP 400 JSON validation error, no HTML proposal. **Likely current behavior (not run):** `html.escape(42)` raises `AttributeError` and the handler terminates the request without a controlled 400. Other invalid nested structures may likewise raise. This is a robustness and reviewer-safety gap, not evidence of remote compromise; the server defaults to loopback `127.0.0.1`.

## Small fix for a separately reviewed PR

1. For `/api/render`, run `ok, errors = schema.validate(scope)` and return HTTP 400 with bounded validation errors when invalid, just as the save endpoint does. Avoid silently repairing at render time.
2. Add offline HTTP regression checks: invalid title number, `sections` wrong type, non-string `exclusions`, invalid nested item; each must return 400 without crashing. A valid `GOOD` fixture must still return 200, HTML-escaped output.
3. Confirm UI only renders a contractor-reviewed scope; validation is structural and **does not establish factual grounding**. Do not merge/deploy until tests and owner review.

## Why this matters for the first paid pilots

A failed printable proposal is a direct fulfillment failure for a contractor-reviewed $99 simple-job pilot. Prioritize fixing this narrowly over additional feature development. This does **not** justify declaring Scopewright validated: source-note unknowns and 20 permissioned real-job evaluations remain open.

**Commercial baseline:** 0/3 verified paying contractors; nine historical Outlook drafts last verified Nov 1; three fictional, human-authored demonstrations; 0/20 verified real-job evaluations. Do not treat drafts as sends or the fictional gallery as generated proof. The $99 price remains a hypothesis, not an approved offer.

**Owner approval required:** engineering PR/merge/deploy, one specific prospect send, customer-facing price/terms, privacy and retention, payment/refund workflow, and Scopewright commercial IP permissions.

**Cash/entity boundaries:** Scopewright is first priority within proposed ABSOL Technologies under ABSOL LLC; track its receipts, delivery hours, direct costs and fees separately from construction and planned Creature Codex TCG/collectibles/3D-printed-display activities. Creature Codex DBA/eBay setup is unverified; do not purchase speculative inventory. ABSOL LLC developed ForgeEPM, but **Forge EMP LLC owns it**. No new spending or construction wind-down decision is supported by this audit.

Sources: [commercial launch #1](https://github.com/ABSOL7471/Scopewright/issues/1), [cash-first #2](https://github.com/ABSOL7471/Scopewright/issues/2), [server](https://github.com/ABSOL7471/Scopewright/blob/main/scopewright_server.py), [schema](https://github.com/ABSOL7471/Scopewright/blob/main/schema.py), [Nov 11 outreach decision](https://github.com/ABSOL7471/Scopewright/blob/main/docs/first-send-decision-brief-2026-11-11.md).
