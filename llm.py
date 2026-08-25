"""
The Ollama backend. Stdlib urllib against http://localhost:11434, non-
streaming, temperature 0.2.

Failure philosophy: this module never pretends. If Ollama is down, callers
get OllamaDown with a message a human can act on, and the UI shows an
"Ollama not detected" state instead of a broken button. If the model can't
produce a valid scope after repair + one retry, callers get GenerationError
- not a half-repaired guess.

The pipeline is: chat -> extract_json -> schema.repair -> schema.validate
-> (on failure) ONE retry with the validation errors appended -> honest
failure. The retry exists because local models fix shape errors well when
told exactly what's wrong; more than one retry is just burning GPU on a
model that isn't going to get there.
"""

import json
import os
import re
import urllib.error
import urllib.request

import prompt
import schema

OLLAMA = os.environ.get("SCOPEWRIGHT_OLLAMA", "http://localhost:11434")

# Model choice: env wins, then the coder model that behaves best on strict
# JSON, then any qwen/llama-family chat model that's installed. Embedding
# and vision-only models are never a sensible pick.
PREFERRED = ("qwen2.5-coder:7b", "qwen2.5-coder")
CHAT_HINTS = ("qwen", "llama", "mistral", "gemma", "phi", "deepseek")
NEVER = ("embed", "bge", "nomic", "minilm", "rerank")

# Vision: only used for transcribing photos of notes. Capability-gated -
# without one of these installed, the photo button simply doesn't appear.
VISION_HINTS = ("qwen2.5vl", "qwen2-vl", "llava", "minicpm-v", "moondream",
                "llama3.2-vision", "bakllava")

TRANSCRIBE_PROMPT = (
    "Transcribe the notes in this photo exactly as written - handwritten or "
    "typed job-site notes. Keep the original line breaks, abbreviations, "
    "misspellings, arrows, and question marks; expand nothing and add "
    "nothing. If a word is unreadable, write [illegible] in its place. "
    "Output only the transcription, no commentary.")


class OllamaDown(Exception):
    """Ollama unreachable, or reachable with nothing usable installed."""


class GenerationError(Exception):
    """The model could not produce a valid scope. Honest failure."""


def list_models(timeout=3):
    """Names of installed models, or None if Ollama is unreachable.
    None vs [] matters: down and empty get different error messages."""
    try:
        with urllib.request.urlopen(OLLAMA + "/api/tags",
                                    timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return None


def pick_model(names):
    """Pure function so the preference order is testable offline."""
    env = os.environ.get("SCOPEWRIGHT_MODEL")
    if env:
        return env
    if not names:
        return None
    usable = [n for n in names
              if n and not any(b in n.lower() for b in NEVER)]
    for pref in PREFERRED:
        for n in usable:
            if n == pref or n.startswith(pref + ":"):
                return n
    for n in usable:
        if any(h in n.lower() for h in CHAT_HINTS):
            return n
    return usable[0] if usable else None


def pick_vision_model(names):
    """Pure function, like pick_model. None when no vision model installed."""
    env = os.environ.get("SCOPEWRIGHT_VISION_MODEL")
    if env:
        return env
    if not names:
        return None
    for hint in VISION_HINTS:
        for n in names:
            if n and hint in n.lower():
                return n
    return None


def status():
    """For GET /api/status and the UI's capability gating."""
    names = list_models()
    if names is None:
        return {"ollama": False, "model": None, "vision_model": None}
    return {"ollama": True, "model": pick_model(names),
            "vision_model": pick_vision_model(names)}


def chat(model, messages, timeout=600):
    """Non-streaming /api/chat. Returns the assistant message content."""
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA + "/api/chat", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise OllamaDown("Ollama returned HTTP %d for model %r. %s"
                         % (e.code, model, detail))
    except Exception as e:
        raise OllamaDown("Could not reach Ollama at %s (%s). Is it running?"
                         % (OLLAMA, e))
    return (data.get("message") or {}).get("content", "")


_FENCE = re.compile(r"```[a-zA-Z]*\s*(.*?)```", re.S)


def extract_json(text):
    """Find the JSON object in whatever the model actually said.

    Local models wrap JSON in fences, preambles ("Here is the scope:"),
    and trailing commentary. Strategy: prefer fenced content, then scan
    from the first '{' with a string-aware brace counter so braces inside
    string values don't end the object early. Returns a dict, or None -
    never raises, never "fixes" broken JSON."""
    if not text:
        return None
    candidates = [m.strip() for m in _FENCE.findall(text)] + [text]
    for cand in candidates:
        obj = _outermost_object(cand)
        if obj is not None:
            return obj
    return None


def _outermost_object(text):
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        if isinstance(obj, dict):
                            return obj
                    except ValueError:
                        pass
                    break
        start = text.find("{", start + 1)
    return None


def transcribe_image(image_b64):
    """Photo of notes -> verbatim text via a local vision model.
    Returns (text, model_name). The transcription goes back to the HUMAN
    for review in the notes box - it is never fed to generate_scope
    blind, because a misread word must become an edit, not a line item."""
    names = list_models()
    if names is None:
        raise OllamaDown(
            "Ollama not detected at %s. Start it and try again." % OLLAMA)
    model = pick_vision_model(names)
    if not model:
        raise OllamaDown(
            "No vision model installed. Try: ollama pull qwen2.5vl:7b")
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": TRANSCRIBE_PROMPT,
                      "images": [image_b64]}],
        "stream": False,
        "options": {"temperature": 0},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA + "/api/chat", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        raise OllamaDown("Ollama returned HTTP %d for vision model %r. %s"
                         % (e.code, model, detail))
    except Exception as e:
        raise OllamaDown("Could not reach Ollama at %s (%s)." % (OLLAMA, e))
    text = ((data.get("message") or {}).get("content", "") or "").strip()
    if not text:
        raise GenerationError(
            "The vision model (%s) returned an empty transcription. "
            "Try a sharper, better-lit photo." % model)
    return text, model


def generate_scope(notes):
    """The full pipeline. Returns (scope, repairs_made, model_name).
    Raises OllamaDown or GenerationError with messages meant for humans."""
    names = list_models()
    if names is None:
        raise OllamaDown(
            "Ollama not detected at %s. Start it (`ollama serve` or the "
            "desktop app) and try again." % OLLAMA)
    model = pick_model(names)
    if not model:
        raise OllamaDown(
            "Ollama is running but no usable chat model is installed. "
            "Try: ollama pull qwen2.5-coder:7b")

    messages = [
        {"role": "system", "content": prompt.SYSTEM_PROMPT},
        {"role": "user", "content": prompt.user_prompt(notes)},
    ]

    raw = chat(model, messages)
    obj = extract_json(raw)
    if obj is None:
        errors = ["output contained no parseable JSON object"]
    else:
        obj, repairs = schema.repair(obj)
        ok, errors = schema.validate(obj)
        if ok:
            return obj, repairs, model

    # One retry, with the validator's exact complaints. Then honesty.
    messages.append({"role": "assistant", "content": raw})
    messages.append({"role": "user", "content": prompt.retry_prompt(errors)})
    raw2 = chat(model, messages)
    obj2 = extract_json(raw2)
    if obj2 is not None:
        obj2, repairs = schema.repair(obj2)
        ok, errors2 = schema.validate(obj2)
        if ok:
            return obj2, repairs, model
        errors = errors2

    raise GenerationError(
        "The model (%s) could not produce a valid scope after one retry. "
        "Last problems: %s. Try rewording the notes, or a stronger model "
        "via SCOPEWRIGHT_MODEL." % (model, "; ".join(errors[:6])))
