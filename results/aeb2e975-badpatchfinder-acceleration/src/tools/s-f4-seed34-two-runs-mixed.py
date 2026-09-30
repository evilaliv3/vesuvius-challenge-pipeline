#!/usr/bin/env python3
"""Figure S4, the data step: the mixture of two runs in seed34's growth tree.

The specification: "the mixture of two runs on seed34: patch ids on the x axis, the stale ones
marked, the 104 without a file and the 327 silent ones
(growth-bookkeeping/evidence/id-inventory-seed34.csv)".

The specification names the wrong file for the strip, and the correction of 2026-09-22 from the
coordinator says so. id-inventory-seed34.csv is a twelve row quantity table: one row per
quantity, with value and source. It states every count the figure needs, including the 413 ids
the growth log says cannot be this run's, the 104 orphans, the 86 that are both, and the 327
that the new run created again and that therefore point at geometry the alignment was never
computed against. It holds no patch id and no timestamp at all, so nothing per id can be drawn
from it.

The per id data is in two other files of the same study, and the figure reads both:

  growth-bookkeeping/evidence/impossible-ids-seed34.csv    one row per stale id, with the round
                     header at which the aligner first named it
  growth-bookkeeping/evidence/stale-chunks-seed34.csv      one row per file under
                     growth/surface.bp whose mtime is before the start of the growth that wrote
                     growth/rel.csv: the earlier run's leftovers, which the new growth opened as
                     its starting surface. Its last row is a summary with chunk = TOTAL and is
                     not a chunk; it is excluded from the strip and its value is kept as a row
                     of the plotted table.

What no CSV of this home carries is the join: which of those 413 ids has a patch file and which
does not. The counts are in the inventory, the ids are in the other file, and nothing pairs
them. So this script draws the two strips it can draw, writes the composition it can count, and
writes one row with series = pending naming exactly the table that is missing. The figure prints
that pending line on its own face rather than colouring the strip by a rule invented here.

  panel stale id     impossible-ids-seed34.csv, columns patch_id and
                     first_named_at_round_header
  panel stale chunk  stale-chunks-seed34.csv, columns mtime and bytes, the timeline of what the
                     earlier run left in the folder
  panel composition  five counts: id-inventory-seed34.csv, column value on the rows whose
                     quantity is the exact string named in the quantity column here
  pending            what has to be measured before the strip can be marked by class
"""

import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib  # noqa: E402

DEFAULT_RUNS = "/data/scrollagent/runs/rev1"
COMPOSITION = [
    ("patch files on disk", "patch files written by this run"),
    ("ids the log says cannot be this run's", "stale ids named by the aligner"),
    ("orphan ids of badpatch-crash", "ids in rel.csv with no patch file"),
    ("orphans that the log also says cannot be this run's", "stale and with no patch file"),
    ("of those, with a patch file", "stale and created again by this run"),
]
FIELDS = ["i",
          "stale_patch_id", "stale_round",
          "chunk_minutes", "chunk_bytes", "chunk_name",
          "comp_label", "comp_count", "comp_quantity",
          "chunk_total_bytes", "pending_label", "pending_note",
          "source_files"]
NUMERIC = ("stale_patch_id", "stale_round", "chunk_minutes", "chunk_bytes", "comp_count",
           "chunk_total_bytes")
