# Scopewright

Paste your messy job-walk notes. Get a structured, client-ready Scope of
Work. All on your own machine — the notes never leave it.

You walk a job, you thumb fragments into your phone — "reloc toilet ~2ft,
tile TBD client picks, subfloor felt soft nr tub" — and then the real work
starts: turning that into a document a client can read, agree to, and sign.
That translation is where evenings go, and where jobs go sideways when it's
skipped. Scopewright does the translation. You do the judgment.

## Why exclusions and allowances are the point

Ask any contractor where disputes come from. It's almost never the work you
listed — it's the work the client *assumed* was included. A scope that only
says what you'll do is half a contract.

So Scopewright treats the boring back half as the product:

- **Exclusions**, always. Demo in the notes? "Concealed conditions behind
  walls" goes in. Painting? "Existing surface defects beyond normal prep."
  Electrical? "Panel upgrades unless noted." The protections you'd write at
  11pm if you weren't tired.
- **Allowances** for anything the client picks. Notes say "tile TBD"? That's
  an allowance line, not a guess at a tile.
- **Open questions**, out loud. Anything the notes didn't answer becomes a
  listed question on the document — *"Is the subfloor sound near the tub?"*
  — instead of a silently invented answer. The model is hard-forbidden from
  making up measurements, brands, or dollar figures; the unknowns section is
  the honesty valve that makes that rule survivable.

## Quickstart

Needs only Python and [Ollama](https://ollama.com) with a chat model:

    ollama pull qwen2.5-coder:7b      # once, or any qwen/llama chat model
    python scopewright_server.py      ->  http://localhost:8431

Stdlib only — no pip install. If Ollama isn't running, the UI says
"Ollama not detected" and tells you what to do; nothing pretends to work.
Model override: `SCOPEWRIGHT_MODEL=llama3.1:8b` (otherwise it picks the
best installed model itself).

From the generated scope: **Download JSON** (the structured data) or
**Open printable proposal** (a clean paper-look HTML document with
signature lines, ready to print or PDF).

## Architecture: the model proposes, the code validates

The LLM never gets the last word.

    notes -> model -> extract JSON -> repair near-misses -> validate
          -> (if invalid) ONE retry with the exact errors -> honest failure

- `schema.py` — the scope structure, a strict validator, and a repair layer
  that fixes boring shape errors (missing optional keys, a string where a
  list belongs) but **refuses** to repair hallucination-prone ones (a
  `sections` that isn't a list, an item with no description). Repairing
  those would mean the code inventing scope.
- `prompt.py` — the GC craft: non-invention rules, the exclusions reflex,
  allowances for client selections, construction-sequence ordering, one
  worked example.
- `llm.py` — Ollama over stdlib urllib, temperature 0.2, robust JSON
  extraction from fenced/prose-wrapped output.
- `scopewright_server.py` — stdlib http.server. The printable proposal is
  rendered by code from validated JSON with every string escaped; the model
  never writes HTML.
- `scopewright.html` — the single-page UI, vanilla JS.

## Evals

`eval/golden/` holds 12 draft cases across the residential range (bath gut,
deck, water damage, punch list…) with messy field-note inputs and per-case
expectations: required elements, required exclusions, and **forbidden
inventions** — strings like `$`, brand names, and dimensions that appear
only if the model hallucinated. `eval/eval_harness.py` runs them against
live Ollama and scores validity, coverage, invention rate, and whether
unknowns landed in open questions.

**Results pending — harness included.** The golden cases are AI-drafted and
marked as such; they're being replaced case-by-case with real examples from
a working GC before the numbers mean anything.

## What this does not do

- **It does not price jobs.** No dollar figures, ever, unless they were in
  your notes. Allowance lines say *how* an amount will be set, not what it
  is.
- **It does not replace judgment.** The output is a draft for the
  contractor to review, edit, and sign — the proposal footer says exactly
  that.
- **It does not guess.** Unknowns become open questions on the document.
  A scope that quietly resolves "tile TBD" into a tile is a scope you'll
  eat the difference on.

## Tests

    python selftest.py     # 60 checks: schema, extraction, prompt, routes, render

All 60 run offline — no Ollama needed; the server checks run against a
mocked model layer, and the "Ollama not detected" path is itself one of
the things under test.

## Screenshots

![Notes to scope](screenshots/scope.png)

*(placeholder — screenshots landing with the first real-GC golden case)*

## Your letterhead

Copy `company.example.json` to `company.json` (gitignored — your details stay
local) and the printable proposal carries your company name, license, and
contact block. Without it, proposals render generic.

## License

MIT — see [LICENSE](LICENSE).

## Author

Jarrett Yount — jarrettyount1@gmail.com · github.com/ABSOL7471
