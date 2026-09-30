#!/usr/bin/env python3
"""road1b_memory.py: the two stage c runs of road 1b, read from their logs, one row each.

Road 1b (the eight seed collection, one u tree of 52,906 patches) was stopped twice by its RSS bound
in simpaper10 stage c: log/road1b.txt (bound 40 GB) and log/road1b-c.txt (bound 70 GB, restarted at
stage c from the kept u tree). Closed by the director at 2026-09-28T15:50:25Z, not rerun.

Per run: the bound, the patches, the first sample of pass 3 (the first with 3 passes), the last
sample before the stop, and the stop line. GB is kB / 1e6, as the logs' bound compares.
Writes evidence/road1b-memory.csv.
"""
import csv, os, re

S = "/data/scrollagent/runs/rev1/area-0826-90"
OUT = os.path.join(S, "evidence", "road1b-memory.csv")
SAMPLE = re.compile(r"^(\S+Z) sample 'c': (\d+) s, .*bad patch lines (\d+), passes (\d+), .*rss (\d+) kB")
STOP = re.compile(r"^(\S+Z) RSS (\d+) kB above (\d+) GB in 'c'")
PATCHES = re.compile(r"patches (?:on disk )?(\d+)")


def secs(t):
    h, m, s = t[11:19].split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


rows = []
for run, log in (("first", "log/road1b.txt"), ("second", "log/road1b-c.txt")):
    lines = open(os.path.join(S, log)).read().splitlines()
    samples = [m.groups() for m in map(SAMPLE.match, lines) if m]
    stop = [m.groups() for m in map(STOP.match, lines) if m]
    if len(stop) != 1:
        raise SystemExit("%s: %d stop lines, want 1" % (log, len(stop)))
    t_stop, kb_stop, bound = stop[0]
    p = [int(x) for l in lines for x in PATCHES.findall(l)]
    p3 = [s for s in samples if s[3] == "3"]
    if not p3:
        raise SystemExit("%s: no sample in pass 3" % log)
    first3 = p3[0]
    rows.append({"tool": "tools/road1b_memory.py", "run": run, "log": log, "rss_bound_gb": bound,
                 "patches": p[0] if p else "",
                 "pass3_first_sample_utc": first3[0], "pass3_first_rss_gb": "%.1f" % (int(first3[4]) / 1e6),
                 "pass3_bad_patch_lines": first3[2],
                 "last_sample_utc": samples[-1][0], "last_sample_rss_gb": "%.1f" % (int(samples[-1][4]) / 1e6),
                 "stop_utc": t_stop, "stop_rss_gb": "%.1f" % (int(kb_stop) / 1e6),
                 "pass3_first_to_stop_min": "%.0f" % ((secs(t_stop) - secs(first3[0])) / 60),
                 "seconds_in_c_at_last_sample": samples[-1][1]})

with open(OUT, "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(open(OUT).read(), end="")
