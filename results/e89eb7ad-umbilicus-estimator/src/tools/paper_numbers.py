#!/usr/bin/env python3
"""Write src/paper/numbers.tex from src/evidence for the umbilicus estimator work.

The house shape, as in the other works of results/: every macro here is one cell of a file in
src/evidence, a missing cell stops the tool with the file and the row named and is never a
default, and the tool says how many macros it expected and how many it wrote.

Three blocks.

  SecRef...  the nineteen macros of the second reference of PHerc1218, from
             evidence/second-reference.csv. This is the typesetting half that lived as
             paper/00001/tools/second_reference_numbers.py of the laboratory, moved here with its
             table unchanged; the file it writes defines, line for line, the macros that file
             defined for the article of 2026-09-19.
  Up...      pull request 1823, which carries the line of the article and was merged, from
             evidence/upstream-status.csv, which tools/upstream_status.py writes from the clone.
  UpSquash.. what the merged squash touches, from evidence/merged-patch.csv.
  Now...     the same pull request read again from the GitHub API on 2026-09-28, for the
             introduction, from evidence/upstream-status-2026-09-28.csv, written by
             tools/upstream_status.py version 3 with --merged-at.

Not here, and why. The Umb... macros (paper/umbilicus-numbers.tex) were written by the frozen
run's make_numbers.py, which no longer exists, and the Rev... macros and the generated table rows
(paper/rev1-numbers.tex, paper/rev1-*.tex) by paper/00001/tools/rev1_numbers.py, which also read
the tip of the upstream clone and the fork. Its copy src/paper/rev1_numbers.py has those commits
pinned since 2026-09-23 and says why the carried rev1-numbers.tex still stays carried. Both files
are carried as they were built on 2026-09-19, byte for byte.

    python3 src/tools/paper_numbers.py
"""
import csv
import re
import datetime
import os
import sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence")
OUT = os.path.join(S, "paper", "numbers.tex")

ORDINAL = ["", "smallest", "second smallest", "third smallest", "fourth smallest",
           "fifth smallest"]
WORDS = ["none", "one", "two", "three", "four", "five"]

# macro name, the quantity whose row carries it, which column of the row, how it is printed.
SECREF = [
    ("SecRefScrolls",               "scrolls with a derived second reference",            "value", "int"),
    ("SecRefHandScrolls",           "scrolls with a hand umbilicus",                      "value", "int"),
    ("SecRefChallengeHands",        "hand umbilici published by the challenge",           "value", "int"),
    ("SecRefThirdPartyHands",       "hand umbilici clicked by the third party",           "value", "int"),
    ("SecRefMinMm",                 "smallest distance mm",                               "value", "3f"),
    ("SecRefMinScroll",             "smallest distance mm",                               "note",  "str"),
    ("SecRefMaxMm",                 "largest distance mm",                                "value", "3f"),
    ("SecRefMaxScroll",             "largest distance mm",                                "note",  "str"),
    ("SecRefMedianMm",              "median distance mm",                                 "value", "3f"),
    ("SecRefQOneMm",                "first quartile mm",                                  "value", "3f"),
    ("SecRefQThreeMm",              "third quartile mm",                                  "value", "3f"),
    ("SecRefRatio",                 "largest over smallest",                              "value", "1f"),
    ("SecRefRankWord",              "rank of PHerc1218 ascending",                        "value", "ord"),
    ("SecRefAboveSpread",           "scrolls above the published number",                 "value", "int"),
    ("SecRefPearson",               "Pearson against the centroid baseline",              "value", "4f"),
    ("SecRefGapMedianMm",           "median difference against the centroid baseline mm", "value", "2f"),
    ("SecRefGapMaxMm",              "largest difference against the centroid baseline mm", "value", "2f"),
    ("SecRefGapScrollMm",           "difference on PHerc1218 mm",                         "value", "2f"),
    ("SecRefPublishedVsCentroidMm", "published number against the centroid column mm",    "value", "2f"),
]

PATCH_PR = 1823


def read(name):
    p = os.path.join(EV, name)
    if not os.path.exists(p):
        sys.exit("paper_numbers.py: no %s" % p)
    with open(p, newline="") as fh:
        return list(csv.DictReader(fh))


def cell(row, col, what):
    if col not in row or row[col] == "":
        sys.exit("paper_numbers.py: %s has no cell in column %s" % (what, col))
    return row[col]


def long_date(iso):
    d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


def utc_time(iso):
    d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(datetime.timezone.utc)
    return d.strftime("%H:%M:%S") + " UTC"


