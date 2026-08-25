# Scopewright eval results

**Run:** August 25, 2026 · 12 golden cases · RTX 3060 12 GB (120 W cap) ·
temperature 0.2 · one retry allowed on invalid JSON · scored by
`eval_harness.py` (raw per-case numbers: `results-qwen2.5-coder-7b.json`,
`results-qwen2.5-14b.json`).

**Caveat up front:** the golden set is still the AI-drafted DRAFT set
(`golden/README.md`). These numbers measure the *pipeline* honestly, but
they will not be treated as the product's numbers until the cases are
replaced with real jobs written by a working general contractor. That
replacement is in progress.

## Side by side

| metric | qwen2.5-coder:7b | qwen2.5:14b |
|---|---|---|
| valid JSON (with ≤1 retry) | **100%** | **100%** |
| expected elements covered | 93% | **96%** |
| expected exclusions matched | 17% | **36%** |
| **invented items (hallucinations)** | **0%** | **0%** |
| unknowns routed to open questions | 61% | **65%** |
| avg seconds per scope | **15.6** | 25.1 |

## What the numbers say

**The constraint architecture works.** Zero forbidden inventions on both
models across all 12 cases — no dollar amounts, brands, or dimensions that
weren't in the notes. That's the metric a contractor should care about
most, and it comes from the schema/validator design, not from model size:
the model proposes, the code refuses to repair anything content-shaped.

**14b is better at everything, for 1.6× the wait.** Element coverage,
exclusions, and open-question honesty all improve. If your machine fits
the 9 GB model, pick it in ☰ Settings; Auto stays on the 7b coder because
16 seconds feels like a tool and 25 starts to feel like a queue.

**The exclusions number is partly a measurement artifact.** Both models
*write* exclusions on every scope (typically 4–7). The low match rate is
substring-matching against the draft set's expected phrasings — e.g. the
model writes "correction of concealed conditions discovered during
demolition" where the golden case expects "concealed conditions behind
walls". Real-GC-authored cases with intent-level expectations will make
this metric meaningful; until then read it as "wording differs", not
"protections missing". The doubling from 7b→14b is still signal — the
bigger model tracks the requested wording more closely.

**Open-question honesty (61–65%) is the real gap.** When notes leave
something unresolved, the models still sometimes resolve it as an
assumption instead of asking. This is the next prompt-engineering target,
and the metric to watch when the real golden set lands.

## Negative result, kept

An earlier single-case run caught the prompt's worked example bleeding
into outputs (open questions about "paint color" from a different job).
An explicit anti-bleed rule fixed the cross-contamination, but one faint
echo ("new toilet on site" as an assumption) still appeared in a 7b run.
Example-bleed is a standing risk of few-shot prompting on small models;
the eval's `forbidden_inventions` lists are how we keep it caught.