SOURCES = ("growth-bookkeeping/evidence/impossible-ids-seed34.csv; "
           "growth-bookkeeping/evidence/stale-chunks-seed34.csv; "
           "growth-bookkeeping/evidence/id-inventory-seed34.csv")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=DEFAULT_RUNS)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = a.out or os.path.join(here, "evidence/figures/s-f4-seed34-two-runs-mixed.csv")

    st = figlib.Studies(here, a.runs)
    notes = []

    # --- the counts, from the quantity table the specification named -----------------------
    _, _, inv = figlib.read_study_csv(
        st.path("growth-bookkeeping/evidence/id-inventory-seed34.csv"))
    counts = {r["quantity"]: r["value"] for r in inv}
    composition = []
    for quantity, label in COMPOSITION:
        if quantity not in counts:
            notes.append(f"id-inventory-seed34.csv has no row for the quantity {quantity}")
            continue
        composition.append({"comp_label": label, "comp_quantity": quantity,
                            "comp_count": figlib.num_or_nan(counts[quantity], "%.0f")})

    # --- the stale ids ---------------------------------------------------------------------
    ids_path = st.path("growth-bookkeeping/evidence/impossible-ids-seed34.csv")
    stale = []
    if os.path.exists(ids_path):
        _, _, idrows = figlib.read_study_csv(ids_path)
        for r in idrows:
            stale.append({"stale_patch_id": figlib.num_or_nan(r["patch_id"], "%.0f"),
                          "stale_round": figlib.num_or_nan(
                              r["first_named_at_round_header"], "%.0f")})
    else:
        notes.append("impossible-ids-seed34.csv is not on disk: the strip has no ids to place")

    # --- the earlier run's leftovers -------------------------------------------------------
    chunks_path = st.path("growth-bookkeeping/evidence/stale-chunks-seed34.csv")
    chunks, total_bytes = [], figlib.NAN
    if os.path.exists(chunks_path):
        _, _, crows = figlib.read_study_csv(chunks_path)
        stamps = []
        for r in crows:
            if r["chunk"].strip() == "TOTAL":
                total_bytes = figlib.num_or_nan(r["bytes"], "%.0f")
                continue
            try:
                ts = dt.datetime.strptime(r["mtime"][:19], "%Y-%m-%dT%H:%M:%S").replace(
                    tzinfo=dt.timezone.utc).timestamp()
            except ValueError:
                notes.append(f"stale-chunks-seed34.csv: {r['chunk']} has mtime {r['mtime']}")
                continue
            stamps.append((ts, r))
        stamps.sort(key=lambda pair: pair[0])
        if stamps:
            t0 = stamps[0][0]
            for ts, r in stamps:
                chunks.append({"chunk_minutes": "%.3f" % ((ts - t0) / 60.0),
                               "chunk_bytes": figlib.num_or_nan(r["bytes"], "%.0f"),
                               "chunk_name": r["chunk"]})
    else:
        notes.append("stale-chunks-seed34.csv is not on disk: the timeline of the earlier "
                     "run's leftovers is not drawn")

    pending = {
        "pending_label": "which stale ids have a patch file",
        "pending_note": (
            "no CSV of this home pairs a stale id with whether the patches folder holds it. "
            "The counts exist in id-inventory-seed34.csv and the ids exist in "
            "impossible-ids-seed34.csv, and the join does not. What would fill it: a table "
            "with one row per stale id and a column saying whether patches/<id> exists, "
            "written by a tool that lists the growth tree once"),
        "chunk_total_bytes": total_bytes,
    }

    rows = figlib.wide_rows(max(len(stale), len(chunks), len(composition), 1))
    for k, row in enumerate(rows):
        if k < len(stale):
            row.update(stale[k])
        if k < len(chunks):
            row.update(chunks[k])
        if k < len(composition):
            row.update(composition[k])
        if k == 0:
            row.update(pending)
        row["source_files"] = SOURCES if k == 0 else ""
        for f in FIELDS:
            row.setdefault(f, figlib.NAN if f in NUMERIC else "")

    comment = (
        "figure S4, the numbers plotted and nothing else. One row per position on the abscissa, "
        "three panels sharing the row index and each with its own columns. The specification "
        "named growth-bookkeeping/evidence/id-inventory-seed34.csv for the strip; that file is "
        "a twelve row quantity table with no patch id and no timestamp in it, so it supplies "
        "the counts only and the per id data comes from the two other files of the same study. "
        "stale_patch_id and stale_round are columns patch_id and first_named_at_round_header "
        "of growth-bookkeeping/evidence/impossible-ids-seed34.csv, one per id the growth log "
        "says cannot be this run's. chunk_minutes and chunk_bytes are columns mtime and bytes "
        "of growth-bookkeeping/evidence/stale-chunks-seed34.csv, one per file the earlier run "
        "left under growth/surface.bp, the minutes counted from the earliest of them; that "
        "file's TOTAL row is not a chunk and is carried apart as chunk_total_bytes, in bytes, "
        "so that no byte count lands on an axis that counts patch ids. comp_count is column "
        "value of id-inventory-seed34.csv on the row whose quantity is in comp_quantity. "
        "pending_label and pending_note say what the specification asks for and no file holds, "
        "and the figure prints it on its own face. A position a panel does not reach carries "
        "nan and never a zero. " + st.report() + " Notes: " + ("; ".join(notes) if notes else "none") +
        ". Written " + figlib.utc_now() + "."
    )
    figlib.write_plotted(out, comment, FIELDS, rows)
    sys.stderr.write(f"{out}: {len(rows)} rows\n")
    for n in notes:
        sys.stderr.write("  note: " + n + "\n")


if __name__ == "__main__":
    main()
