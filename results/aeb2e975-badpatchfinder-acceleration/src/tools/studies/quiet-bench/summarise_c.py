#!/usr/bin/env python3
"""The `c` stage of the quiet bench, summarised per arm and per seed, read back from
evidence/c-stage-runs.csv and from nowhere else.

Three files come out:

  evidence/c-stage-summary.csv   one row per arm per seed: how many runs finished, the smallest
                                 and the largest second, the spread as the largest minus the
                                 smallest and as a per cent of the smallest, the mean, and the
                                 range of cores busy at the start over those runs. A run stopped
                                 by its cap is NOT in these columns: it is counted in
                                 runs_stopped_by_the_cap and its bound is in lower_bound_seconds.
  evidence/a8-factor.csv         what performance/00002 is worth, per seed: the noA8 seconds
                                 over the plain seconds, on the runs that finished, and the
                                 bound where the cap bit. Never a number where there is a bound.
  evidence/c2-factor.csv         the same shape for the arm the pull request proposes, c2
                                 against plain.

Nothing is averaged across seeds and no superlative is written by this tool: the outcome computes
those over every row of these files.
"""
import csv, os, statistics

Q = "/data/scrollagent/runs/rev1/quiet-bench"
RUNS = os.path.join(Q, "evidence", "c-stage-runs.csv")


def rows():
    out = []
    with open(RUNS) as f:
        r = csv.reader(f)
        head = None
        for row in r:
            if not row or row[0].startswith("#"):
                continue
            if head is None:
                head = row
                continue
            if row[0] == "tag":
                continue
            out.append(dict(zip(head, row)))
    return out


def group(rs):
    g = {}
    for d in rs:
        g.setdefault((d["tag"], d["attempt"]), []).append(d)
    return g


def stats(ds):
    ok = [d for d in ds if d["return_code"] == "0" and d["cap_bit"] != "yes"]
    capped = [d for d in ds if d["cap_bit"] == "yes"]
    other = [d for d in ds if d not in ok and d not in capped]
    secs = sorted(float(d["seconds"]) for d in ok)
    busy = [float(d["cores_busy_at_start"]) for d in ok if d["cores_busy_at_start"]]
    return ok, capped, other, secs, busy


