#!/usr/bin/env python3
"""Figure C2: Stevens' formula on every PHerc. 0826 growth run, and on the one run collections,
against his one run on PHerc. 1667.

What it reads. evidence/studies/area-0826-90/stevens-method-0826.csv, column sum_components_cm2 of
every row whose run is a seed (one growth run, its ten delivered sheets summed, overlaps between
sheets counted), and of the row «Stevens PHerc1667, one run, ten components (reference)»; the row
«all 10 sheets», column stevens_formula_cm2, of collection-four-6365.csv and of
collection-control-6365.csv. Each horizontal line of the figure is a column of the plotted table,
so the figure types no number.

The legend of the four seed line is the row fibre_coll_four_legend of evidence/derived/fibre-summary.csv
(tools/fibre_summary.py: whether the fibre test scored any piece of those four seeds), written into the column
collection_four_legend and read by the figure source (director 2026-09-29T04:22:11Z).

What it writes. evidence/figures/c-f3-stevens-formula.csv, one row per growth run in ascending
order of its sum, x the rank, with the reference and collection values repeated on every row, and
the check column `below_reference`, which says for that run whether it is below his one run.

Usage: c-f3-stevens-formula.py [--out PATH]
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

FIGURE = "c-f3-stevens-formula"


def only(rows, col, val, what):
    hit = [r for r in rows if r[col] == val]
    if len(hit) != 1:
        sys.exit("%s: %d rows with %s = %s" % (what, len(hit), col, val))
    return hit[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    A = os.path.join(here, "evidence/studies/area-0826-90")
    _, _, sm = figlib.read_study_csv(os.path.join(A, "stevens-method-0826.csv"))
    runs = [r for r in sm if r["run"].startswith("PHerc0826-seed")]
    ref = [r for r in sm if r["run"].startswith("Stevens PHerc1667")]
    if len(ref) != 1:
        sys.exit("stevens-method-0826.csv: %d reference rows" % len(ref))
    his = figlib.required_number(ref[0], "sum_components_cm2", "his run")
    _, _, four = figlib.read_study_csv(os.path.join(A, "collection-four-6365.csv"))
    _, _, ctrl = figlib.read_study_csv(os.path.join(A, "collection-control-6365.csv"))
    four_v = figlib.required_number(only(four, "sheet", "all 10 sheets", "four"), "stevens_formula_cm2", "four")
    ctrl_v = figlib.required_number(only(ctrl, "sheet", "all 10 sheets", "control"), "stevens_formula_cm2", "control")
    _, _, fs = figlib.read_study_csv(os.path.join(here, "evidence/derived/fibre-summary.csv"))
    leg = only(fs, "quantity", "fibre_coll_four_legend", "fibre-summary")["value"]
    vals = sorted(((figlib.required_number(r, "sum_components_cm2", r["run"]), r["run"]) for r in runs))
    fields = ["x", "run", "sum_components_cm2", "below_reference", "stevens_1667_cm2",
              "collection_four_cm2", "collection_control_cm2", "collection_four_legend", "source_file", "source_column"]
    table = []
    for i, (v, run) in enumerate(vals, 1):
        table.append({"x": i, "run": run, "sum_components_cm2": "%.4f" % v,
                      "below_reference": "yes" if v < his else "no",
                      "stevens_1667_cm2": "%.4f" % his, "collection_four_cm2": "%.4f" % four_v,
                      "collection_control_cm2": "%.4f" % ctrl_v,
                      "collection_four_legend": "{%s}" % leg,
                      "source_file": "area-0826-90/stevens-method-0826.csv; collection-four-6365.csv; collection-control-6365.csv",
                      "source_column": "sum_components_cm2; stevens_formula_cm2 of row all 10 sheets"})
    comment = ("figure C3, the numbers plotted and nothing else, written by src/tools/%s.py at %s: %d growth "
               "runs of stevens-method-0826.csv in ascending order of sum_components_cm2; runs below his one run: %d of %d"
               % (FIGURE, figlib.utc_now(), len(table), sum(r["below_reference"] == "yes" for r in table), len(table)))
    figlib.write_plotted(out, comment, fields, table)
    sys.stderr.write("%s: %d runs\n" % (out, len(table)))


if __name__ == "__main__":
    main()
