"""Offline gate for Scopewright: schema, extraction, prompt, routes, render.
No Ollama needed - the llm layer is mocked for the server checks, and the
mocked-vs-live boundary is itself under test."""
import copy
import json
import os
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import llm
import prompt
import schema
import scopewright_server as S

fails = []
total = [0]


def check(label, cond, detail=""):
    total[0] += 1
    print(("  PASS  " if cond else "  FAIL  ") + label
          + ((" " + str(detail)) if detail and not cond else ""))
    if not cond:
        fails.append(label)


GOOD = {
    "project_title": "Hall Bath Gut Renovation",
    "client_summary": "Full gut and rebuild of the hall bathroom.",
    "sections": [
        {"name": "Demolition",
         "items": [{"description": "Demolish finishes to studs",
                    "quantity": None, "unit": None, "notes": None}]},
        {"name": "Plumbing",
         "items": [{"description": "Relocate toilet flange",
                    "quantity": "2", "unit": "ft",
                    "notes": "pending joist check"}]},
    ],
    "exclusions": ["Concealed conditions behind walls or under floors"],
    "allowances": [{"description": "Tile selection",
                    "amount_note": "allowance set at selection"}],
    "assumptions": ["Water can be shut off during work hours"],
    "change_order_terms": "Work outside this scope requires a signed"
                          " change order.",
    "open_questions": ["Is the subfloor sound near the tub?"],
}

# ---------------------------------------------------------------- schema
ok, errors = schema.validate(GOOD)
check("validate accepts a complete scope", ok, errors)

ok, errors = schema.validate("not a dict")
check("validate rejects non-object top level", not ok and "object" in errors[0])

bad = copy.deepcopy(GOOD)
bad["project_title"] = ""
ok, errors = schema.validate(bad)
check("validate rejects empty project_title",
      not ok and any("project_title" in e for e in errors))

bad = copy.deepcopy(GOOD)
bad["sections"] = "Demolition then plumbing"
ok, errors = schema.validate(bad)
check("validate rejects sections that are not a list",
      not ok and any("sections must be a list" in e for e in errors))

bad = copy.deepcopy(GOOD)
bad["sections"] = []
ok, errors = schema.validate(bad)
check("validate rejects empty sections", not ok)

bad = copy.deepcopy(GOOD)
del bad["sections"][0]["items"][0]["description"]
ok, errors = schema.validate(bad)
check("validate rejects an item without a description",
      not ok and any("description" in e for e in errors))

bad = copy.deepcopy(GOOD)
bad["sections"][0]["items"][0]["quantity"] = 2
ok, errors = schema.validate(bad)
check("validate flags numeric quantity (string or null only)", not ok)

# repair: the boring near-misses
near = copy.deepcopy(GOOD)
del near["exclusions"]
del near["open_questions"]
near["assumptions"] = "Water can be shut off"
near["allowances"] = ["Tile selection"]
del near["sections"][0]["items"][0]["quantity"]
del near["sections"][0]["items"][0]["unit"]
repaired, repairs = schema.repair(near)
ok, errors = schema.validate(repaired)
check("repair makes the near-miss validate", ok, errors)
check("repair fills missing list keys with []",
      repaired["exclusions"] == [] and repaired["open_questions"] == [])
check("repair wraps bare string into a list",
      repaired["assumptions"] == ["Water can be shut off"])
check("repair coerces string allowance to object",
      repaired["allowances"][0]["description"] == "Tile selection"
      and repaired["allowances"][0]["amount_note"] == "")
check("repair fills missing optional item fields with null",
      repaired["sections"][0]["items"][0]["quantity"] is None)
check("repair reports what it did", len(repairs) >= 4, repairs)
check("repair does not mutate the input", "exclusions" not in near)

fixable = copy.deepcopy(GOOD)
fixable["sections"][1]["items"][0]["quantity"] = 2
repaired, repairs = schema.repair(fixable)
ok, _ = schema.validate(repaired)
check("repair coerces numeric quantity to string",
      ok and repaired["sections"][1]["items"][0]["quantity"] == "2")

# repair must NOT rescue hallucination-prone shapes
bad = copy.deepcopy(GOOD)
bad["sections"] = {"Demolition": ["demo stuff"]}
repaired, _ = schema.repair(bad)
ok, errors = schema.validate(repaired)
check("repair refuses to invent sections from a non-list",
      not ok and any("sections must be a list" in e for e in errors))

bad = copy.deepcopy(GOOD)
del bad["sections"][0]["items"][0]["description"]
repaired, _ = schema.repair(bad)
ok, _ = schema.validate(repaired)
check("repair refuses to invent a missing item description", not ok)

r1, _ = schema.repair(GOOD)
check("repair is a no-op on a valid scope (idempotent content)", r1 == GOOD)

# ---------------------------------------------------------- json extraction
payload = json.dumps(GOOD)
check("extract_json: bare object", llm.extract_json(payload) == GOOD)
check("extract_json: ```json fenced",
      llm.extract_json("Here you go:\n```json\n" + payload + "\n```") == GOOD)