def main():
    rs = rows()
    g = group(rs)
    summ = []
    for (tag, att), ds in sorted(g.items()):
        ok, capped, other, secs, busy = stats(ds)
        if secs:
            lo, hi = secs[0], secs[-1]
            mean = statistics.fmean(secs)
            # A spread over one run is not zero, it is unmeasured. Writing 0.0 there put a
            # number in the column that says «these runs agree perfectly» on an arm that ran
            # once, and a reader comparing a difference against it would have compared it
            # against nothing.
            if len(secs) > 1:
                spread = hi - lo
                pct = 100.0 * spread / lo
            else:
                spread = pct = "not measurable, one run"
        else:
            lo = hi = spread = pct = mean = "not measurable"
        summ.append([tag, att, len(ds), len(ok), len(capped), len(other),
                     "%.1f" % lo if secs else lo,
                     "%.1f" % hi if secs else hi,
                     "%.1f" % spread if isinstance(spread, float) else spread,
                     "%.2f" % pct if isinstance(pct, float) else pct,
                     "%.1f" % mean if secs else mean,
                     "; ".join("%.1f" % float(d["seconds"]) for d in ok) or "none",
                     "%.2f" % min(busy) if busy else "not measurable",
                     "%.2f" % max(busy) if busy else "not measurable",
                     "; ".join("greater than %.1f s, stopped by the cap of %s s"
                               % (float(d["seconds"]), d["cap_seconds"]) for d in capped) or "",
                     "; ".join("rc=%s in %s s" % (d["return_code"], d["seconds"]) for d in other) or ""])
    out = os.path.join(Q, "evidence", "c-stage-summary.csv")
    with open(out, "w", newline="") as f:
        f.write("# one row per arm per seed of the quiet bench, read back from "
                "evidence/c-stage-runs.csv. seconds_min, seconds_max, spread and mean cover ONLY "
                "the runs that returned zero and were not stopped by a cap; a run stopped by its "
                "cap is counted in runs_stopped_by_the_cap and its bound is written in "
                "bounds_from_the_cap as a lower bound, never as a time. spread_pct is the spread "
                "over the smallest second, which is the quantity a difference has to beat to be "
                "called a difference. cores_busy_min and _max are over the same runs, from the "
                "one second /proc/stat reading each row carries.\n")
        w = csv.writer(f)
        w.writerow(["arm", "attempt", "runs_written", "runs_that_finished",
                    "runs_stopped_by_the_cap", "runs_that_did_neither",
                    "seconds_min", "seconds_max", "spread_seconds", "spread_pct", "seconds_mean",
                    "every_second_that_finished", "cores_busy_min", "cores_busy_max",
                    "bounds_from_the_cap", "the_other_runs"])
        for r in summ:
            w.writerow(r)
    print("wrote", out)

    idx = {(r[0], r[1]): r for r in summ}
    for arm, fname, what in (("noA8", "a8-factor.csv",
                              "performance/00002-selection-render-state-and-precomputed-normals"),
                             ("c2", "c2-factor.csv",
                              "corrections/00007, 00008 and 00009")):
        p = os.path.join(Q, "evidence", fname)
        with open(p, "w", newline="") as f:
            f.write("# what %s is worth on the c stage, per seed, read back from "
                    "evidence/c-stage-summary.csv. The factor is the arm without the change over "
                    "the arm with it, both from runs that finished on a quiet machine. Where the "
                    "arm without the change was stopped by its cap the factor column says `at "
                    "least` and the bound is the cap: a bound is never written as a time and "
                    "never as zero.\n" % what)
            w = csv.writer(f)
            w.writerow(["attempt", "baseline_arm", "baseline_seconds", "baseline_runs",
                        "other_arm", "other_seconds", "other_runs", "factor", "how_to_read_it"])
            for att in sorted({a for (t, a) in idx}):
                b = idx.get(("plain", att))
                o = idx.get((arm, att))
                if b is None or o is None:
                    continue
                bs = b[6]   # seconds_min of plain
                if o[4] != 0 and o[3] == 0:
                    bound = o[14]
                    w.writerow([att, "plain", bs, b[3], arm, "not measurable", o[3],
                                "at least %.2f" % (float(o[14].split()[2]) / float(bs))
                                if bs != "not measurable" else "not measurable",
                                "the %s run was stopped by its cap: %s" % (arm, bound)])
                elif bs == "not measurable" or o[6] == "not measurable":
                    w.writerow([att, "plain", bs, b[3], arm, o[6], o[3], "not measurable",
                                "one of the two arms has no finished run on this seed"])
                else:
                    # the honest comparison is smallest against smallest: both are the same
                    # quantity measured with the same spread and the smallest is the least
                    # disturbed run of each arm. The spread of each is in c-stage-summary.csv.
                    #
                    # Which way round: the factor is the arm WITHOUT the change over the arm
                    # WITH it, as this file's own header says. For noA8 the arm without the
                    # change is noA8 and the plain arm has it; for c2 it is the other way, the
                    # plain arm is the one without 00007 to 00009. Dividing the same way for
                    # both wrote 0.96 where the answer is 1.04, and 0.00 where it is 205.65.
                    without, with_ = (o[6], bs) if arm == "noA8" else (bs, o[6])
                    f_ = float(without) / float(with_)
                    w.writerow([att, "plain", bs, b[3], arm, o[6], o[3], "%.2f" % f_,
                                "smallest second of each arm, the arm without the change over "
                                "the arm with it (%s over %s here); the spread of each is in "
                                "c-stage-summary.csv, columns spread_seconds and spread_pct"
                                % (without, with_)])
        print("wrote", p)


if __name__ == "__main__":
    main()
