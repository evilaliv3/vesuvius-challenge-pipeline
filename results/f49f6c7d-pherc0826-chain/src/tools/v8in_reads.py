#!/usr/bin/env python3
"""v8in_reads.py: one row per v8-in read of PHerc. 0826, for the article's table «v8-in reads on PHerc. 0826» (owner's
order of 2026-09-30).

Reads, from this work's copies (src/evidence/studies):
  - ink-v8in-0826/describe-v2.csv, render set base: the squares of seeds 6273 and 5364 (route R2c, as they stood before the
    adjudication), both depth orders, the sheet and its two null copies, over the nodes of each square's aligned grid;
  - every describe*.csv of a study named ink-v8in-0826-r2d*: reads of R2d surfaces, rows of region «all» (a whole surface)
    or of a column square/extent when the study writes one. A study with no copy column read the sheet alone: its null
    copies are written «not read». A study added later is read by rerunning this tool, nothing else.
The depth order is «w016» when the row's order label names the order measured on w016 and not the other one, else
«other». sheet_over_larger_copy is the sheet's share over the larger of its two copies' shares, from the source column
when it has one, else computed here from the printed shares (four decimals).

Writes src/evidence/derived/v8in-reads.csv. Standard library only.
"""
import csv, glob, os, re, subprocess, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = os.path.join(SRC, "evidence", "studies")
OUT = os.path.join(SRC, "evidence", "derived", "v8in-reads.csv")
FIELDS = ["read", "surface", "extent", "order", "pixels", "pixel_set", "sheet_share", "plus_share", "minus_share",
          "sheet_over_larger_copy", "nulls", "source"]


def rows(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))


def header(p):
    with open(p) as fh:
        return fh.readline()


def order_of(label):
    label = label.lower()
    if "not" in label or "other" in label:
        return "other"
    if "w016" in label:
        return "w016"
    sys.exit("v8in_reads.py: order label %r names neither order" % label)


def main():
    out = []
    # (1) the two R2c squares
    p = os.path.join(ST, "ink-v8in-0826", "describe-v2.csv")
    by = {}
    for r in rows(p):
        if r["render_set"] != "base":
            continue
        by.setdefault((r["square"], order_of(r["order_label"])), {})[r["surface"]] = r      # the last row of a kind wins
    for (sq, od), d in sorted(by.items(), key=lambda kv: (kv[0][0] != "s6273", kv[0][1] != "w016")):
        if set(d) != {"sheet", "plus", "minus"}:
            sys.exit("v8in_reads.py: %s %s has %s, not the sheet and two copies" % (sq, od, sorted(d)))
        s = d["sheet"]
        out.append(dict(read="R2c-%s-%s" % (sq, od), surface="R2c from seed %s" % sq[1:], extent="square before the adjudication",
                        order=od, pixels=s["square_nodes"], pixel_set="nodes of the square's aligned grid",
                        sheet_share=s["share_prob_ge_0.5"], plus_share=d["plus"]["share_prob_ge_0.5"],
                        minus_share=d["minus"]["share_prob_ge_0.5"],
                        sheet_over_larger_copy=s["sheet_share_over_larger_copy_share"], nulls="read",
                        source="ink-v8in-0826/describe-v2.csv"))
    # (2) the R2d reads, whatever study wrote them
    for p in sorted(glob.glob(os.path.join(ST, "ink-v8in-0826-r2d*", "describe*.csv"))):
        rel = os.path.relpath(p, ST)
        m = re.search(r"R2d (seed\d+) (S\d+)", header(p))
        rs = rows(p)
        cols = set(rs[0]) if rs else set()
        groups = {}
        for r in rs:
            extent = r.get("square") or r.get("extent") or ("whole surface" if r.get("region") == "all" else None)
            if not extent:
                continue
            surf = r.get("surface_name") or (("%s %s" % (m.group(1), m.group(2))) if m else None)
            if not surf:
                sys.exit("v8in_reads.py: %s names no surface" % rel)
            copy = r.get("copy", "sheet")
            groups.setdefault((surf, extent, order_of(r["order_label"])), {})[copy] = r
        for (surf, extent, od), d in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2] != "w016")):
            s = d.get("sheet")
            if s is None:
                sys.exit("v8in_reads.py: %s %s %s has no sheet row" % (rel, surf, od))
            nulls = "read" if {"plus", "minus"} <= set(d) else "not read"
            ratio = ""
            if nulls == "read":
                ratio = s.get("sheet_over_larger_copy") or "%.4f" % (float(s["share_ge_05"]) / max(
                    float(d["plus"]["share_ge_05"]), float(d["minus"]["share_ge_05"])))
            out.append(dict(read="R2d-%s-%s-%s" % (surf.replace(" ", "-"), extent.replace(" ", "-"), od),
                            surface="R2d from %s" % surf.replace("seed", "seed "), extent=extent, order=od,
                            pixels=s["pixels_scored"], pixel_set="render pixels covered by the read",
                            sheet_share=s["share_ge_05"], plus_share=d["plus"]["share_ge_05"] if nulls == "read" else "not read",
                            minus_share=d["minus"]["share_ge_05"] if nulls == "read" else "not read",
                            sheet_over_larger_copy=ratio or "not read", nulls=nulls, source=rel))
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(OUT, "w", newline="") as fh:
        fh.write('"# written by src/tools/v8in_reads.py at %s: one row per v8-in read of PHerc. 0826 (share = pixels at '
                 'probability 0.5 or more over the pixels scored), from this work\'s copies of ink-v8in-0826 and every '
                 'ink-v8in-0826-r2d* study; uncalibrated, descriptive"\n' % now)
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("v8in_reads.py: %d reads" % len(out))


if __name__ == "__main__":
    main()
