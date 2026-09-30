#!/usr/bin/env python3
"""early-tangle: the rule taken to PHerc0139, per the dated addition of 2026-09-21T16:08:59Z.

For every growth on this disk with a log carrying `Patch <n> has <m> matches` and a growth tree
with a rel.csv beside it: the fan out, which settles the kind, and the share of the log's first
100,000 lines, which is the rule being tested. The kind is never decided by the rule.
"""
import csv
import glob
import os
import re

S = "/data/scrollagent/runs/rev1/early-tangle"
R = "/data/scrollagent/runs/rev1"
N = 100000
NM = "not measurable"
RIBBON_MAX_FAN_OUT = 10.0
RIBBON_BAND = (0.02825, 0.04275)
TANGLE_BAND = (0.12002, 0.15170)

# log, growth tree. Listed by hand from the study layouts and written here so the pairing is
# visible and checkable, not buried in a glob. A growth log sits beside the tree its growth wrote.
PAIRS = [
    ("growth-repeat/log/chain-growth-g.txt", "growth-repeat/out/growth"),
    ("reference-b40/log/chain-growth-g.txt", "reference-b40/out/growth"),
    ("seed-distance-ladder/log/growth-D150.txt", "seed-distance-ladder/out/growth-D150"),
    ("seed-distance-ladder/log/growth-D450.txt", "seed-distance-ladder/out/growth-D450"),
    ("why-the-growth-stops/log/growth-P.txt", "why-the-growth-stops/out/growth-P"),
    ("why-the-growth-stops/log/growth-P2.txt", "why-the-growth-stops/out/growth-P2"),
    ("why-the-growth-stops/log/growth-C.txt", "why-the-growth-stops/out/growth-C"),
    ("why-the-growth-stops/log/growth-S.txt", "why-the-growth-stops/out/growth-S"),
    ("held-patch/log/growth-A.txt", "held-patch/out/growth-A"),
    ("ceiling-24000/log/chain-growth-g.txt", "ceiling-24000/out/growth"),
]


def scroll_of(study):
    """The scroll a study declares, from its own DECLARATION.md, or not measurable."""
    p = os.path.join(R, study, "DECLARATION.md")
    if not os.path.exists(p):
        return NM
    found = sorted(set(re.findall(r"PHerc\d{4}", open(p, errors="replace").read())))
    return found[0] if len(found) == 1 else (NM if not found else " and ".join(found))


def fan_out(tree):
    rel = os.path.join(tree, "rel.csv")
    if not os.path.exists(rel):
        return None
    deg = {}
    n = 0
    with open(rel) as f:
        for line in f:
            i = line.find(",")
            j = line.find(",", i + 1)
            if i < 0 or j < 0:
                continue
            for k in (line[:i], line[i + 1:j]):
                deg[k] = 1
            n += 1
    return (n, len(deg), 2 * n / len(deg)) if deg else None


def share(log):
    if not os.path.exists(log):
        return None
    hits = total = 0
    with open(log, errors="replace") as f:
        for line in f:
            total += 1
            if total > N:
                break
            if line.startswith("Patch ") and line.rstrip().endswith(" matches"):
                hits += 1
    return (hits, total) if total >= N else None


def main():
    rows = []
    for rel_log, rel_tree in PAIRS:
        study = rel_log.split("/")[0]
        log, tree = os.path.join(R, rel_log), os.path.join(R, rel_tree)
        r = dict(study=study, scroll=scroll_of(study), log=rel_log, tree=rel_tree)
        f = fan_out(tree) if os.path.isdir(tree) else None
        s = share(log)
        if f is None:
            r.update(edges=NM, keys=NM, fan_out=NM, kind=NM)
        else:
            n, k, v = f
            r.update(edges=n, keys=k, fan_out="%.2f" % v,
                     kind="ribbon" if v < RIBBON_MAX_FAN_OUT else "tangle")
        if s is None:
            r.update(log_lines_at_least_n="no", share_of_first_100000=NM, verdict_of_the_rule=NM)
        else:
            hits, _t = s
            sh = hits / N
            r.update(log_lines_at_least_n="yes", share_of_first_100000="%.5f" % sh)
            if RIBBON_BAND[0] <= sh <= RIBBON_BAND[1]:
                r["verdict_of_the_rule"] = "ribbon"
            elif TANGLE_BAND[0] <= sh <= TANGLE_BAND[1]:
                r["verdict_of_the_rule"] = "tangle"
            else:
                r["verdict_of_the_rule"] = "outside both bands"
        r["rule_agrees_with_the_fan_out"] = (
            NM if NM in (r["kind"], r["verdict_of_the_rule"])
            else ("yes" if r["kind"] == r["verdict_of_the_rule"] else "no"))
        rows.append(r)
    note = (
        "# the rule of early-tangle taken off PHerc1447, per DECLARATION.md's dated addition of "
        "2026-09-21T16:08:59Z. kind is settled by fan_out, twice the edges over the keys of that "
        "growth's own rel.csv, with the cut at 10 that fell in an empty gap on PHerc1447; it is "
        "NEVER settled by the rule being tested. share_of_first_100000 is the rule's own reading "
        "of the growth log. verdict_of_the_rule applies the two bands fitted on PHerc1447, "
        "ribbon 0.02825 to 0.04275 and tangle 0.12002 to 0.15170, and says 'outside both bands' "
        "when the value falls in neither, which is itself a result. scroll is read from each "
        "study's own DECLARATION.md and is 'not measurable' when the file names none. A pairing "
        "with no tree or a log shorter than 100,000 lines is not measurable, never a pass.")
    out = os.path.join(S, "evidence", "other-scroll.csv")
    cols = ["study", "scroll", "edges", "keys", "fan_out", "kind", "log_lines_at_least_n",
            "share_of_first_100000", "verdict_of_the_rule", "rule_agrees_with_the_fan_out",
            "log", "tree"]
    with open(out, "w", newline="") as f:
        f.write('"%s"\n' % note)
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, NM) for c in cols})
    for r in rows:
        print("%-22s %-10s fan %7s %-14s share %9s -> %-19s agrees %s"
              % (r["study"], r["scroll"][:10], r["fan_out"], r["kind"],
                 r["share_of_first_100000"], r["verdict_of_the_rule"],
                 r["rule_agrees_with_the_fan_out"]))


if __name__ == "__main__":
    main()
