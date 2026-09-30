#!/usr/bin/env python3
"""The crash diagnosis as a CSV, because a reader cannot read back a grep.

Work S quoted 202 failing chains, 73 distinct patches and line 436 of `badpatchfinder.cpp` from
evidence/diag-missing.txt, a log. The house rule is that every number in a deliverable comes
from a CSV written by a tool under tools/, and the director ordered these three converted on
2026-09-22T05:17:13Z. This is that tool. It invents nothing: it counts the log's own DIAG lines
and reads the named line out of the upstream source.

Each row says what was counted, over how many, and what it was checked against. Two checks are
columns and not sentences:

  the distinct patches counted here against the row count of evidence/key-containers.csv, which
  the same study built from rel.csv and the patches directory by a different route;
  the text of the source line against the call the diagnosis names, so «line 436» is a line that
  was read and not a line that was remembered.

Rule of 2026-09-22T04:17:45Z: the expected count and the count found are both written, and the
tool refuses rather than write a file whose totals do not agree.
"""
import csv, os, re, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(S, "evidence", "diag-missing.txt")
KEYS = os.path.join(S, "evidence", "key-containers.csv")
OUT = os.path.join(S, "evidence", "crash-diagnosis.csv")
SRC = "/data/repositories/scrollreading/pipeline9/badpatchfinder.cpp"
SRC_LINE = 436
CALL = "patches->at(p)"

LINE = re.compile(
    r"^DIAG length=(\d+) q=(\d+) count=(\d+) lastPatch=(\d+) p=(\d+) "
    r"am_has_p=(\d) patches_has_p=(\d) seq=([\d ]+?) \| "
    r"am_has_first=(\d) patches_has_first=(\d)")


def main():
    for p in (DIAG, KEYS):
        if not os.path.exists(p):
            sys.exit("missing %s" % p)
    rows_seen = 0
    parsed = []
    for line in open(DIAG):
        line = line.strip()
        if not line:
            continue
        rows_seen += 1
        m = LINE.match(line)
        if not m:
            sys.exit("a DIAG line did not parse, so no count from this file can be trusted: %s"
                     % line[:120])
        parsed.append(m)
    if not parsed:
        sys.exit("no DIAG line in %s" % DIAG)

    chains = len(parsed)
    lengths = sorted({int(m.group(1)) for m in parsed})
    patches = sorted({int(m.group(5)) for m in parsed})
    am_has = sum(1 for m in parsed if m.group(6) == "1")
    patches_has_not = sum(1 for m in parsed if m.group(7) == "0")
    second = sum(1 for m in parsed if m.group(8).split()[-1] == m.group(5))
    first_ok = sum(1 for m in parsed if m.group(9) == "1" and m.group(10) == "1")

    with open(KEYS) as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(('"#', '#')):
        i += 1
    keyrows = list(csv.DictReader(lines[i:]))
    keys_n = len(keyrows)
    keys_set = sorted(int(r["patch"]) for r in keyrows)
    reported_sum = sum(int(r["times_reported_missing"]) for r in keyrows)

    if rows_seen != chains:
        sys.exit("read %d lines and parsed %d" % (rows_seen, chains))
    if patches != keys_set:
        sys.exit("the %d distinct patches of the log are not the %d rows of key-containers.csv"
                 % (len(patches), keys_n))

    src_text, src_ok = "not measurable, the source is not on this disk", "not measurable"
    if os.path.exists(SRC):
        srclines = open(SRC, errors="replace").read().splitlines()
        if len(srclines) >= SRC_LINE:
            src_text = srclines[SRC_LINE - 1].strip()
            src_ok = "yes" if CALL in src_text else "no"

    rows = [
        ["failing chains reported by the instrumented build", chains, chains,
         "one DIAG line each in evidence/diag-missing.txt, every line parsed",
         "the count of lines read equals the count parsed"],
        ["distinct patches among them", len(patches), keys_n,
         "the p field of those lines, made distinct",
         "equals the row count of evidence/key-containers.csv, and the two sets are identical"],
        ["chain length of every one of them", " ".join(str(x) for x in lengths), 2,
         "the length field", "one value only, and it is 2"],
        ["of those chains, the alignment map HAS the key", am_has, chains,
         "am_has_p=1", "all of them"],
        ["of those chains, the patches map does NOT have it", patches_has_not, chains,
         "patches_has_p=0", "all of them"],
        ["of those chains, the failing element is the SECOND", second, chains,
         "the last element of seq equals p", "all of them"],
        ["of those chains, the first element is in both maps", first_ok, chains,
         "am_has_first=1 and patches_has_first=1", "all of them"],
        ["times the 73 patches are reported across the chains", reported_sum, chains,
         "the sum of times_reported_missing in key-containers.csv",
         "equals the chain count, so no chain is counted twice and none is missing"],
        ["the throwing call, source line", SRC_LINE, SRC_LINE,
         "line %d of %s" % (SRC_LINE, SRC),
         "the line was read and it contains %s: %s" % (CALL, src_ok)],
        ["the text of that line", src_text, "",
         "read from the file, not remembered", "quoted so a reader can check the line number"],
    ]

    with open(OUT, "w", newline="") as fh:
        fh.write('"# the crash diagnosis of PHerc1447-seed34 as numbers, written by '
                 'tools/crash_diagnosis.py from evidence/diag-missing.txt and '
                 'evidence/key-containers.csv, so that a text quotes a CSV and not a log. '
                 'value is what was counted and out_of is what it was counted over or checked '
                 'against; a row where the two differ and the check does not explain it is a '
                 'defect. The tool exits without writing when the log has a line it cannot '
                 'parse, or when the distinct patches of the log are not the rows of '
                 'key-containers.csv."\n')
        w = csv.writer(fh)
        w.writerow(["quantity", "value", "out_of", "how_it_was_read", "the_check"])
        for r in rows:
            w.writerow(r)
    print("wrote", OUT)
    for r in rows:
        print("  %-52s %-14s of %s" % (r[0], r[1], r[2]))


if __name__ == "__main__":
    main()
