#!/usr/bin/env python3
"""Figure C18: our changes to Stevens' pipeline added in turn on PHerc. 0826 (item 91), as a step chart.

What it reads. evidence/studies/stevens-changes-0826-91/per-run.csv (one row per arm and seed; the rows of
arms A to D whose outcome is «completed») and evidence/studies/stevens-changes-0826-91/arms.csv (the
median of each arm, the numbers the article's table prints). Arm X, the chain as delivered, and arm E, the
seed selection, are not drawn: X was not run in this study and E grows nothing.

What it draws. Panel a: the CPU seconds of every seed in every arm, one thin line per seed, and the
arm medians as a thick step line; each step carries its factor, old median over new median, computed
here. Panel b: the output of the same runs, Stevens' formula per seed, one line per seed, with the
arm medians. Whether an arm's output is the same as the arm before is decided here, per seed and
per output column (growth_patches, sheets, stevens_formula_cm2, best_square_mm, a2_share, v2_cells,
clean_cm2): «same» only when every column of every shared seed is equal as written; the count of
seeds that agree is a row of the table. The figure marks A to C as equal on every output column of
per-run.csv (never byte identity: the sheets are not compared here) only when that count
is every seed; D is drawn in the colour of an outcome that differs.

What it writes. evidence/figures/c-f18-arms-steps.csv (one row per quantity drawn: key, panel, what,
source, value) and tools/c-f18-arms-steps-body.tex, the pgfplots body made from those rows, which
c-f18-arms-steps.tex inputs. No number is typed in either .tex.

Usage: c-f18-arms-steps.py [--out PATH] [--tex PATH]
"""
import argparse, math, os, statistics, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

