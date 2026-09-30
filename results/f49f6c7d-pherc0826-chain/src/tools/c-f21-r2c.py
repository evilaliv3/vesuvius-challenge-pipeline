#!/usr/bin/env python3
"""Figure C21: the headline surface: panel (a) its certified square, panels (b) and (c) the square that passed the checks against our sheets before crossings between traced surfaces were adjudicated,
drawn by render-routes-0826's own figure tool and, since 2026-09-30, redrawn in this work by src/tools/c-f21-fig-r2c.py
(that tool taken from the study's, panel (b) without the height of the cut: locations withheld, the owner's decision).

RAW SCAN, NO INK DETECTOR. The figure is paper/figures/assets/r2c-seed6273-squarecentre.pdf, written by c-f21-fig-r2c.py
from the data of the study's fig_r2c.py (shipped under tools/studies/render-routes-0826): (a) the raw scan over the square regridded by
best-windows-0826's align.py (height up, arc length across); (b) an axial cut at the square's centre height with
the tracer surface and our certified sheet; (c) the straightened sections along the square's two centre lines. It is used on
the director's order of 2026-09-29T15:38:23Z (owner's word).

What this tool does, every step checked. The PDF, its PNG, its data table and c-f21-fig-r2c.py itself must have the sha256 pinned in
c-f21-r2c-pins.csv (a redrawn figure stops this tool rather than enter the article unseen). The figure's data table must
agree with this work's snapshot of square-checks.csv (route R2cnative, the same surface): the square within half of its
last printed digit, the section medians and shares and the share of nodes on our sheet exactly. Then the PDF is copied to
paper/figures/c-f21-r2c.pdf and the PNG beside it, and the plotted table evidence/figures/c-f21-r2c.csv is written with the
caption's keys. With --out elsewhere than the default, nothing is copied and only the table is written there.

Usage: c-f21-r2c.py [--out CSV] [--png PNG]
"""
import argparse
import csv
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402
import rasterlib as RL  # noqa: E402

FIGURE = "c-f21-r2c"
# Since 2026-09-30 (the owner's decision: no locations on the scroll) the figure is redrawn inside this work by
# src/tools/c-f21-fig-r2c.py, taken from the study's fig_r2c.py, with panel (b) untitled by its height; its files are
# under paper/figures/assets and pinned in c-f21-r2c-pins.csv with the drawing tool itself.
AF = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paper/figures/assets")
DRAW = "c-f21-fig-r2c.py"
STEM = "r2c-seed6273-squarecentre"
SURFACE = "PHerc0826-seed6273-squarecentre"
FIELDS = ["key", "panel", "what", "source_file", "source_column", "value"]
PIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), FIGURE + "-pins.csv")