check("extract_json: bare ``` fence",
      llm.extract_json("```\n" + payload + "\n```\nHope that helps!") == GOOD)
check("extract_json: prose before and after",
      llm.extract_json("Sure! The scope is: " + payload
                       + " Let me know if you need changes.") == GOOD)
tricky = json.dumps({"project_title": 'Deck ("about 12x16") build',
                     "note": "brace } inside { string"})
check("extract_json: braces inside strings don't truncate",
      llm.extract_json("answer: " + tricky) == json.loads(tricky))
check("extract_json: no JSON at all -> None",
      llm.extract_json("I cannot help with that.") is None)
check("extract_json: empty -> None", llm.extract_json("") is None)
check("extract_json: broken JSON -> None, not a guess",
      llm.extract_json('{"project_title": "Deck", "sections": [') is None)

# ------------------------------------------------------------- model pick
os.environ.pop("SCOPEWRIGHT_MODEL", None)
check("pick_model prefers qwen2.5-coder:7b",
      llm.pick_model(["llama3.1:8b", "qwen2.5-coder:7b",
                      "nomic-embed-text"]) == "qwen2.5-coder:7b")
check("pick_model falls back to a chat model",
      llm.pick_model(["nomic-embed-text", "llama3.1:8b"]) == "llama3.1:8b")
check("pick_model never picks an embedding model",
      llm.pick_model(["nomic-embed-text", "bge-m3"]) is None)
check("pick_model with nothing installed -> None", llm.pick_model([]) is None)
os.environ["SCOPEWRIGHT_MODEL"] = "my-model:latest"
check("SCOPEWRIGHT_MODEL env wins",
      llm.pick_model(["qwen2.5-coder:7b"]) == "my-model:latest")
os.environ.pop("SCOPEWRIGHT_MODEL", None)

# ----------------------------------------------------------------- prompt
p = prompt.SYSTEM_PROMPT
check("prompt forbids inventing", "NEVER invent" in p)
check("prompt bans invented measurements and brands",
      "measurements" in p and "brands" in p and "dollar amounts" in p)
check("prompt routes unknowns to open_questions",
      "open_questions" in p and "not a guess" in p)
check("prompt demands exclusions", "EXCLUSIONS" in p and "concealed" in p)
check("prompt covers allowances for client selections",
      "ALLOWANCES" in p and "client-selectable" in p)
check("prompt orders by construction sequence",
      "construction sequence" in p and "demolition" in p.lower())
check("prompt contains a worked example that parses",
      llm.extract_json(p.split("WORKED EXAMPLE", 1)[1]) is not None)
ex = llm.extract_json(p.split("WORKED EXAMPLE", 1)[1])
ok, errors = schema.validate(ex)
check("worked example validates against the schema", ok, errors)
check("retry prompt carries the validator's errors",
      "sections must be a list" in prompt.retry_prompt(
          ["sections must be a list"]))

# ----------------------------------------------------------------- server
# Mock the llm layer: the server must be bootable and testable with
# Ollama completely absent.
llm.status = lambda: {"ollama": True, "model": "mock-model",
                      "vision_model": "mock-vl"}
llm.generate_scope = lambda notes: (
    copy.deepcopy(GOOD), ["filled missing exclusions with []"], "mock-model")
llm.transcribe_image = lambda b64: ("hall bath gut, reloc toilet ~2ft",
                                    "mock-vl")

srv = ThreadingHTTPServer(("127.0.0.1", 0), S.Handler)
base = "http://127.0.0.1:%d" % srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()