FIGURE = "c-f18-arms-steps"
ARMS = ["A", "B", "C", "D"]
OUTPUT = ["growth_patches", "sheets", "stevens_formula_cm2", "best_square_mm", "a2_share", "v2_cells", "clean_cm2"]
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
ST = "stevens-changes-0826-91"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    tex = a.tex or os.path.join(here, "tools/%s-body.tex" % FIGURE)
    ev = os.path.join(here, "evidence/studies", ST)
    _, _, runs = figlib.read_study_csv(os.path.join(ev, "per-run.csv"))
    _, _, arms = figlib.read_study_csv(os.path.join(ev, "arms.csv"))
    arm = {r["arm"]: r for r in arms}
    by = {}
    for r in runs:
        if r["arm"] in ARMS and r["outcome"] == "completed":
            by.setdefault(r["attempt"], {})[r["arm"]] = r
    seeds = sorted(s for s, d in by.items() if all(x in d for x in ARMS))
    if not seeds:
        sys.exit("per-run.csv: no seed completed in all four arms")
    rows = []

    def put(key, panel, what, src, col, value):
        rows.append(dict(key=key, panel=panel, what=what, source_file=src, source_column=col, value=value))

    put("seeds", "a;b", "seeds completed in all of A B C D", ST + "/per-run.csv", "attempt; outcome completed", len(seeds))
    med = {}
    for x in ARMS:
        m = statistics.median(float(by[s][x]["cpu_seconds"]) for s in seeds)
        if "%.4f" % m != arm[x]["cpu_seconds"]:
            sys.exit("arm %s: median CPU over the shared seeds %.4f is not arms.csv's %s" % (x, m, arm[x]["cpu_seconds"]))
        med[x] = m
        put("cpu_median_%s" % x.lower(), "a", "arm %s median CPU s; equal to arms.csv" % x, ST + "/arms.csv", "cpu_seconds",
            arm[x]["cpu_seconds"])
        put("formula_median_%s" % x.lower(), "b", "arm %s median formula cm2" % x, ST + "/arms.csv", "stevens_formula_cm2",
            arm[x]["stevens_formula_cm2"])
        put("square_median_%s" % x.lower(), "b", "arm %s median best square mm" % x, ST + "/arms.csv", "largest_square_mm",
            arm[x]["largest_square_mm"])
    same = {}
    for p, q in (("A", "B"), ("B", "C"), ("C", "D")):
        n = sum(all(by[s][p][c] == by[s][q][c] for c in OUTPUT) for s in seeds)
        same[p + q] = n
        put("same_%s%s" % (p.lower(), q.lower()), "a;b", "seeds whose every output column is equal in %s and %s" % (p, q),
            ST + "/per-run.csv", " ".join(OUTPUT), n)
        put("factor_%s%s" % (p.lower(), q.lower()), "a", "CPU factor %s to %s; old median over new median" % (p, q),
            ST + "/arms.csv", "cpu_seconds", "%.2f" % (med[p] / med[q]))
    put("factor_ac", "a", "CPU factor A to C; old median over new median", ST + "/arms.csv", "cpu_seconds",
        "%.2f" % (med["A"] / med["C"]))
    identical_ac = same["AB"] == len(seeds) and same["BC"] == len(seeds)
    put("same_a_to_c", "a;b", "every seed equal on every output column of per-run.csv in A B and C", ST + "/per-run.csv", " ".join(OUTPUT),
        "yes" if identical_ac else "no")
    for s in seeds:
        for x in ARMS:
            put("", "a", "%s arm %s CPU s" % (s, x), ST + "/per-run.csv", "cpu_seconds", by[s][x]["cpu_seconds"])
            put("", "b", "%s arm %s formula cm2" % (s, x), ST + "/per-run.csv", "stevens_formula_cm2",
                by[s][x]["stevens_formula_cm2"])
    comment = ("figure C18, what the step chart drew, written by src/tools/%s.py: per seed CPU seconds and Stevens' "
               "formula of item 91's arms A to D from %s/per-run.csv (outcome completed) and the arm medians of "
               "%s/arms.csv; factors are old median over new median; «same» means every output column equal as written"
               % (FIGURE, ST, ST))
    figlib.write_plotted(out, comment, FIELDS, rows)

    # the body, from those rows only
    cpu = {s: [float(by[s][x]["cpu_seconds"]) for x in ARMS] for s in seeds}
    frm = {s: [float(by[s][x]["stevens_formula_cm2"]) for x in ARMS] for s in seeds}
    fm = [float(arm[x]["stevens_formula_cm2"]) for x in ARMS]
    sqm = [arm[x]["largest_square_mm"] for x in ARMS]
    L = ["%% Generated by src/tools/%s.py from evidence/figures/%s.csv. Do not edit." % (FIGURE, FIGURE)]
    lo = min(min(v) for v in cpu.values())
    hi = max(max(v) for v in cpu.values())
    L.append("\\nextgroupplot[ymode=log, ymin=%g, ymax=%g, xmin=-0.35, ylabel={CPU per seed (s)}, title={(a) time}]"
             % (10 ** math.floor(math.log10(lo)), 10 ** math.ceil(math.log10(hi))))
    for s in seeds:
        v = cpu[s]
        L.append("\\addplot[seedline] coordinates {(1,%g) (2,%g) (3,%g)};" % tuple(v[:3]))
        L.append("\\addplot[seedlineD] coordinates {(3,%g) (4,%g)};" % (v[2], v[3]))
    m = [med[x] for x in ARMS]
    L.append("\\addplot[stepours] coordinates {(0.65,%g) (1.5,%g) (1.5,%g) (2.5,%g) (2.5,%g) (3.35,%g)};"
             % (m[0], m[0], m[1], m[1], m[2], m[2]))
    L.append("\\addplot[stepD] coordinates {(3.35,%g) (3.5,%g) (3.5,%g) (4.35,%g)};" % (m[2], m[2], m[3], m[3]))
    L.append("\\addplot[medmark] coordinates {(1,%g) (2,%g) (3,%g)};" % tuple(m[:3]))
    L.append("\\addplot[medmarkD] coordinates {(4,%g)};" % m[3])
    L.append("\\node[factor, anchor=south] at (axis cs:1.5,%g) {$\\times$%.2f};" % (m[0] * 1.12, med["A"] / med["B"]))
    L.append("\\node[factor, anchor=west] at (axis cs:2.53,%g) {$\\times$%.2f};" % (math.sqrt(m[1] * m[2]), med["B"] / med["C"]))
    L.append("\\node[factorD, anchor=west] at (axis cs:3.53,%g) {$\\times$%.2f};" % (math.sqrt(m[2] * m[3]), med["C"] / med["D"]))
    L.append("\\draw[acbrace] (axis cs:0.6,%g) -- (axis cs:0.6,%g) node[midway, factor, anchor=east, align=right] "
             "{A to C\\\\$\\times$%.2f};" % (m[0], m[2], med["A"] / med["C"]))
    flo = min(min(v) for v in frm.values())
    fhi = max(max(v) for v in frm.values())
    L.append("\\nextgroupplot[ymode=log, ymin=%g, ymax=%g, ylabel={Stevens' formula per seed (cm$^2$)}, title={(b) output}]"
             % (10 ** math.floor(math.log10(flo)), 10 ** math.ceil(math.log10(fhi)) * 10))
    for s in seeds:
        v = frm[s]
        L.append("\\addplot[seedline] coordinates {(1,%g) (2,%g) (3,%g)};" % tuple(v[:3]))
        L.append("\\addplot[seedlineD] coordinates {(3,%g) (4,%g)};" % (v[2], v[3]))
    L.append("\\addplot[stepours] coordinates {(0.65,%g) (3.35,%g)};" % (fm[0], fm[2]) if fm[0] == fm[1] == fm[2] else
             "\\addplot[stepours] coordinates {(0.65,%g) (1.5,%g) (1.5,%g) (2.5,%g) (2.5,%g) (3.35,%g)};"
             % (fm[0], fm[0], fm[1], fm[1], fm[2], fm[2]))
    L.append("\\addplot[stepD] coordinates {(3.35,%g) (3.5,%g) (3.5,%g) (4.35,%g)};" % (fm[2], fm[2], fm[3], fm[3]))
    L.append("\\addplot[medmark] coordinates {(1,%g) (2,%g) (3,%g)};" % tuple(fm[:3]))
    L.append("\\addplot[medmarkD] coordinates {(4,%g)};" % fm[3])
    if identical_ac:
        L.append("\\node[samebox] at (axis cs:2,%g) {every output column of per-run.csv\\\\equal on %d of %d seeds\\\\median %s cm$^2$, square %s mm};"
                 % (10 ** math.ceil(math.log10(fhi)) * 9.3, len(seeds), len(seeds), arm["A"]["stevens_formula_cm2"], sqm[0]))
    L.append("\\node[diffbox, anchor=south] at (axis cs:2.9,%g) {output columns differ in D on %d of %d seeds\\\\median %s cm$^2$, square %s mm};"
             % (10 ** math.floor(math.log10(flo)) * 1.25, len(seeds) - same["CD"], len(seeds), arm["D"]["stevens_formula_cm2"], sqm[3]))
    with open(tex, "w") as fh:
        fh.write("\n".join(L) + "\n")
    sys.stderr.write("%s: %d seeds, %d rows\n" % (out, len(seeds), len(rows)))


if __name__ == "__main__":
    main()
