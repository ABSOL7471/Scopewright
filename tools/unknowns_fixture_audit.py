"""Offline, fictional-notes-only reviewer marker audit for Scopewright.

Does not call Ollama, validate generated scope facts, or change production behavior.
Run: python tools/unknowns_fixture_audit.py
"""
import re

MARKERS = (
    ("tbd", re.compile(r"\bTBD\b", re.I)),
    ("verify", re.compile(r"\b(?:verify|confirm|inspection needed|engineer review needed)\b", re.I)),
    ("undecided", re.compile(r"\b(?:undecided|maybe)\b", re.I)),
    ("question", re.compile(r"\b[\w-]+\?")),
)


def review_markers(notes):
    """Return source-exact, advisory markers. Not semantic coverage claims."""
    if not isinstance(notes, str):
        raise TypeError("notes must be a string")
    out = []
    for kind, pattern in MARKERS:
        for match in pattern.finditer(notes):
            start, end = match.span()
            left = max(notes.rfind(".", 0, start), notes.rfind("\n", 0, start)) + 1
            right_period = notes.find(".", end)
            right_newline = notes.find("\n", end)
            boundaries = [p for p in (right_period, right_newline) if p != -1]
            right = min(boundaries) if boundaries else len(notes)
            excerpt = notes[left:right].strip()[:160]
            out.append({"kind": kind, "marker": match.group(0), "excerpt": excerpt, "start": start, "end": end})
    return sorted(out, key=lambda x: (x["start"], x["end"]))


def selftest():
    cases = [
        ("U01", "Guest bath. Tile TBD. Keep tub.", {"tbd"}),
        ("U02", "Floor by doorway soft?", {"question"}),
        ("U03", "Verify framing before railing install.", {"verify"}),
        ("U04", "Vanity stays maybe; paint color undecided.", {"undecided"}),
        ("U05", "12x16 deck, composite or cedar? Confirm with owner.", {"question", "verify"}),
        ("U06", "Replace 4 smoke alarms. Customer confirmed white.", set()),
        ("U07", "Install TBD brand light, verify circuit.", {"tbd", "verify"}),
        ("U08", 'Scope note: quote includes the literal label "TBD" printed on an existing storage bin.', {"tbd"}),
        ("U09", "Replace trim; material choice? Homeowner to confirm.", {"question", "verify"}),
        ("U10", "Deck beam looks damaged. Engineer review needed.", {"verify"}),
    ]
    for name, notes, expected in cases:
        original = notes
        found = review_markers(notes)
        kinds = {x["kind"] for x in found}
        assert expected <= kinds, (name, kinds, expected)
        if name == "U06":
            assert not found, (name, found)
        if name == "U07":
            assert len(found) >= 2, (name, found)
        for item in found:
            assert item["marker"] in notes and item["excerpt"] in notes, (name, item)
        assert notes == original, name
        print(name + ": PASS (advisory markers: " + str(len(found)) + ")")
    repeated = review_markers("TBD. TBD.")
    assert len(repeated) == 2, repeated
    assert [x["start"] for x in repeated] == [0, 5], repeated
    assert all("start" in x and "end" in x for x in repeated)
    print("A03: PASS (duplicate markers retain distinct source offsets)")
    print("10/10 original fictional fixtures plus A03 offset regression passed; NOT an LLM or UI validation")


if __name__ == "__main__":
    selftest()
