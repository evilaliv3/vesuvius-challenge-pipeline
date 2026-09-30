#!/usr/bin/env python3
"""Figure C1: the chain on PHerc. 0826 drawn as boxes, each box the exact program and mode it runs.

Where each label comes from. The growth's mode and patch count and the five downstream stages with
their arguments are parsed from the chain's own runner, src/tools/studies/chain-0826/run_seed.sh
(the line `$BIN g <n>` and the line `for st in ...`), so the figure cannot name a stage the chain
does not run. The ladder cap is read from the header of chain-0826/ladder.csv. The line number of
each simpaper10 mode in Stevens' published source is read from src/evidence/derived/simpaper10-
lines.csv (mode_lines.py). The tool names of the seed steps are the shipped tools themselves, and
the box refuses to be drawn when its tool is not in src/tools/studies/.

The measured factor on each box (director 2026-09-28T18:29:38Z, owner's word: «the pipeline with the
measured factor on each box»). A factor is old median over new median of CPU seconds, computed here from
two rows this article already prints: arm A to B (the bad patch finder, stage c) and arm B to C (the
growth) of evidence/derived/arms-paired.csv, medians over the same seeds; the box says «outputs equal in
arms.csv» only when every output column of evidence/studies/stevens-changes-0826-91/arms.csv (sheets,
stevens_formula_cm2, largest_square_mm, a2_share, v2_cells, deaths) is equal in the two arms as written
(director 2026-09-28T21:22:13Z: equal columns, never byte identity);
and the zstd to LZ4HC copy of evidence/derived/speed-factors.csv (column factor, clock cpu). A box with
no measured factor says «not measured»; none is estimated. Stages run as published say so.

What it writes. src/evidence/figures/c-f1-pipeline.csv, one row per box and one per arrow, and
src/tools/c-f1-pipeline-body.tex, the TikZ nodes and arrows made from those rows, which
c-f1-pipeline.tex inputs. The ink reading is drawn dashed and marked experimental: nothing of it is
in this article.

Usage: c-f1-pipeline.py [--out PATH] [--tex PATH]
"""
import argparse, csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

