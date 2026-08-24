"""
The Scope of Work contract: what a scope IS, and what to do when the model
almost produces one.

This is the "code validates" half of the architecture. The model proposes a
JSON object; this module decides whether it is a real scope. Two layers:

    validate(obj)  ->  (ok, errors)      strict, no mercy, plain-English errors
    repair(obj)    ->  (obj, repairs)    coerce near-misses before validating

repair() fixes the boring failure modes local models actually produce -
a missing optional key, a bare string where a list belongs, a number where
a string belongs. It deliberately does NOT repair the hallucination-prone
failures: if "sections" is not a list, or an item has no description, the
model didn't almost-succeed, it produced something else wearing the schema's
clothes. Those go back as validation errors for the one retry, then honest
failure. Repairing them would mean the code inventing scope, which is the
exact sin this tool exists to prevent.
"""

# The shape, for reference (prompt.py teaches it to the model):
#
# {
#   "project_title": str,
#   "client_summary": str,
#   "sections": [ { "name": str,
#                   "items": [ { "description": str,
#                                "quantity": str|null,
#                                "unit": str|null,
#                                "notes": str|null } ] } ],
#   "exclusions": [str],
#   "allowances": [ { "description": str, "amount_note": str } ],
#   "assumptions": [str],
#   "change_order_terms": str,
#   "open_questions": [str]
# }

TOP_KEYS = ("project_title", "client_summary", "sections", "exclusions",
            "allowances", "assumptions", "change_order_terms",
            "open_questions")

STRING_LIST_KEYS = ("exclusions", "assumptions", "open_questions")
ITEM_OPTIONAL_KEYS = ("quantity", "unit", "notes")


def validate(obj):
    """Strict check. Returns (ok, errors) where errors are plain English -
    they get appended to the retry prompt, so a local model has to be able
    to act on them."""
    errors = []
    if not isinstance(obj, dict):
        return False, ["top level must be a JSON object"]

    for key in ("project_title", "client_summary"):
        v = obj.get(key)
        if not isinstance(v, str) or not v.strip():
            errors.append("%s must be a non-empty string" % key)
    if not isinstance(obj.get("change_order_terms"), str):
        errors.append("change_order_terms must be a string")

    sections = obj.get("sections")
    if not isinstance(sections, list):
        errors.append("sections must be a list of section objects")
    elif not sections:
        errors.append("sections must contain at least one section")
    else:
        for i, sec in enumerate(sections):
            if not isinstance(sec, dict):
                errors.append("sections[%d] must be an object with"
                              " name and items" % i)
                continue
            name = sec.get("name")
            if not isinstance(name, str) or not name.strip():
                errors.append("sections[%d].name must be a non-empty"
                              " string" % i)
            items = sec.get("items")
            if not isinstance(items, list):
                errors.append("sections[%d].items must be a list" % i)
                continue
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append("sections[%d].items[%d] must be an"
                                  " object" % (i, j))
                    continue
                desc = item.get("description")
                if not isinstance(desc, str) or not desc.strip():
                    errors.append("sections[%d].items[%d].description must"
                                  " be a non-empty string" % (i, j))
                for opt in ITEM_OPTIONAL_KEYS:
                    v = item.get(opt)
                    if v is not None and not isinstance(v, str):
                        errors.append("sections[%d].items[%d].%s must be a"
                                      " string or null" % (i, j, opt))

    for key in STRING_LIST_KEYS:
        v = obj.get(key)
        if not isinstance(v, list):
            errors.append("%s must be a list of strings" % key)
        else:
            for i, s in enumerate(v):
                if not isinstance(s, str):
                    errors.append("%s[%d] must be a string" % (key, i))

    allowances = obj.get("allowances")
    if not isinstance(allowances, list):
        errors.append("allowances must be a list")
    else:
        for i, a in enumerate(allowances):
            if (not isinstance(a, dict)
                    or not isinstance(a.get("description"), str)
                    or not a.get("description", "").strip()
                    or not isinstance(a.get("amount_note"), str)):
                errors.append("allowances[%d] must be an object with string"
                              " description and amount_note" % i)

    return (not errors), errors


