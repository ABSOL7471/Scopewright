# Scopewright — JSON top-level type crash audit (2026-11-15)

**Status:** Source-inspected, not runtime-reproduced. Internal engineering preparation only; no production changes, outreach, deployment, or paid commitments.

## Specific defect found

On default branch `main`, `scopewright_server.py` defines `Handler._body()` as `json.loads(self.rfile.read(n) or b"{}")`, returning the decoded JSON **without checking that it is an object**. `Handler.do_POST()` immediately calls `body.get("scope")` for `/api/render` and `/api/scopes`, and similarly calls `body.get(...)` for other POST routes. JSON arrays, strings, numbers, booleans, and `null` decode successfully but do not have a `.get` method.

**Expected impact:** a syntactically valid request with a non-object JSON body can raise `AttributeError` before the route returns an HTTP 400. The HTTP server may close the connection instead of delivering a useful response. This is a source-derived prediction, not an executed test.

**Concrete reproduction to try on a local checkout:**
```sh
python scopewright_server.py
curl -i -X POST http://127.0.0.1:8431/api/render -H 'Content-Type: application/json' --data '[]'
curl -i -X POST http://127.0.0.1:8431/api/scopes -H 'Content-Type: application/json' --data 'null'
```
Use fictional test data only. `/api/render` needs no Ollama. Confirm the response/error logs rather than assuming the predicted failure occurred.

## Proposed minimal engineering correction (not implemented)

Guard decoded POST payloads before any `.get` access. A route-wide `if not isinstance(body, dict): return self._send(400, {"error": "body must be a JSON object"})` early in `do_POST` is one option. Preserve existing malformed-JSON handling and test whether empty-body semantics should remain backward-compatible. A separate body-size limit is worth considering later, but is **not** part of this small change.

## Acceptance tests to add

1. `POST /api/render` with `[]` returns structured HTTP 400, not a connection reset.
2. `POST /api/render` with `null` returns structured HTTP 400.
3. `POST /api/scopes` with `"hello"` returns structured HTTP 400, with no saved file.
4. `POST /api/generate` with `true` returns structured HTTP 400 without invoking Ollama.
5. Valid object-shaped request behavior is unchanged.
6. The five existing proposed tests in draft [PR #6](https://github.com/ABSOL7471/Scopewright/pull/6) still pass after integration.

## Relationship to current work

[Draft PR #6](https://github.com/ABSOL7471/Scopewright/pull/6) adds `schema.validate(scope)` to the rendering path but does **not** guard top-level `body` before `body.get`. As inspected November 15, the PR is still open/draft/unmerged and GitHub reports `mergeable=false`. Do not merge or deploy until tests, mergeability and owner review are resolved.

**Owner-facing priority:** this is a small reliability fix, not proof of content accuracy or a reason to postpone qualified contractor conversations indefinitely. Commercial goal remains **3 distinct verified paying Scopewright pilots**; last established baseline 0/3, with 0/20 permissioned real-job evaluations. Nine outreach drafts were last checked November 1, not reverified here. The proposed $99 pilot is a hypothesis, not an approved public price. Do not send any outreach without approval.

**Business boundaries:** Scopewright is the first proposed ABSOL Technologies product under ABSOL LLC, pending IP/name checks. ABSOL LLC developed ForgeEPM; **Forge EMP LLC owns it**. Creature Codex is a planned ABSOL LLC collectibles/TCG/3D-printed-display operating brand, not a separate LLC or Forge EMP asset; DBA/eBay setup unverified. Keep separate product-level contribution tracking, no speculative purchases.

References: [launch issue #1](https://github.com/ABSOL7471/Scopewright/issues/1), [cash-first issue #2](https://github.com/ABSOL7471/Scopewright/issues/2), `scopewright_server.py`, `schema.py`, [PR #6](https://github.com/ABSOL7471/Scopewright/pull/6).
