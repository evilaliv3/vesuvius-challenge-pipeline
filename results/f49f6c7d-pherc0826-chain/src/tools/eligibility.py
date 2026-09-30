#!/usr/bin/env python3
"""Whether PHerc. 0826 is eligible, read from the organisers' raw prizeEligibility.json.

The list is read from the raw JSON of the villa repository (scrollprize.org/src/data), saved on
2026-09-27 with the commit it was read at, and never from a summary of the prizes page: a summary
once put a scroll in the wrong list. One row per list: how many scrolls it names, whether PHerc0826
is one of them, and the volume the list pairs with it.

Usage: eligibility.py [--out PATH]
"""
import argparse, csv, glob, json, os, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(S, "inputs", "prize-eligibility")
SCROLL = "PHerc0826"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "eligibility.csv"))
    a = ap.parse_args()
    files = glob.glob(os.path.join(IN, "prizeEligibility-*.json"))
    if len(files) != 1:
        sys.exit("eligibility.py: %d prizeEligibility files in %s" % (len(files), IN))
    lists = json.load(open(files[0]))
    commit = json.load(open(glob.glob(os.path.join(IN, "main-commit-*.json"))[0]))
    read_at = open(os.path.join(IN, "read-at.txt")).read().strip()
    rows = []
    for name, items in lists.items():
        hit = [x for x in items if x["scroll"] == SCROLL]
        rows.append({"list": name, "scrolls": len(items), "pherc0826_listed": "yes" if hit else "no",
                     "pherc0826_volume": hit[0]["volume"] if hit else "not listed",
                     "commit": commit["sha"], "commit_date": commit["commit"]["committer"]["date"][:10],
                     "read_at": read_at, "source": os.path.basename(files[0])})
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/eligibility.py at %s from src/inputs/prize-eligibility, the raw '
                 'prizeEligibility.json of the villa repository at the commit named in each row"\n' % now)
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print("eligibility.py: %s, %d scrolls, PHerc0826 %s (%s)" % (r["list"], r["scrolls"], r["pherc0826_listed"], r["pherc0826_volume"]))


if __name__ == "__main__":
    main()