def main():
    M = []

    rows = {r["quantity"]: r for r in read("second-reference.csv")}
    for name, quantity, column, how in SECREF:
        if quantity not in rows:
            sys.exit("paper_numbers.py: second-reference.csv has no row %r, which %s is built from"
                     % (quantity, name))
        raw = cell(rows[quantity], column, "second-reference.csv row %r" % quantity)
        if how == "str":
            v = raw
        elif how == "int":
            v = str(int(raw))
        elif how == "ord":
            v = ORDINAL[int(raw)]
        else:
            v = "%.*f" % (int(how[0]), float(raw))
        M.append((name, v))

    # Pull request PATCH_PR carries the line of this article. It was merged; the build stops
    # unless both files still say so. The author's other pull requests to villa were closed
    # without merge and the article no longer names them (lean pass of 2026-09-30, the owner's
    # word: only upstream items of ours that are open or merged are cited).
    up = {int(r["pr"]): r for r in read("upstream-status.csv")}
    if PATCH_PR not in up:
        sys.exit("paper_numbers.py: upstream-status.csv has no row for pull request %d" % PATCH_PR)
    p = up[PATCH_PR]
    if cell(p, "in_main", "upstream-status.csv, %d" % PATCH_PR) != "yes":
        sys.exit("paper_numbers.py: pull request %d is not in the main branch by upstream-status.csv; "
                 "the article says it is merged and must not be built" % PATCH_PR)
    sq = cell(p, "squash_commit", "upstream-status.csv, %d" % PATCH_PR)
    M += [("UpPatchPR", str(PATCH_PR)),
          ("UpPatchSquashShort", sq[:9]),
          ("UpPatchMergedLong", long_date(cell(p, "squash_committed", "upstream-status.csv, %d" % PATCH_PR))),
          ("UpPatchFilesSame", cell(p, "squash_files_same_as_head", "upstream-status.csv, %d" % PATCH_PR)),
          ("UpMainTipShort", p["main_tip"][:9]),
          ("UpMainTipLong", long_date(cell(p, "main_tip_committed", "upstream-status.csv, %d" % PATCH_PR)))]

    # The same pull request read again from the GitHub API on 2026-09-28,
    # evidence/upstream-status-2026-09-28.csv (upstream_status.py version 3, with merged_at). The
    # reading time printed is the Date header of the answer, as state_source records it.
    NOW = "upstream-status-2026-09-28.csv"
    now = {int(r["pr"]): r for r in read(NOW)}
    if PATCH_PR not in now:
        sys.exit("paper_numbers.py: %s has no row for pull request %d" % (NOW, PATCH_PR))
    ncols = [c for c in now[PATCH_PR] if c.startswith("state_as_of_")]
    if len(ncols) != 1:
        sys.exit("paper_numbers.py: %s has %d state_as_of_ columns, not one" % (NOW, len(ncols)))
    got = (cell(now[PATCH_PR], ncols[0], "%s, %d" % (NOW, PATCH_PR)),
           cell(now[PATCH_PR], "merged", "%s, %d" % (NOW, PATCH_PR)))
    if got != ("merged", "yes"):
        sys.exit("paper_numbers.py: pull request %d is %s by %s, and the article says merged"
                 % (PATCH_PR, got, NOW))
    if cell(now[PATCH_PR], "api_head_same_as_clone", "%s, %d" % (NOW, PATCH_PR)) != "yes":
        sys.exit("paper_numbers.py: the API and the clone name different heads for %d in %s" % (PATCH_PR, NOW))
    merged_at = cell(now[PATCH_PR], "merged_at", "%s, %d" % (NOW, PATCH_PR))
    m = re.search(r"answered (\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)",
                  cell(now[PATCH_PR], "state_source", "%s, %d" % (NOW, PATCH_PR)))
    if not m:
        sys.exit("paper_numbers.py: %s gives no answer time for %d" % (NOW, PATCH_PR))
    M += [("NowReadLong", long_date(m.group(1))),
          ("NowReadTime", utc_time(m.group(1))),
          ("NowPatchMergedLong", long_date(merged_at)),
          ("NowPatchMergedTime", utc_time(merged_at))]

    # What the squash of PATCH_PR touches, from evidence/merged-patch.csv (tools/merged_patch.py,
    # 2026-09-30, the referee's finding 4), checked against the squash named above.
    mp = read("merged-patch.csv")
    if not mp or any(r["squash_commit"] != sq for r in mp):
        sys.exit("paper_numbers.py: merged-patch.csv is not the squash %s of upstream-status.csv" % sq[:9])
    M += [("UpSquashFiles", str(sum(r["kind"] == "file" for r in mp))),
          ("UpSquashTestCases", str(sum(r["kind"] == "test_case_added" for r in mp)))]

    expected = len(SECREF) + 6 + 4 + 2
    with open(OUT, "w") as fh:
        fh.write("%% Generated by src/tools/paper_numbers.py from src/evidence. Do not edit.\n")
        for name, v in M:
            fh.write("\\newcommand{\\%s}{%s\\xspace}\n" % (name, v))
    print("paper_numbers.py: wrote %s, %d macros of %d expected" % (OUT, len(M), expected))
    return 0 if len(M) == expected else 1


if __name__ == "__main__":
    sys.exit(main())