def repair(obj):
    """Coerce near-misses. Returns (obj, repairs_made) where repairs_made is
    a list of plain-English notes - the UI shows them, because a client
    document assembled with silent fixups is a document you can't trust.

    Never invents content: every repair either fills an empty container or
    reshapes text the model already wrote."""
    repairs = []
    if not isinstance(obj, dict):
        return obj, repairs  # not repairable; validate() will say why

    obj = dict(obj)  # never mutate the caller's object

    # Scalar strings: fill missing with empty, stringify stray numbers.
    for key in ("project_title", "client_summary", "change_order_terms"):
        v = obj.get(key)
        if key not in obj or v is None:
            obj[key] = ""
            repairs.append("filled missing %s" % key)
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            obj[key] = str(v)
            repairs.append("coerced %s from number to string" % key)

    # Lists of strings: missing -> [], bare string -> [string],
    # objects inside -> their description text if they have one.
    for key in STRING_LIST_KEYS:
        v = obj.get(key)
        if key not in obj or v is None:
            obj[key] = []
            repairs.append("filled missing %s with []" % key)
        elif isinstance(v, str):
            obj[key] = [v] if v.strip() else []
            repairs.append("wrapped bare %s string into a list" % key)
        elif isinstance(v, list):
            cleaned, changed = [], False
            for entry in v:
                if isinstance(entry, str):
                    cleaned.append(entry)
                elif entry is None:
                    changed = True
                elif isinstance(entry, dict) and isinstance(
                        entry.get("description"), str):
                    cleaned.append(entry["description"])
                    changed = True
                elif isinstance(entry, (int, float)) and not isinstance(
                        entry, bool):
                    cleaned.append(str(entry))
                    changed = True
                else:
                    cleaned.append(entry)  # leave it; validate() rejects
            if changed:
                obj[key] = cleaned
                repairs.append("normalized entries in %s" % key)

    # Allowances: missing -> [], bare string(s) -> objects, missing
    # amount_note -> "" (an allowance with no note is still an allowance).
    v = obj.get("allowances")
    if "allowances" not in obj or v is None:
        obj["allowances"] = []
        repairs.append("filled missing allowances with []")
    elif isinstance(v, str):
        obj["allowances"] = ([{"description": v, "amount_note": ""}]
                             if v.strip() else [])
        repairs.append("wrapped bare allowances string into a list")
    elif isinstance(v, list):
        fixed, changed = [], False
        for entry in v:
            if isinstance(entry, str):
                fixed.append({"description": entry, "amount_note": ""})
                changed = True
            elif isinstance(entry, dict):
                e = dict(entry)
                if not isinstance(e.get("amount_note"), str):
                    if e.get("amount_note") is None or "amount_note" not in e:
                        e["amount_note"] = ""
                        changed = True
                fixed.append(e)
            else:
                fixed.append(entry)  # validate() rejects
        if changed:
            obj["allowances"] = fixed
            repairs.append("normalized allowances entries")

    # Sections: only repair INSIDE a well-shaped skeleton. A non-list
    # sections, a non-dict section, a non-list items, a missing
    # description - none of those get repaired here. See module docstring.
    if isinstance(obj.get("sections"), list):
        for sec in obj["sections"]:
            if not isinstance(sec, dict):
                continue
            items = sec.get("items")
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue
                for opt in ITEM_OPTIONAL_KEYS:
                    v = item.get(opt)
                    if opt not in item:
                        item[opt] = None
                        # so common it would drown real repairs; count once
                        note = "filled missing optional item fields with null"
                        if note not in repairs:
                            repairs.append(note)
                    elif isinstance(v, (int, float)) and not isinstance(
                            v, bool):
                        item[opt] = str(v)
                        note = "coerced numeric item fields to strings"
                        if note not in repairs:
                            repairs.append(note)

    return obj, repairs