def rd(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=None)
    ap.add_argument("--png", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_out = os.path.join(here, "evidence/figures/%s.csv" % FIGURE)
    out = os.path.abspath(a.out or default_out)
    shipped = out == os.path.abspath(default_out)
    rows = []

    def put(panel, what, source_file, source_column, value, key=""):
        rows.append(dict(key=key, panel=panel, what=what, source_file=source_file, source_column=source_column, value=value))

    pins = {r["file"]: r["sha256"] for r in rd(PIN_FILE)}
    for f in (STEM + ".pdf", STEM + ".png", STEM + "-data.csv", DRAW):
        h = RL.sha256(os.path.join(os.path.dirname(os.path.abspath(__file__)), f) if f == DRAW else os.path.join(AF, f))
        if pins.get(f) != h:
            raise SystemExit("%s: sha256 %s is not the pinned %s; the figure was redrawn after this article took it" % (f, h, pins.get(f)))
        put("a;b;c", "%s sha256 (pinned)" % f, ("src/tools/" if f == DRAW else "paper/figures/assets/") + f, "", h)
    d = rd(os.path.join(AF, STEM + "-data.csv"))
    if len(d) != 1 or d[0]["surface"] != SURFACE:
        raise SystemExit("the figure's data table is not one row of %s" % SURFACE)
    d = d[0]
    sq = [r for r in rd(os.path.join(here, "evidence/studies/render-routes-0826/square-checks.csv"))
          if r["route"] == "R2cnative" and r["surface"] == SURFACE]
    if len(sq) != 1:
        raise SystemExit("square-checks.csv: %d R2cnative rows of %s" % (len(sq), SURFACE))
    sq = sq[0]
    src = "render-routes-0826/square-checks.csv"
    if abs(float(d["square_mm"]) - float(sq["square_mm"])) > 5e-4:
        raise SystemExit("figure square %s is not square-checks' %s" % (d["square_mm"], sq["square_mm"]))
    for fc, sc in (("section_i_median_vox", "section_i_peak_offset_median_vox"), ("section_i_within3", "section_i_share_within_3_vox"),
                   ("section_j_median_vox", "section_j_peak_offset_median_vox"), ("section_j_within3", "section_j_share_within_3_vox"),
                   ("our_sheet_within3_share", "within3_share_all_cells"), ("our_sheet", "within3_best_sheet")):
        if d[fc] != sq[sc]:
            raise SystemExit("figure %s %s is not square-checks' %s %s" % (fc, d[fc], sc, sq[sc]))
    put("a;b;c", "the figure's data table equals square-checks.csv on the square and every section and sheet column",
        src, "square_mm and the sections", "yes")
    put("b;c", "square that passed the checks against our sheets before crossings between traced surfaces were adjudicated (panels b and c); mm", src, "square_mm", sq["square_mm"], key="square_mm")
    # The headline under the certificate with adjudicated crossings (decision of 2026-09-30): column c of the same
    # surface's row of square-three-definitions.csv; the figure itself still draws the square of column a.
    td = [r for r in rd(os.path.join(here, "inputs/render-routes-0826/square-three-definitions.csv"))
          if r["route"] == "R2cnative" and r["surface"] == SURFACE]
    if len(td) != 1:
        raise SystemExit("square-three-definitions.csv: %d R2cnative rows of %s" % (len(td), SURFACE))
    if abs(float(td[0]["a_certified_this_study_mm"]) - float(sq["square_mm"])) > 5e-4:
        raise SystemExit("square-three-definitions.csv column a %s is not square-checks' %s" % (td[0]["a_certified_this_study_mm"], sq["square_mm"]))
    if abs(float(d["adjudicated_square_mm"]) - float(td[0]["c_certified_adjudicated_mm"])) > 5e-5:
        raise SystemExit("figure panel (a) square %s is not column c's %s" % (d["adjudicated_square_mm"], td[0]["c_certified_adjudicated_mm"]))
    put("a", "certified square with crossings between traced surfaces adjudicated (drawn in panel a); mm",
        "inputs/render-routes-0826/square-three-definitions.csv", "c_certified_adjudicated_mm",
        td[0]["c_certified_adjudicated_mm"], key="square_c")
    put("a", "seed of the start", src, "surface", SURFACE.split("-")[1].replace("seed", ""), key="seed")
    put("a", "turn to z up", "figure data", "turn_to_z_up", d["turn_to_z_up"])
    rt = [r for r in rd(os.path.join(here, "evidence/studies/render-routes-0826/routes.csv"))
          if r.get("route") == "R2cnative" and r["surface"] == SURFACE][0]
    put("a", "in plane rotation of the grid from the nearest axis aligned grid, over the earlier square's box; degrees", "render-routes-0826/routes.csv",
        "rotation_inplane_median", rt["rotation_inplane_median"], key="rotation")
    put("a", "panel (a) regrid", "", "", "none: the tracer's own grid, quarter turns only (the align.py regrid was of the earlier square)")
    put("b", "our sheet in the cut", src, "within3_best_sheet", sq["within3_best_sheet"].replace("PHerc0826-", ""), key="our_sheet")
    put("b", "share of the square's nodes within the near band of that sheet", src, "within3_share_all_cells",
        sq["within3_share_all_cells"], key="on_ours")
    put("c", "section i share within the near band", src, "section_i_share_within_3_vox", sq["section_i_share_within_3_vox"], key="sec_i")
    put("c", "section j share within the near band", src, "section_j_share_within_3_vox", sq["section_j_share_within_3_vox"], key="sec_j")
    put("b;c", "near band; voxels", src, "the column name within_3", "3", key="near_vox")
    figlib.write_plotted(out, "figure C21, written by src/tools/%s.py at %s: render-routes-0826's figure of the R2c certified square (panel a adjudicated, b and c the earlier square) of "
                         "%s, pinned and checked against square-checks.csv; RAW SCAN, NO INK DETECTOR. Not for a public "
                         "repository without the owner's word." % (FIGURE, figlib.utc_now(), SURFACE), FIELDS, rows)
    if shipped:
        dst = os.path.join(here, "paper/figures")
        shutil.copyfile(os.path.join(AF, STEM + ".pdf"), os.path.join(dst, FIGURE + ".pdf"))
        shutil.copyfile(os.path.join(AF, STEM + ".png"), os.path.join(dst, FIGURE + ".png"))
    sys.stderr.write("%s: %d rows\n" % (out, len(rows)))


if __name__ == "__main__":
    main()
