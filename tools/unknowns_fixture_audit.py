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
            # Keep the actual marker in the excerpt even in long unpunctuated notes.
            excerpt_start = left if start - left < 100 else max(left, start - 60)
            excerpt_end = min(right, excerpt_start + 160)
            excerpt = notes[excerpt_start:excerpt_end].strip()
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
    long_notes = "Kitchen " + ("existing finish " * 30) + "tile TBD and owner to select."
    long_hits = review_markers(long_notes)
    assert len(long_hits) == 1 and "TBD" in long_hits[0]["excerpt"], long_hits
    assert long_hits[0]["excerpt"] in long_notes, long_hits
    print("A04: PASS (long-note excerpt preserves actual uncertainty marker)")
    print("A03: PASS (duplicate markers retain distinct source offsets)")
    print("10/10 original fictional fixtures plus A03 offset regression passed; NOT an LLM or UI validation")


if __name__ == "__main__":
    selftest()
