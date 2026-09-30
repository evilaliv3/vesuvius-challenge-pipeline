#!/usr/bin/env python3
"""For every row of the quiet bench, say whether a relaunch of the leftover throttle fell in
its window.

Why a file beside c-stage-runs.csv and not a column inside it: bench2.sh is running and
appends to that file. Rewriting it to widen the header would race with the append and could
lose a row, which is the same hazard as rewriting the ledger. This file is keyed on the four
fields that identify a bench row, so the two join, and it is rebuilt from scratch every time
it runs, so it covers rows the bench wrote after the throttle was stopped.

A bench row is marked yes when the closed interval of a burst
(evidence/throttle-bursts.csv, start_utc to end_utc) intersects the closed interval of the
run (started_utc to started_utc + seconds). A row with cap_bit=yes has a seconds that is a
lower bound, so its window is a lower bound too and the answer is marked as such.

Writes evidence/throttle-overlap.csv.
"""
import csv, os, sys
from datetime import datetime, timezone

STUDY = "/data/scrollagent/runs/rev1/quiet-bench"
RUNS = os.path.join(STUDY, "evidence", "c-stage-runs.csv")
BURSTS = os.path.join(STUDY, "evidence", "disturbances.csv")
OUT = os.path.join(STUDY, "evidence", "throttle-overlap.csv")


def secs(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def read_after_comment(path):
    """Skip the leading comment lines. c-stage-runs.csv writes its comment bare and
    throttle-bursts.csv writes it as a quoted field, so both openings are accepted."""
    with open(path) as fh:
        lines = fh.readlines()
    start = 0
    while start < len(lines) and lines[start].lstrip().startswith(('"#', '#')):
        start += 1
    return list(csv.DictReader(lines[start:]))


def main():
    for p in (RUNS, BURSTS):
        if not os.path.exists(p):
            sys.exit("missing %s" % p)
    bursts = []
    for b in read_after_comment(BURSTS):
        bursts.append((secs(b["start_utc"]), secs(b["end_utc"]), b["what_it_was"],
                       b["start_utc"], b["source"], b["how_much_of_the_machine"]))
    rows = []
    for r in read_after_comment(RUNS):
        t0 = secs(r["started_utc"])
        try:
            dur = float(r["seconds"])
        except ValueError:
            dur = 0.0
        t1 = t0 + dur
        hits = [b for b in bursts if b[0] <= t1 and b[1] >= t0]
        overlap = sum(max(0.0, min(t1, b[1]) - max(t0, b[0])) for b in hits)
        lower_bound = r.get("cap_bit", "") == "yes"
        if hits:
            answer = "yes"
        else:
            answer = "no"
        if lower_bound:
            answer += ", on a window that is a lower bound because this run was stopped at its cap"
        rows.append({
            "tag": r["tag"],
            "attempt": r["attempt"],
            "repeat_index": r["repeat_index"],
            "started_utc": r["started_utc"],
            "seconds": r["seconds"],
            "throttle_relaunch_in_window": answer,
            "bursts_in_window": " ".join(b[3] for b in hits),
            "burst_seconds_inside_the_window": "%.0f" % overlap,
            "burst_share_of_the_run": ("%.5f" % (overlap / dur)) if dur > 0 else "not computable",
            "what_the_burst_was_doing": " | ".join(sorted({b[2] for b in hits})),
            "which_source_declared_it": " | ".join(sorted({b[4] for b in hits})),
            "how_much_of_the_machine": " | ".join(sorted({b[5] for b in hits})),
        })
    with open(OUT, "w", newline="") as fh:
        fh.write('"# one row per row of evidence/c-stage-runs.csv, written by '
                 'tools/throttle_overlap.py, joined on tag, attempt, repeat_index and '
                 'started_utc. throttle_relaunch_in_window answers the only question asked of '
                 'it: did a relaunch of the leftover tools/mesh_throttle12.sh fall between the '
                 'start of this run and its end. burst_share_of_the_run is the burst seconds '
                 'inside the window over the run seconds, and it is a share of WALL CLOCK on a '
                 'run that had four threads, so the share of the machine the burst took is '
                 'smaller than this number by about four. This file is beside c-stage-runs.csv '
                 'and not inside it because bench2.sh was appending to that file when this was '
                 'written."\n')
        w = csv.writer(fh)
        w.writerow(list(rows[0].keys()))
        for r in rows:
            w.writerow(list(r.values()))
    n = sum(1 for r in rows if r["throttle_relaunch_in_window"].startswith("yes"))
    print("wrote %s, %d bench rows, %d with a relaunch in the window" % (OUT, len(rows), n))
    for r in rows:
        if r["throttle_relaunch_in_window"].startswith("yes"):
            print("  %s %s r%s started %s, %s s: bursts %s, %s s inside, share %s"
                  % (r["tag"], r["attempt"], r["repeat_index"], r["started_utc"],
                     r["seconds"], r["bursts_in_window"],
                     r["burst_seconds_inside_the_window"], r["burst_share_of_the_run"]))


if __name__ == "__main__":
    main()
