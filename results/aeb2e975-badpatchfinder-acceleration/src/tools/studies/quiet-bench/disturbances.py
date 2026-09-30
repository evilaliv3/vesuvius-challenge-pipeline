#!/usr/bin/env python3
"""Every window in which something other than the bench was using this machine.

Two sources, and the file says which for every row:

  the bursts of the leftover throttle, read from evidence/throttle-bursts.csv, which
  tools/throttle_bursts.py takes out of another study's log;
  windows DECLARED here, because the thing that loaded the machine left no log of its own.
  The only one so far is this coordinator's own read back sweep: tools/read_back_draft.py
  walked the whole study tree again for every citation it could not resolve, which is minutes
  of a core, and the process was stopped by its group at 05:22:09Z. It is written down for the
  same reason the throttle is: a run timed under it is a run with something else on the
  machine, and the reader is entitled to know which rows those are.

A declared window carries what is known about it and no more. The sweep's load was NOT
constant across its window: most runs of that tool took under a second and two walked the
tree. The honest reading is the conservative one, that the whole window is disturbed, and the
row says so rather than inventing a profile.

Writes evidence/disturbances.csv, which tools/throttle_overlap.py joins onto the bench rows.
"""
import csv, os, sys
from datetime import datetime, timezone

Q = "/data/scrollagent/runs/rev1/quiet-bench"
BURSTS = os.path.join(Q, "evidence", "throttle-bursts.csv")
OUT = os.path.join(Q, "evidence", "disturbances.csv")

# Declared windows: (start, end, what, cores, how the two instants are known)
DECLARED = [
    ("2026-09-22T04:55:57Z", "2026-09-22T05:22:09Z",
     "the coordinator's read back sweep, tools/read_back_draft.py: it walked the study tree "
     "again for every citation it could not resolve",
     "up to one core, and NOT constant across the window: most runs of that tool took under a "
     "second and two walked the tree for minutes",
     "start is the mtime of the first report it wrote, "
     "$CLAUDE_JOB_DIR/tmp/readback-S.csv at 04:55:57Z; end is the kill of its process group, "
     "read from the ps that found the group gone at 05:22:09Z"),
]


def secs(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def read_after_comment(path):
    with open(path) as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith(('"#', '#')):
        i += 1
    return list(csv.DictReader(lines[i:]))


def main():
    rows = []
    if os.path.exists(BURSTS):
        for b in read_after_comment(BURSTS):
            rows.append({
                "start_utc": b["start_utc"],
                "end_utc": b["end_utc"],
                "seconds": b["wall_seconds"],
                "source": "evidence/throttle-bursts.csv",
                "what_it_was": "a relaunch of tools/mesh_throttle12.sh running grid_pipeline on "
                               "a grid whose cubes were all already done",
                "how_much_of_the_machine": "one core, grid_weld",
                "how_the_instants_are_known": b["how_the_end_was_determined"],
            })
    else:
        sys.exit("no %s: run tools/throttle_bursts.py first" % BURSTS)
    for start, end, what, cores, how in DECLARED:
        rows.append({
            "start_utc": start,
            "end_utc": end,
            "seconds": "%d" % round(secs(end) - secs(start)),
            "source": "declared in tools/disturbances.py",
            "what_it_was": what,
            "how_much_of_the_machine": cores,
            "how_the_instants_are_known": how,
        })
    rows.sort(key=lambda r: r["start_utc"])
    with open(OUT, "w", newline="") as fh:
        fh.write('"# every window in which something other than the quiet bench was using this '
                 'machine, written by tools/disturbances.py. Rows from '
                 'evidence/throttle-bursts.csv are read out of another study\'s log; rows whose '
                 'source is «declared» had no log of their own and are written down by hand, '
                 'with how each instant is known in its own column. %d rows, %d of them '
                 'declared. A bench row that overlaps any of these is named in '
                 'evidence/throttle-overlap.csv."\n' % (len(rows), len(DECLARED)))
        w = csv.writer(fh)
        w.writerow(list(rows[0].keys()))
        for r in rows:
            w.writerow(list(r.values()))
    print("wrote %s, %d windows (%d from the throttle log, %d declared)"
          % (OUT, len(rows), len(rows) - len(DECLARED), len(DECLARED)))


if __name__ == "__main__":
    main()
