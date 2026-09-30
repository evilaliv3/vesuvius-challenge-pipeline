#!/usr/bin/env python3
"""Turn the armed grid log into one row per burst of the leftover throttle.

tools/mesh_throttle12.sh (pid 2876727, started 2026-09-21T02:07Z, stopped by group
between 2026-09-22T03:48:32Z and 03:49:32Z) relaunched tools/run_grid12_armed.sh whenever its target concurrency
changed, and each relaunch ran grid_pipeline on a grid that was already finished: 1728 cubes
all `skipped already-done`, then grid_weld, about 24 s on one core. Those bursts fell on a
machine the quiet bench was timing.

A burst opens on the `machine before` line and closes on the `grid_pipeline rc=` line that
follows it. When no rc line follows before the next `machine before`, the burst was killed by
the throttle's own `kill -- -$PG` at that next relaunch, so it closes there and the row says
so: those are the bursts that did real meshing work and are not 24 s.

Writes evidence/throttle-bursts.csv. Reads nothing else, writes nothing else.
"""
import csv, os, re, sys
from datetime import datetime, timezone

LOG = "/data/scrollagent/runs/rev1/scrollfiesta-grid-0139/log/grid-armed.txt"
OUT = "/data/scrollagent/runs/rev1/quiet-bench/evidence/throttle-bursts.csv"
# Upper bound of the instant the group was killed by this round: the throttle's last
# row in scrollfiesta-grid-0139/evidence/mesh-throttle.csv is 2026-09-22T03:48:32Z and it
# appended one row every 60 s, so it died at or before 03:49:32Z; ps read the group gone.
# No burst uses this constant today: every burst inside the bench closed on its own rc line.
THROTTLE_STOPPED = "2026-09-22T03:49:32Z"

T = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) ")
RC = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) grid_pipeline rc=(-?\d+) in (\d+) s")
BEFORE = re.compile(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ) machine before:")


def secs(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp()


def main():
    if not os.path.exists(LOG):
        sys.exit("no log at %s" % LOG)
    opens, closes = [], []
    with open(LOG) as fh:
        for n, line in enumerate(fh, 1):
            m = BEFORE.match(line)
            if m:
                opens.append((n, m.group(1)))
                continue
            m = RC.match(line)
            if m:
                closes.append((n, m.group(1), m.group(2), m.group(3)))
    rows = []
    for i, (ln, start) in enumerate(opens):
        next_open_line = opens[i + 1][0] if i + 1 < len(opens) else None
        hit = None
        for cl, ct, rc, rep in closes:
            if cl > ln and (next_open_line is None or cl < next_open_line):
                hit = (ct, rc, rep)
                break
        if hit:
            end, rc, reported = hit
            how = "closed by its own grid_pipeline rc line"
        elif next_open_line is not None:
            end, rc, reported = opens[i + 1][1], "", ""
            how = "no rc line: killed by the next relaunch, this end is that relaunch instant and is an upper bound"
        else:
            end, rc, reported = THROTTLE_STOPPED, "", ""
            how = "no rc line: still open when the throttle group was killed, this end is that kill"
        rows.append({
            "burst_index": i + 1,
            "start_utc": start,
            "end_utc": end,
            "wall_seconds": int(round(secs(end) - secs(start))),
            "grid_pipeline_return_code": rc,
            "seconds_reported_by_the_pipeline": reported,
            "how_the_end_was_determined": how,
            "log_line": ln,
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        fh.write('"# one row per burst of the leftover tools/mesh_throttle12.sh, read from '
                 'scrollfiesta-grid-0139/log/grid-armed.txt by tools/throttle_bursts.py. '
                 'start_utc is the machine before line of the relaunch, end_utc the '
                 'grid_pipeline rc line that closes it. A row whose '
                 'grid_pipeline_return_code is empty has no rc line: it was killed by the next '
                 'relaunch, so its end_utc and wall_seconds are UPPER BOUNDS, not a measured '
                 'duration. These bursts ran on one core (grid_weld) when every cube was '
                 'already done, and on up to max_conc cores when they were not."\n')
        w = csv.writer(fh)
        w.writerow(list(rows[0].keys()))
        for r in rows:
            w.writerow(list(r.values()))
    print("wrote %s, %d bursts" % (OUT, len(rows)))
    print("unclosed (upper bound rows): %d" % sum(1 for r in rows if not r["grid_pipeline_return_code"]))


if __name__ == "__main__":
    main()
