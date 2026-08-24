"""
Golden-case eval: run each case in eval/golden/ through the real pipeline
against live Ollama and score what came back.

    python eval/eval_harness.py            # all cases
    python eval/eval_harness.py fence      # just the named case(s)

Metrics per case, aggregated at the end:

  json_valid          the pipeline returned a schema-valid scope at all
  element_coverage    expected_elements found in the scope (fuzzy, ci)
  exclusion_coverage  expected_exclusions found in the exclusions list
  invention_rate      forbidden_inventions present ANYWHERE = hallucination
  oq_honesty          expected_open_questions that landed in open_questions
                      (unknowns surfaced, not silently resolved)

Matching is deliberately asymmetric: expected phrases match leniently
(substring OR all significant tokens present) because wording varies;
forbidden phrases match by strict substring only, so a hallucination flag
means the string is actually there.

Writes eval/results.json and prints a table. If Ollama is down it says so
and exits nonzero - it never fakes results.
"""

import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import llm  # noqa: E402

GOLDEN = os.path.join(HERE, "golden")
RESULTS = os.path.join(HERE, "results.json")


def flatten(obj):
    """Every string in the scope, joined, lowercased."""
    parts = []

    def walk(x):
        if isinstance(x, str):
            parts.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(obj)
    return " ".join(parts).lower()


def norm(s):
    return re.sub(r"[^a-z0-9$]+", " ", s.lower()).strip()


def found_lenient(phrase, text):
    """Substring, or all significant tokens present. Case-insensitive."""
    p, t = norm(phrase), norm(text)
    if not p:
        return False
    if p in t:
        return True
    tokens = [w for w in p.split() if len(w) >= 3]
    return bool(tokens) and all(w in t for w in tokens)


def found_strict(phrase, text):
    """Plain substring - used for forbidden inventions so a hallucination
    flag means the string is really in the document."""
    return phrase.lower() in text.lower()


def run_case(name):
    d = os.path.join(GOLDEN, name)
    notes = open(os.path.join(d, "notes.txt"), encoding="utf-8").read()
    exp = json.load(open(os.path.join(d, "expected.json"), encoding="utf-8"))

    t0 = time.time()
    result = {"case": name, "seconds": None, "json_valid": False,
              "element_coverage": 0.0, "exclusion_coverage": 0.0,
              "invention_rate": 0.0, "oq_honesty": None,
              "missing_elements": [], "missing_exclusions": [],
              "inventions_found": [], "missing_open_questions": [],
              "error": None}
    try:
        scope, repairs, model = llm.generate_scope(notes)
    except llm.OllamaDown:
        raise
    except Exception as e:
        result["seconds"] = round(time.time() - t0, 1)
        result["error"] = str(e)
        return result
    result["seconds"] = round(time.time() - t0, 1)
    result["json_valid"] = True
    result["model"] = model
    result["repairs"] = repairs

    everything = flatten(scope)
    exclusions_text = " ".join(scope.get("exclusions", [])).lower()
    oq_text = " ".join(scope.get("open_questions", [])).lower()

    elems = exp.get("expected_elements", [])
    hits = [p for p in elems if found_lenient(p, everything)]
    result["element_coverage"] = len(hits) / len(elems) if elems else 1.0
    result["missing_elements"] = [p for p in elems if p not in hits]

    excl = exp.get("expected_exclusions", [])
    hits = [p for p in excl if found_lenient(p, exclusions_text)]
    result["exclusion_coverage"] = len(hits) / len(excl) if excl else 1.0
    result["missing_exclusions"] = [p for p in excl if p not in hits]

    forb = exp.get("forbidden_inventions", [])
    bad = [p for p in forb if found_strict(p, everything)]
    result["invention_rate"] = len(bad) / len(forb) if forb else 0.0
    result["inventions_found"] = bad

    oq = exp.get("expected_open_questions", [])
    if oq:
        hits = [p for p in oq if found_lenient(p, oq_text)]
        result["oq_honesty"] = len(hits) / len(oq)
        result["missing_open_questions"] = [p for p in oq if p not in hits]
    return result


def main():
    cases = sorted(n for n in os.listdir(GOLDEN)
                   if os.path.isdir(os.path.join(GOLDEN, n)))
    picked = [a for a in sys.argv[1:] if not a.startswith("-")]
    if picked:
        cases = [c for c in cases if c in picked]
        if not cases:
            print("no matching cases; have: " + ", ".join(
                sorted(os.listdir(GOLDEN))))
            return 2

    st = llm.status()
    if not st["ollama"]:
        print("Ollama is not running - the eval needs the live model and"
              " will not fake results. Start Ollama and re-run.")
        return 1
    if not st["model"]:
        print("Ollama is up but no usable chat model is installed."
              " Try: ollama pull qwen2.5-coder:7b")
        return 1
    print("model: %s   cases: %d\n" % (st["model"], len(cases)))

    results = []
    hdr = "%-22s %5s %6s %6s %6s %6s %6s" % (
        "case", "valid", "elem", "excl", "inv", "oq", "sec")
    print(hdr)
    print("-" * len(hdr))
    for name in cases:
        r = run_case(name)
        results.append(r)
        if r["error"]:
            print("%-22s %5s  ERROR %s" % (name, "no", r["error"][:60]))
            continue
        print("%-22s %5s %6.0f%% %5.0f%% %5.0f%% %6s %6s" % (
            name, "yes",
            r["element_coverage"] * 100, r["exclusion_coverage"] * 100,
            r["invention_rate"] * 100,
            ("%.0f%%" % (r["oq_honesty"] * 100)
             if r["oq_honesty"] is not None else "n/a"),
            r["seconds"]))

    ok = [r for r in results if r["json_valid"]]
    summary = {
        "model": st["model"],
        "cases": len(results),
        "json_valid_rate": len(ok) / len(results) if results else 0.0,
        "element_coverage": (sum(r["element_coverage"] for r in ok)
                             / len(ok)) if ok else 0.0,
        "exclusion_coverage": (sum(r["exclusion_coverage"] for r in ok)
                               / len(ok)) if ok else 0.0,
        "invention_rate": (sum(r["invention_rate"] for r in ok)
                           / len(ok)) if ok else 0.0,
        "oq_honesty": (lambda xs: sum(xs) / len(xs) if xs else None)(
            [r["oq_honesty"] for r in ok if r["oq_honesty"] is not None]),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("-" * len(hdr))
    print("json_valid %.0f%%   elements %.0f%%   exclusions %.0f%%   "
          "inventions %.0f%%   oq honesty %s" % (
              summary["json_valid_rate"] * 100,
              summary["element_coverage"] * 100,
              summary["exclusion_coverage"] * 100,
              summary["invention_rate"] * 100,
              ("%.0f%%" % (summary["oq_honesty"] * 100)
               if summary["oq_honesty"] is not None else "n/a")))

    with open(RESULTS, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cases": results}, f, indent=2)
    print("\nwrote %s" % RESULTS)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except llm.OllamaDown as e:
        print("Ollama went away mid-run: %s" % e)
        raise SystemExit(1)