FIGURE = "c-f1-pipeline"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--tex", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    tex = a.tex or os.path.join(here, "tools/%s-body.tex" % FIGURE)
    tools = os.path.join(here, "tools/studies")

    rs = open(os.path.join(tools, "chain-0826/run_seed.sh")).read()
    g = re.findall(r"^\s*\$BIN g (\d+) ", rs, re.M)
    st = re.findall(r'^for st in (.*); do', rs, re.M)
    if len(g) != 1 or len(st) != 1:
        sys.exit("run_seed.sh: %d growth lines and %d stage lines, expected one each" % (len(g), len(st)))
    stages = re.findall(r'"([^"]+)"', st[0])
    lad = open(os.path.join(here, "evidence/studies/chain-0826/ladder.csv")).readline()
    m = re.search(r"ladder cap of (\d+) s", lad)
    if not m:
        sys.exit("ladder.csv: no cap in the header")
    cap = m.group(1)
    _, _, lines = figlib.read_study_csv(os.path.join(here, "evidence/derived/simpaper10-lines.csv"))
    line = {r["key"]: r["line"] for r in lines}

    _, _, paired = figlib.read_study_csv(os.path.join(here, "evidence/derived/arms-paired.csv"))
    _, _, speed = figlib.read_study_csv(os.path.join(here, "evidence/derived/speed-factors.csv"))

    _, _, armrows = figlib.read_study_csv(os.path.join(here, "evidence/studies/stevens-changes-0826-91/arms.csv"))
    arm = {x["arm"]: x for x in armrows}
    OUTCOLS = ["sheets", "stevens_formula_cm2", "largest_square_mm", "a2_share", "v2_cells", "deaths"]

    def arm_factor(pair):
        r = [x for x in paired if x["pair"] == pair and x["measure"] == "cpu_seconds"]
        if len(r) != 1:
            sys.exit("arms-paired.csv: %d cpu rows for %s" % (len(r), pair))
        old, new = figlib.required_number(r[0], "old_median", pair), figlib.required_number(r[0], "new_median", pair)
        same = all(arm[pair[0]][c] == arm[pair[1]][c] for c in OUTCOLS)
        return ("CPU x%.2f, %s to %s, %s" % (old / new, pair[0], pair[1],
                                              "outputs equal in arms.csv" if same else "outputs differ in arms.csv"),
                "derived/arms-paired.csv %s cpu_seconds old_median over new_median (%s over %s); arms.csv %s %s"
                % (pair, r[0]["old_median"], r[0]["new_median"], " ".join(OUTCOLS), "all equal" if same else "not all equal"))

    def speed_factor(step):
        r = [x for x in speed if x["step"] == step and x["clock"] == "cpu"]
        if len(r) != 1:
            sys.exit("speed-factors.csv: %d cpu rows for %s" % (len(r), step))
        return ("CPU x%s, zstd to LZ4HC, same tree" % r[0]["factor"],
                "derived/speed-factors.csv %s cpu factor (%s)" % (step, r[0]["factor_is"]))

    NM = ("not measured", "none: no factor measured for this box")
    ASPUB = ("as published, not measured", "none: run as published, no factor measured")
    FACTOR = {"ct": NM, "m7": NM, "umb": NM, "draw": NM, "rule": NM, "near": NM, "ladder": NM,
              "lz": speed_factor("zstd copy to LZ4HC copy, MLP"), "g": arm_factor("BC"), "s0": arm_factor("AB"),
              "sq": NM, "a2": NM, "area": NM, "ink": ("", "none: not part of this article")}

    def shipped(t):
        hits = [r for r, _, fs in os.walk(tools) if os.path.basename(t) in fs]
        if not hits:
            sys.exit("box names %s, which is not shipped in src/tools/studies" % t)
        return t

    # Where each box sits (owner's remark of 2026-09-30: the arrows of the earlier order crossed). Column and row of a
    # 4 by 5 grid, read top to bottom as the flow runs: the inputs, the seed selection and the growth, Stevens' stages in
    # a loop down the right and back, and the measures with the ink reading at the bottom. With this order no two arrows
    # cross and no arrow passes over a box that is not one of its ends; the count is written into the figure's table.
    AT = {"m7": (0, 0), "ct": (1, 0), "umb": (2, 0), "lz": (3, 0),
          "draw": (0, 1), "rule": (1, 1), "near": (2, 1), "g": (3, 1),
          "s3": (1, 2), "ladder": (2, 2), "s0": (3, 2),
          "ink": (0, 3), "s4": (1, 3), "s2": (2, 3), "s1": (3, 3),
          "sq": (0, 4), "a2": (1, 4), "area": (2, 4)}
    # id, column, row, kind, first line, second line, source of the label
    B = [
        ("ct", 0, 0, "data", "CT scan, masked", "PHerc0826 20250821151701", "src/inputs/prize-eligibility"),
        ("m7", 1, 0, "data", "m7 surface prediction", "organisers' nnU-Net", "chain-0826/DECLARATION.md part 1"),
        ("lz", 2, 0, "data", "LZ4HC copy of m7", "read by the growth only", "hot-lines-88/identity-l-summary.csv"),
        ("umb", 3, 0, "external", "umbilicus", "published, not ours", "chain-0826/DECLARATION.md I6"),
        ("draw", 0, 1, "select", "seed draw", shipped("draw_seeds.py"), "chain-0826/tools/draw_seeds.py"),
        ("rule", 1, 1, "select", "seed rule v2", shipped("seed_rule_check_v2.py"), "chain-0826/tools/seed_rule_check_v2.py"),
        ("near", 2, 1, "select", "proximity draw", shipped("draw_near.py"), "chain-0826/tools/draw_near.py"),
        ("ladder", 3, 1, "select", "ladder", "simpaper10 g, %s s cap" % cap, "chain-0826/ladder.csv header"),
    ]
    B.append(("g", 0, 2, "growth", "simpaper10 g %s" % g[0], "MLP build, source line %s" % line["mode_g"], "run_seed.sh; simpaper10-lines.csv mode_g"))
    for i, s in enumerate(stages):
        key = "mode_" + s.split()[0]
        if key not in line:
            sys.exit("stage %s has no line in simpaper10-lines.csv" % s)
        FACTOR.setdefault("s%d" % i, ASPUB)
        B.append(("s%d" % i, 0, 0, "stage", "simpaper10 %s" % s, "source line %s" % line[key],
                  "run_seed.sh; simpaper10-lines.csv %s" % key))
    last = "s%d" % (len(stages) - 1)
    B += [
        ("sq", 0, 4, "measure", "largest square", shipped("square.py"), "seed-search-1447/tools/square.py"),
        ("a2", 1, 4, "measure", "a2 cluster rule", shipped("a2_cluster_seed.py"), "chain-0826/tools/a2_cluster_seed.py"),
        ("area", 2, 4, "measure", "clean area, formula", shipped("stevens_method.py"), "area-0826-90/tools/stevens_method.py"),
        ("ink", 3, 4, "experimental", "ink reading", "experimental, not here", "none"),
    ]
    E = [("m7", "draw"), ("draw", "rule"), ("ct", "rule"), ("umb", "rule"), ("rule", "near"), ("near", "ladder"),
         ("lz", "g"), ("ladder", "g"), ("g", "s0")]
    E += [("s%d" % i, "s%d" % (i + 1)) for i in range(len(stages) - 1)]
    E += [(last, "sq"), (last, "a2"), (last, "area"), (last, "ink")]
    if set(AT) != {b[0] for b in B}:
        sys.exit("layout and boxes differ: %s" % sorted(set(AT) ^ {b[0] for b in B}))
    B = [(b[0], AT[b[0]][0], AT[b[0]][1]) + tuple(b[3:]) for b in B]
    if len({(b[1], b[2]) for b in B}) != len(B):
        sys.exit("two boxes share a cell of the layout")
    ids = {b[0] for b in B}
    if set(FACTOR) != ids:
        sys.exit("boxes without a factor entry: %s" % sorted(ids ^ set(FACTOR)))
    for x, y in E:
        if x not in ids or y not in ids:
            sys.exit("arrow %s to %s names a box that is not drawn" % (x, y))

    # Arrow crossings, counted on the segments TikZ draws (each arrow lies on the line between its two box centres):
    # two arrows cross when their segments meet at a point that is not a box they share.
    DX, DY = 4.45, 1.75
    C = {b[0]: (b[1] * DX, -b[2] * DY) for b in B}

    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def cross(e, f):
        if len({e[0], e[1], f[0], f[1]}) < 4:
            return False
        p1, p2, p3, p4 = C[e[0]], C[e[1]], C[f[0]], C[f[1]]
        return orient(p3, p4, p1) * orient(p3, p4, p2) < 0 and orient(p1, p2, p3) * orient(p1, p2, p4) < 0
    ncross = {e: sum(cross(e, f) for f in E if f != e) for e in E}
    total = sum(ncross.values()) // 2

    rows = [{"kind": "box", "id": b[0], "col": b[1], "row": b[2], "style": b[3], "line1": b[4], "line2": b[5],
             "from": "", "to": "", "label_source": b[6],
             "factor": FACTOR[b[0]][0], "factor_source": FACTOR[b[0]][1], "crossings": ""} for b in B]
    rows += [{"kind": "arrow", "id": "%s-%s" % e, "col": "", "row": "", "style": "", "line1": "", "line2": "",
              "from": e[0], "to": e[1], "label_source": "", "factor": "", "factor_source": "", "crossings": ncross[e]} for e in E]
    rows.append({"kind": "count", "id": "arrow crossings", "col": "", "row": "", "style": "", "line1": "", "line2": "",
                 "from": "", "to": "", "label_source": "segment intersections between the arrows drawn", "factor": "",
                 "factor_source": "", "crossings": total})
    fields = ["kind", "id", "col", "row", "style", "line1", "line2", "from", "to", "label_source", "factor", "factor_source",
              "crossings"]
    comment = ("figure C1 (the pipeline), every box and arrow drawn and nothing else, written by src/tools/%s.py; "
               "growth and stages parsed from chain-0826/run_seed.sh, ladder cap from ladder.csv, source lines from "
               "derived/simpaper10-lines.csv at scrollreading 62cbc21; factor is old over new median CPU from derived/arms-paired.csv "
               "or derived/speed-factors.csv, or not measured; column crossings: how many other arrows each arrow crosses, and in the "
               "last row the arrow crossings of the whole figure, %d" % (FIGURE, total))
    figlib.write_plotted(out, comment, fields, rows)

    def t(s):
        return s.replace("_", r"\_").replace("%", r"\%")
    with open(tex, "w") as fh:
        fh.write("%% Generated by src/tools/c-f1-pipeline.py from evidence/figures/c-f1-pipeline.csv. Do not edit.\n")
        for b in B:
            f = FACTOR[b[0]][0]
            if f.startswith("CPU"):
                parts = [x.strip() for x in f.split(",")]
                f3 = "\\\\{\\scriptsize\\color{sablue}CPU $\\times$%s, %s}" % (parts[0].split("x", 1)[1], t(parts[1]))
                if len(parts) > 2:
                    f3 += "\\\\{\\scriptsize\\color{sablue}%s}" % t(", ".join(parts[2:]))
            elif f:
                f3 = "\\\\{\\scriptsize\\itshape\\color{sagrey} %s}" % t(f)
            else:
                f3 = ""
            fh.write("\\node[box, %s] (%s) at (%.2f,%.2f) {\\textbf{%s}\\\\{\\scriptsize %s}%s};\n"
                     % (b[3], b[0], b[1] * 4.45, -b[2] * 1.75, t(b[4]), t(b[5]), f3))
        for x, y in E:
            fh.write("\\draw[arr] (%s) -- (%s);\n" % (x, y))
    sys.stderr.write("%s: %d boxes, %d arrows, %d arrow crossings\n" % (out, len(B), len(E), total))


if __name__ == "__main__":
    main()
