#!/usr/bin/env python3
"""cap_and_size_v2.py: PLAN item 95 (f), the next ten regrowths (DECLARATION.md addition on the certified square).
New file, written 2026-09-28T15:2xZ by a coordinator agent, from tools/cap_and_size.py. Ranks every chain-0826 seed by its
best measured square_mm_min_step (evidence/squares-<seed>.csv), leaves out the seeds already regrown here (evidence/
cap-check.csv), and walks down the ranking reading each growth's highest «Patch N had» generation: a seed at 36000 or more
is taken, a seed below is skipped and named (it ended by itself; a g 72000 regrowth would repeat it), until ten are taken.
Size: the kept size of this study's five regrowths now (du -sB1M of out/<seed>) and the growth/patches transient (the
largest growth/patches of the five at its end, read from runs-<seed>.csv growth_patches times the median patch file size
is not kept, so the transient is taken as the largest C80/patches du of the five), against df -B1G /data and the 40 GB stop.
Writes evidence/cap-check-next10.csv and evidence/size-next10.csv.
"""
import csv, glob, os, re, subprocess

C = "/data/scrollagent/runs/rev1/chain-0826"
S = "/data/scrollagent/runs/rev1/square20-0826-95"
TOOL = "square20-0826-95/tools/cap_and_size_v2.py"
PAT = re.compile(rb"^Patch (\d+) had \d+ growth steps", re.M)


def rows(p):
    if not os.path.exists(p):
        return []
    return list(csv.DictReader([l for l in open(p, newline="") if not l.lstrip('"').startswith("#")]))


def du(p):
    return int(subprocess.check_output(["du", "-sB1M", p]).split()[0]) if os.path.exists(p) else 0


def main():
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    done = {r["attempt"] for r in rows(S + "/evidence/cap-check.csv")}
    best = []
    for p in glob.glob(C + "/evidence/squares-PHerc0826-seed*.csv"):
        a = os.path.basename(p)[len("squares-"):-4]
        m = [r for r in rows(p) if r["status"] == "measured"]
        if m and a not in done:
            b = max(m, key=lambda r: float(r["square_mm_min_step"]))
            best.append((float(b["square_mm_min_step"]), a, b["sheet"]))
    best.sort(reverse=True)
    out, taken = [], 0
    for mm, a, sh in best:
        if taken >= 10:
            break
        lg = C + "/log/growth-%s.txt" % a
        run = {x["quantity"]: x["value"] for x in rows(C + "/evidence/runs/%s.csv" % a)}
        if not os.path.exists(lg):
            out.append([a, "%.4f" % mm, sh, "", "", run.get("growth_return_code", ""), "not measurable", "no", "growth log absent"])
            continue
        g = [int(x) for x in PAT.findall(open(lg, "rb").read())]
        hi = max(g) if g else -1
        cap = hi >= 36000
        take = cap and run.get("growth_return_code") == "0" and os.path.exists(C + "/scratch/bin-%s/%s/simpaper10" % (run.get("binary_series"), a))
        taken += 1 if take else 0
        out.append([a, "%.4f" % mm, sh, hi, len(g), run.get("growth_return_code", ""), "yes" if cap else "no",
                    "yes" if take else "no", "at the cap, regrown" if take else ("ended by itself: a regrowth would repeat it"
                                                                                  if not cap else "binary or rc missing")])
    with open(S + "/evidence/cap-check-next10.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: chain-0826 seeds by best g 36000 square after the five of cap-check.csv, walked down until '
                'ten at the g 36000 cap are taken"\n' % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["attempt", "best_square_mm_min_step", "best_sheet", "highest_generation", "patch_lines", "growth_return_code",
                    "at_cap", "regrow", "why"])
        w.writerows(out)
    five = [r["attempt"] for r in rows(S + "/evidence/cap-check.csv")]
    kept = [du(S + "/out/%s" % a) for a in five]
    trans = max(du(S + "/out/%s/C80/patches" % a) for a in five)
    per = max(kept) + trans
    free = int(subprocess.check_output(["df", "-B1G", "--output=avail", "/data"]).split()[-1])
    fit = max(0, int((free - 40) * 1024 // per))
    chain_q = sum(1 for l in open(C + "/evidence/queue.txt") if l.strip())
    with open(S + "/evidence/size-next10.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: size of the next g 72000 regrowths from the five done here (du -sB1M), /data by df -B1G, '
                'the stop at 40 GB free"\n' % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["quantity", "value", "what_it_is"])
        w.writerow(["kept_mb_of_the_five", ";".join(map(str, kept)), "du -sB1M of out/<seed> after growth/patches removal"])
        w.writerow(["transient_mb", trans, "largest C80/patches of the five: the growth/patches copy held until the measurement"])
        w.writerow(["per_seed_peak_mb", per, "largest kept plus transient"])
        w.writerow(["data_free_gb", free, "df -B1G /data now"])
        w.writerow(["regrowths_that_fit_above_40gb", fit, "floor((free - 40) GB / per seed peak), with nothing else writing"])
        w.writerow(["ten_need_gb", "%.1f" % (10 * max(kept) / 1024.0), "ten kept trees"])
        w.writerow(["chain_queue_lines", chain_q, "chain-0826/evidence/queue.txt lines; each delivered chain seed keeps about 1.3 GB (wave 4 size row)"])
    print("taken %d; per seed %d MB; free %d GB; fit %d" % (taken, per, free, fit))
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
