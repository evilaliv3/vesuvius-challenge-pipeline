#!/usr/bin/env python3
"""Read the two perf reports written by tools/perf_tables.sh and write them as CSV.

perf's own report is the source of every share here: this tool parses its lines and does not
recompute a percentage. A line of the report is `  12.34%  name`, and for the srcline sort the
name is `file:line`.

Usage: perf_to_csv.py <tag> <perf.data> <binary>
"""
import csv, os, re, sys

S = "/data/scrollagent/runs/rev1/c-stage-cost"


def rows(path):
    out = []
    with open(path, errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")
            m = re.match(r"^\s+([0-9.]+)%\s+(.*)$", line)
            if m:
                out.append((float(m.group(1)), m.group(2).strip()))
    return out


def main():
    tag, data, binary = sys.argv[1], sys.argv[2], sys.argv[3]
    out = os.path.join(S, "evidence", "profile-%s.csv" % tag)
    with open(out, "w", newline="") as fh:
        fh.write("# the profile of the c stage, as perf report prints it and not recomputed here. "
                 "sort is `symbol` for the share of the whole run that fell in one function and "
                 "`srcline` for the share that fell on one line of source. share_percent is "
                 "perf's own number, cycles:u sampled at 299 Hz over the whole stage. The binary "
                 "is the one named in the header row; it was built with -g and its .text section "
                 "is byte for byte that of the binary built without -g "
                 "(evidence/binaries.csv, column sha256_stripped, and the .text comparison in "
                 "OUTCOME.md).\n")
        w = csv.writer(fh)
        w.writerow(["tag", "sort", "rank", "share_percent", "what", "perf_data", "binary"])
        for sort, path in (("symbol", os.path.join(S, "log", "perf-symbols-%s.txt" % tag)),
                           ("srcline", os.path.join(S, "log", "perf-srclines-%s.txt" % tag))):
            for i, (pct, name) in enumerate(rows(path), 1):
                w.writerow([tag, sort, i, "%.2f" % pct, name, data, binary])
    print("written to %s" % out)
    for sort, path in (("symbol", os.path.join(S, "log", "perf-symbols-%s.txt" % tag)),
                       ("srcline", os.path.join(S, "log", "perf-srclines-%s.txt" % tag))):
        print("--- top by %s" % sort)
        for pct, name in rows(path)[:12]:
            print("  %6.2f%%  %s" % (pct, name))


if __name__ == "__main__":
    sys.exit(main())
