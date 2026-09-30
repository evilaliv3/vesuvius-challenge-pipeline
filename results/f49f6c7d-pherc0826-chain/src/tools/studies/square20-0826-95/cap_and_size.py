#!/usr/bin/env python3
"""cap_and_size.py: PLAN item 95 (c), first step. New file, written 2026-09-28T12:4xZ by a coordinator agent.

For each source of chain-0826/evidence/wave5-sources.csv (the five seeds at 15 mm or more), reads, never writes:
  - chain-0826/log/growth-<seed>.txt: the highest N of the lines «Patch N had ... growth steps» (the growth's own count of
    generations; simpaper10 g 36000 runs generations 0 to 36000 and stops there), the number of such lines;
  - chain-0826/evidence/runs/<seed>.csv: growth_return_code, growth_wall_clock_seconds, growth_patches,
    growth_rel_csv_lines, growth_peak_vmhwm_kb, binary_sha256, binary_series, growth_zarr;
  - du -sB1M of chain-0826/out/<seed>/growth and out/<seed>/C40; df -B1G of /data.
Writes evidence/cap-check.csv (one row per seed: at_cap yes when the highest generation is 36000 or more, which is
the cap and not an ending by itself) and evidence/size.csv (the size row of a g 72000 regrowth: disk and memory taken
as twice the g 36000 values, the 1447 precedent larger-sheets-1447/evidence/larger-vs-36000.csv beside it).
"""
import csv, glob, os, re, subprocess

C = "/data/scrollagent/runs/rev1/chain-0826"
S = "/data/scrollagent/runs/rev1/square20-0826-95"
TOOL = "square20-0826-95/tools/cap_and_size.py"
CAP = 36000
PAT = re.compile(rb"^Patch (\d+) had \d+ growth steps", re.M)


def rows(p):
    L = [l for l in open(p, newline="") if not l.lstrip().startswith('"#')]
    return list(csv.DictReader(L))


def du_mb(p):
    if not os.path.exists(p):
        return 0
    return int(subprocess.check_output(["du", "-sB1M", p]).split()[0])


def main():
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    free = int(subprocess.check_output(["df", "-B1G", "--output=avail", "/data"]).split()[-1])
    src = [r for r in rows(os.path.join(C, "evidence/wave5-sources.csv")) if r["is_source"] == "yes"]
    src.sort(key=lambda r: -float(r["best_square_mm_min_step"]))
    cap, size = [], []
    for r in src:
        a = r["attempt"]
        b = open(os.path.join(C, "log/growth-%s.txt" % a), "rb").read()
        gens = [int(m) for m in PAT.findall(b)]
        run = {x["quantity"]: x["value"] for x in rows(os.path.join(C, "evidence/runs/%s.csv" % a))}
        hi = max(gens)
        cap.append([a, r["best_square_mm_min_step"], CAP, hi, len(gens), run["growth_return_code"],
                    "yes" if hi >= CAP else "no", run["growth_patches"], run["growth_rel_csv_lines"],
                    run["growth_wall_clock_seconds"], run["growth_peak_vmhwm_kb"], run["binary_series"],
                    run["binary_sha256"], run.get("growth_zarr", "not listed")])
        g, c40 = du_mb(os.path.join(C, "out", a, "growth")), du_mb(os.path.join(C, "out", a, "C40"))
        peak_gb = int(run["growth_peak_vmhwm_kb"]) / 1048576.0
        size.append([a, g, c40, 2 * (g + c40), round(peak_gb, 2), round(2 * peak_gb, 2),
                     2 * int(run["growth_wall_clock_seconds"])])
    lr = rows("/data/scrollagent/runs/rev1/larger-sheets-1447/evidence/larger-vs-36000.csv")
    prec = "; ".join("%s peak %s GB wall %s s patches %s square 36000 %s -> 72000 %s" % (
        x["attempt"], x["growth_peak_rss_gb"], x["growth_wall_clock_seconds"], x["growth_patches"],
        x["largest_square_mm_36000"], x["largest_square_mm_72000"]) for x in lr)
    with open(os.path.join(S, "evidence/cap-check.csv"), "w", newline="") as f:
        f.write('"# written by %s at %s: did each growth of the five seeds at 15 mm or more stop at the g %d cap or by itself; '
                'highest_generation is the largest N of «Patch N had» in chain-0826/log/growth-<seed>.txt"\n' % (TOOL, t, CAP))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["attempt", "best_square_mm_min_step", "cap_generations", "highest_generation", "patch_lines",
                    "growth_return_code", "at_cap", "growth_patches", "growth_rel_csv_lines", "growth_wall_clock_seconds",
                    "growth_peak_vmhwm_kb", "binary_series", "binary_sha256", "growth_zarr"])
        w.writerows(cap)
    tot_disk = sum(x[3] for x in size) / 1024.0
    with open(os.path.join(S, "evidence/size.csv"), "w", newline="") as f:
        f.write('"# written by %s at %s: size row of the g 72000 regrowths; estimates are twice the g 36000 values (disk: '
                'growth plus C40 of chain-0826/out; memory: VmHWM; time: wall clock); /data %d GB free (df -B1G); stop at 40 '
                'GB free; 1447 precedent at g 72000 (larger-sheets-1447/evidence/larger-vs-36000.csv, uncapped chunks): %s"\n'
                % (TOOL, t, free, prec))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["attempt", "growth_36000_mb", "c40_36000_mb", "disk_72000_estimate_mb", "peak_36000_gb",
                    "peak_72000_estimate_gb", "wall_72000_estimate_s"])
        w.writerows(size)
        w.writerow(["all five", sum(x[1] for x in size), sum(x[2] for x in size), sum(x[3] for x in size), "", "", ""])
        w.writerow(["data_free_gb_now", free, "", "", "", "", ""])
        w.writerow(["data_free_gb_after_estimate", round(free - tot_disk, 1), "", "", "", "", ""])
    for x in cap:
        print("%s best %s highest generation %d at_cap %s" % (x[0], x[1], x[3], x[6]))
    print("disk estimate %.1f GB for the five, /data %d GB free" % (tot_disk, free))


if __name__ == "__main__":
    main()