def req(path, payload=None):
    r = urllib.request.Request(
        base + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET")
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, resp.read(), resp.headers.get(
                "Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), ""


s, b, ct = req("/")
check("GET / serves the UI", s == 200 and b"Scopewright" in b
      and "html" in ct)
check("UI has the notes textarea and generate button",
      b'id="notes"' in b and b'id="go"' in b)
check("UI has the Ollama-not-detected banner state",
      b"Ollama not detected" in b)

s, b, _ = req("/api/status")
check("GET /api/status reports the mocked llm layer",
      s == 200 and json.loads(b) == {"ollama": True, "model": "mock-model",
                                     "vision_model": "mock-vl"})

s, b, _ = req("/api/generate", {"notes": "hall bath gut, reloc toilet"})
d = json.loads(b)
check("POST /api/generate runs the pipeline",
      s == 200 and d["scope"]["project_title"] == GOOD["project_title"])
check("generate response carries repairs and model",
      d["repairs"] == ["filled missing exclusions with []"]
      and d["model"] == "mock-model")

s, b, _ = req("/api/generate", {"notes": "   "})
check("generate rejects empty notes with 400", s == 400)
s, b, _ = req("/api/generate", {"notes": "x" * (S.MAX_NOTES + 1)})
check("generate rejects absurdly long notes with 400", s == 400)

llm.generate_scope = _down = (lambda notes: (_ for _ in ()).throw(
    llm.OllamaDown("Ollama not detected at http://localhost:11434.")))
s, b, _ = req("/api/generate", {"notes": "deck build"})
check("generate surfaces OllamaDown as 503 with the message",
      s == 503 and "not detected" in json.loads(b)["error"])

llm.generate_scope = (lambda notes: (_ for _ in ()).throw(
    llm.GenerationError("The model could not produce a valid scope.")))
s, b, _ = req("/api/generate", {"notes": "deck build"})
check("generate surfaces GenerationError as 502 honest failure",
      s == 502 and "could not produce" in json.loads(b)["error"])

s, b, ct = req("/api/render", {"scope": GOOD})
html_out = b.decode("utf-8")
check("POST /api/render returns HTML", s == 200 and "html" in ct
      and html_out.startswith("<!DOCTYPE html>"))
check("render contains the scope content",
      GOOD["project_title"] in html_out
      and "Relocate toilet flange" in html_out
      and GOOD["exclusions"][0] in html_out
      and GOOD["open_questions"][0] in html_out)
check("render shows quantity with unit", "2 ft" in html_out)
check("render includes signature and change-order blocks",
      "Client signature" in html_out and "change order" in html_out)

evil = copy.deepcopy(GOOD)
evil["project_title"] = '<script>alert("xss")</script>'
evil["exclusions"] = ['<img src=x onerror="pwn()">']
s, b, _ = req("/api/render", {"scope": evil})
page = b.decode("utf-8")
check("render escapes model-authored HTML",
      "<script>alert" not in page and "&lt;script&gt;" in page
      and "<img" not in page)

s, b, _ = req("/api/render", {"scope": "not an object"})
check("render rejects a non-object scope with 400", s == 400)

# Photo transcription route (vision, mocked): text comes back for HUMAN
# review in the notes box - the route never chains into generate.
s, b, _ = req("/api/transcribe", {"image": "aGVsbG8="})
d = json.loads(b)
check("POST /api/transcribe returns text + vision model",
      s == 200 and d["text"].startswith("hall bath gut")
      and d["model"] == "mock-vl")
s, b, _ = req("/api/transcribe", {"image": ""})
check("transcribe rejects empty image with 400", s == 400)
s, b, _ = req("/api/transcribe", {"image": "x" * (S.MAX_IMAGE_B64 + 1)})
check("transcribe rejects oversized image with 400", s == 400)
llm.transcribe_image = (lambda b64: (_ for _ in ()).throw(
    llm.OllamaDown("No vision model installed.")))
s, b, _ = req("/api/transcribe", {"image": "aGVsbG8="})
check("transcribe surfaces OllamaDown as 503",
      s == 503 and b"vision" in b.lower())

s, ui_page, _ = req("/")
check("UI has the photo button, capability-gated",
      b'id="photoBtn"' in ui_page and b'id="photoFile"' in ui_page)

s, b, _ = req("/api/nope")
check("unknown route 404s", s == 404)
srv.shutdown()

# Vision model picker (pure function, offline)
check("pick_vision_model finds an installed vision model",
      llm.pick_vision_model(["qwen2.5-coder:7b", "qwen2.5vl:7b"])
      == "qwen2.5vl:7b")
check("pick_vision_model -> None when only chat models installed",
      llm.pick_vision_model(["qwen2.5-coder:7b", "llama3.1:8b"]) is None)
os.environ["SCOPEWRIGHT_VISION_MODEL"] = "my-vl:latest"
check("SCOPEWRIGHT_VISION_MODEL env override wins",
      llm.pick_vision_model(["qwen2.5vl:7b"]) == "my-vl:latest")
del os.environ["SCOPEWRIGHT_VISION_MODEL"]

# ----------------------------------------------------------- golden cases
GOLDEN = os.path.join(HERE, "eval", "golden")
case_dirs = sorted(n for n in os.listdir(GOLDEN)
                   if os.path.isdir(os.path.join(GOLDEN, n)))
check("12 golden cases present", len(case_dirs) == 12, case_dirs)
problems = []
for name in case_dirs:
    d = os.path.join(GOLDEN, name)
    try:
        notes = open(os.path.join(d, "notes.txt"), encoding="utf-8").read()
        exp = json.load(open(os.path.join(d, "expected.json"),
                             encoding="utf-8"))
    except Exception as e:
        problems.append("%s: %s" % (name, e))
        continue
    if len(notes.strip()) < 80:
        problems.append("%s: notes too thin to be a real job walk" % name)
    for key in ("expected_elements", "expected_exclusions",
                "forbidden_inventions"):
        v = exp.get(key)
        if not isinstance(v, list) or not v or not all(
                isinstance(x, str) for x in v):
            problems.append("%s: %s missing/empty" % (name, key))
check("every golden case parses with required keys and real notes",
      not problems, problems)
check("golden README marks the set as DRAFT",
      "DRAFT" in open(os.path.join(GOLDEN, "README.md"),
                      encoding="utf-8").read())

print("\n%d checks, FAILURES: %s" % (
    total[0], fails if fails else "none"))
raise SystemExit(1 if fails else 0)
