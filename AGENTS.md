# AGENTS.md — Scopewright / ABSOL Technologies

This is **public, repository-scoped guidance** for Codex or another AI coding agent (including an agent called "Venom AI") when working in `ABSOL7471/Scopewright`. Do not add private company financials, customer information, secrets, account details, or personal records to this repository.

## Mission and priorities
1. **Cash first.** Help the existing business generate dependable income from Scopewright without speculative spending, new entities, or avoidable subscriptions.
2. **Product focus.** Scopewright turns rough residential construction job-walk notes into draft scopes of work with inclusions, exclusions, allowances, and unresolved questions clearly flagged. It is **not** an automatic price estimator, law firm, architect, engineer, or substitute for the contractor's review.
3. **First commercial milestone:** three paying, contractor-reviewed scope-writing pilot jobs. Proposed pricing to test: **$99** simple job; **$149–$199** involved jobs. These are test prices, not validated revenue.
4. **Reliability before growth.** Increase open-question coverage and test against 20 permissioned/anonymized real construction cases before relying on broad accuracy claims.
5. **Cost discipline.** Favor the existing local-first Python/Ollama app, current tooling, and low-cost outreach. Do not purchase subscriptions, ad spend, hosting, equipment, or inventory without owner approval.

## Verified project starting points
- See `README.md` for app behavior, local setup, and current documented limitations.
- See `docs/paid-pilot-kit.md` for the draft paid-pilot offer, example and manual delivery workflow.
- See GitHub issues [#1](https://github.com/ABSOL7471/Scopewright/issues/1) (launch plan) and [#2](https://github.com/ABSOL7471/Scopewright/issues/2) (cash-first ABSOL LLC strategy).
- Start with `python selftest.py`. The README describes 92 offline checks, but **run them and report observed results** rather than asserting tests currently pass.
- See `eval/EVAL.md`. The initial 12 AI-drafted test cases are *not proof of real-world reliability*. In August 2026, the stored evaluation reported underperformance in routing unknowns into open questions. Keep this limitation visible.

## Business ownership boundaries
- **ABSOL LLC** is the existing legal company. ABSOL Construction is the current construction line; `ABSOL Technologies` is a **proposed** software/AI operating brand, not yet confirmed registered.
- **Creature Codex** is a proposed TCG/collectibles/3D-printed-products operating brand of ABSOL LLC, subject to verification of legal name, inventory ownership, and marketplace business identity. Do not divert Scopewright launch funds into speculative inventory.
- **ForgeEPM belongs to Forge EMP LLC**, a **separate legal entity**. ABSOL LLC developed it, but **does not own the ForgeEPM product**. Do not claim, merge, license, transfer, or market ForgeEPM as ABSOL-owned without a documented agreement and permission.
- Scopewright's public `LICENSE` is MIT and currently bears an individual copyright notice. Do not casually remove notices or claim exclusive ABSOL LLC ownership without legal review.
- No Oregon DBA registrations or new legal structures should be represented as completed solely from these planning documents.

## Engineering and commercial rules
- Preserve local-first privacy promises. A **done-for-you** service where a contractor sends notes to an operator is a different data flow; require permission, privacy terms, careful retention, and human review.
- Never fabricate dimensions, materials, permits, code compliance, scope decisions, pricing, market demand, paid customers, evaluations, or test results.
- Prefer small, reviewable changes and pull requests. Do not deploy, publish marketing, send emails, sign contracts, file government paperwork, pay money, connect financial institutions, or alter customer data without explicit human approval.
- Work on a proposal / branch with diffs and test output. Get approval before production releases, destructive edits, or merging changes that affect pricing, licensing, or data handling.
- Keep the owner decision burden small: where possible complete the groundwork and present **one practical 5–10-minute action** and a measurable status.
- Do not intermingle Forge EMP LLC books with ABSOL LLC books. Keep separate division-level P&L for construction, technology/Scopewright and Creature Codex; verify actual bank/transaction feeds before asserting cash, profits, runway, or taxes.

## Immediate next work for an agent
1. Read the repo, `README.md`, `docs/paid-pilot-kit.md`, `eval/EVAL.md`, and issues #1/#2.
2. Run existing offline tests and record actual pass/fail output; don't overstate missing Ollama model availability.
3. Identify and prioritize one **open-question / unsupported-assumption** defect that blocks reliable paid pilots.
4. Propose a focused patch with regression tests, no unrelated refactor and no added expenses.
5. Produce a contractor-reviewable demo only from fictional or permissioned/anonymized notes; describe what was actually executed.
6. Report test evidence, risks, cost, and the next one human approval / action.
