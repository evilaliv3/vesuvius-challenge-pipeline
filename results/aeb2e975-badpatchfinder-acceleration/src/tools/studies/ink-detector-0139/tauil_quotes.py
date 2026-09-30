#!/usr/bin/env python3
"""Write src/evidence/studies/ink-detector-0139/tauil-quotes.csv: the words and numbers this work
quotes from TAUIL Abd Elilah's pherc1447-ink-survey, each checked verbatim against the README kept
in src/inputs/github-api/tauil-pherc1447-ink-survey/ (read from the GitHub API, anonymously, at the
time in fetched-utc.txt of that folder).

Written 2026-09-24 by an agent of the coordinator, on the director's order of 2026-09-24T18:24:03Z:
the headline of that survey is never quoted without its correction of 13 and 16 September, so both
are rows here and paper_numbers.py stops unless both are.

One row per quotation. `quoted` is the exact text the article prints; `value` is the number inside
it where the article prints the number alone, else the quoted text; `verbatim_in_readme` is yes
only when `quoted` occurs in the README exactly as written once its line breaks are read as spaces
and the «> » that opens each line of its blockquote is dropped (the correction is a blockquote and
its sentences wrap), and the tool exits non zero otherwise.
"""
import csv, hashlib, os, re, sys

S = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(S, "inputs", "github-api", "tauil-pherc1447-ink-survey")
OUT = os.path.join(S, "evidence", "studies", "ink-detector-0139", "tauil-quotes.csv")

# (quantity, quoted text, regex for the value inside it or None for the whole text)
QUOTES = [
    ("headline", "no legible ink in those four segments", None),
    ("segments_word", "no legible ink in those four segments", r"those (\w+) segments"),
    ("area_cm2_approx", "~42 cm² of real surface", r"~(\d+) cm"),
    ("best_window_score", "| PHerc1447 seg4 | **0.1407** |", r"\*\*([0-9.]+)\*\*"),
    ("control_median", "median 0.2382", r"median ([0-9.]+)"),
    ("correction_dates", "Correction (2026-09-13, updated 2026-09-16)", None),
    ("oblique_median", "Median 61.2°", None),
    ("half_off", "half off the scanned papyrus", None),
    ("correction", "it shows no ink was recovered from these surfaces, not that PHerc1447 lacks ink in those regions", None),
]


def main():
    readme = open(os.path.join(SRC, "README.md"), encoding="utf-8").read()
    sha = hashlib.sha256(readme.encode("utf-8")).hexdigest()
    flat = " ".join(re.sub(r"^>\s?", "", ln).strip() for ln in readme.splitlines())
    fetched = open(os.path.join(SRC, "fetched-utc.txt")).read().strip()
    rows, bad = [], 0
    for q, text, rx in QUOTES:
        ok = text in flat
        if rx is None:
            val = text
        else:
            m = re.search(rx, text)
            if not m:
                sys.exit("tauil_quotes.py: %s: no value in %r" % (q, text))
            val = m.group(1)
        if not ok:
            bad += 1
        rows.append([q, text, val, "yes" if ok else "no", sha, fetched])
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        fh.write("# by src/tools/studies/ink-detector-0139/tauil_quotes.py; quotations of "
                 "TAUIL-Abd-Elilah/pherc1447-ink-survey README.md (src/inputs/github-api/"
                 "tauil-pherc1447-ink-survey/), each checked verbatim\n")
        w = csv.writer(fh)
        w.writerow(["quantity", "quoted", "value", "verbatim_in_readme", "readme_sha256", "fetched_utc"])
        w.writerows(rows)
    print("wrote %s: %d quotation(s), %d not verbatim" % (OUT, len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
