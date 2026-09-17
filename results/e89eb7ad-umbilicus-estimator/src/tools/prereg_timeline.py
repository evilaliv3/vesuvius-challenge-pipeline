# This file is a copy of tools/prereg_timeline.py of the working tree and differs from it in one
# way only: the four documents it reads are taken from this folder, the folder that holds each is
# named beside it rather than guessed from the name, and the `document` column names the file
# read. Nothing that computes a number is changed.
"""Which scrolls had been measured before each pre-registration was written, read from the files.

Reviewer's point 2 on the short paper (2026-09-17): the pre-registration of the fifteen references
says it was written before any accuracy number beyond the four of result-d-one-division.md, so the
scrolls that file already reports are in sample for the criteria and the rest are out of sample.
The paper must say which block that makes in sample, and the count must come from the files, not
from memory: this reads the scroll table of result-d-one-division.md, intersects it with the two
blocks of fifteen-config.json, and reads the stated date of each pre-registration from its own
first lines.
It also records how many seeds per slice the pre-registration of the twenty-four scroll run fixed,
against the twenty of the later note, for the clause in Section IV that says why the two differ.

Output: evidence/prereg-timeline.csv, one row per document.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L        # noqa: E402
import rev1_recompute as R  # noqa: E402

RESULT_D = os.path.join(L.NG, "result-d-one-division.md")
PREREG = os.path.join(L.SRC, "prereg")
FIFTEEN = "preregistration-fifteen-references.md"
# (folder, file, what it is), the folder named rather than guessed from the file name
DOCS = [(PREREG, FIFTEEN, "fifteen references"),
        (L.NG, "preregistration-twenty-four-scrolls.md", "twenty-four scrolls"),
        (L.NG, "note-twenty-seeds.md", "twenty seeds")]


def stated_date(path):
    """The date the document declares, off the line it declares it on.

    Anchored on a line that begins "Written on", and not on the first date in the file, so that
    a date quoted anywhere else in the document cannot be taken for the date it declares.
    """
    head = open(path).read(4000)
    m = re.search(r"^Written on (\d{4}-\d{2}-\d{2})(?:\s+at\s+(\d{2}:\d{2}(?::\d{2})?))?",
                  head, re.M)
    return (m.group(1) + ("T" + m.group(2) + "Z" if m.group(2) else "")) if m else ""


def main():
    text = open(RESULT_D).read()
    measured = sorted({m.group(1) for m in re.finditer(r"^\|\s*(PHerc\w+)\s*\|", text, re.M)})
    prim = [s for s in L.PRIMARY if s in measured]
    conf = [s for s in L.CONFIRM if s in measured]
    k20_seeds = int(L.read_csv(os.path.join(L.EV, "fifteen-k20.csv"))[0]["seeds"])
    rows = []
    for folder, name, what in DOCS:
        p = os.path.join(folder, name)
        rows.append(dict(document=name, what=what, stated_written=stated_date(p),
                         measured_before=os.path.basename(RESULT_D) if name == FIFTEEN else "",
                         primary_measured_before=len(prim) if name == FIFTEEN else "",
                         primary_measured_before_scrolls=" ".join(prim) if name == FIFTEEN else "",
                         primary_total=len(L.PRIMARY), confirm_measured_before=len(conf) if name == FIFTEEN else "",
                         confirm_total=len(L.CONFIRM),
                         seeds_per_slice=len(R.SEEDS) if name == "preregistration-twenty-four-scrolls.md"
                         else (k20_seeds if name == "note-twenty-seeds.md" else "")))
    for r in rows:
        print(f"  {r['document']:32s} written {r['stated_written']:20s} seeds {r['seeds_per_slice']}  "
              f"primary measured before {r['primary_measured_before']}", flush=True)
    L.write_csv(os.path.join(L.EV, "prereg-timeline.csv"), list(rows[0]), rows)


if __name__ == "__main__":
    main()
