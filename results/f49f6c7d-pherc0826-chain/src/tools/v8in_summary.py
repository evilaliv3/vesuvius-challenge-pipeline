#!/usr/bin/env python3
"""The numbers of the paragraph on Youssef Nader's v8-in ink model, picked or recomputed from the copies of ink-v8in-0826
and selftrain-v8in-0826 in src/evidence/studies, one row each, with the file, the column and the rows each is over.

WHY IT EXISTS. The owner's order of 2026-09-30 puts one paragraph on v8-in in the article, after the positive control.
paper_numbers.py picks ONE cell per macro; the lowest and highest ratio on known ink (a spread over three rows), the
latest of repeated rows of describe-v2.csv, the probability threshold and the face offset (read from a column name and
from a render set's name) and the check that each PHerc0826 ratio lies inside the known ink spread are written here.

What it reads:
  selftrain-v8in-0826/order-0139.csv   the depth order on PHerc0139 w016 (column ba; the row chosen yes and the other)
  ink-v8in-0826/hf-files.csv           the release read: repository and pinned revision
  ink-v8in-0826/describe-v2.csv        the maps over each aligned square: share_prob_ge_0.5 per square, render set, order,
                                       surface; a repeated key takes its LAST row (the file is appended in time)
  ink-v8in-0826/ratio-calibration.csv  ratio_to_larger_copy: the three known ink rows of PHerc0139 w016 on the labelled
                                       pixel set, and the PHerc0826 rows (for seed5364 the corrected row, scroll PHerc0826)
Nothing is interpolated or defaulted: a missing row stops the tool.

Usage: v8in_summary.py [--out PATH]
"""
import argparse, csv, os, re, subprocess, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(S, "evidence", "studies")


def rd(p):
    with open(p, newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.lstrip().startswith(('"#', "#"))))


def one(rows, what, **kw):
    hit = [r for r in rows if all(r.get(k) == v for k, v in kw.items())]
    if len(hit) != 1:
        sys.exit("v8in_summary.py: %s: %d rows for %s" % (what, len(hit), kw))
    return hit[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(S, "evidence", "derived", "v8in-summary.csv"))
    a = ap.parse_args()
    out = []

    def put(q, v, f, col, rows):
        out.append({"quantity": q, "value": v, "source_file": f, "source_column": col, "rows_covered": rows})

    # the depth order on w016
    O = "selftrain-v8in-0826/order-0139.csv"
    orows = rd(os.path.join(EV, O))
    ch = one(orows, O, chosen="yes"); ot = one(orows, O, chosen="no")
    put("order_w016_ba_chosen", ch["ba"], O, "ba", "chosen yes (order %s)" % ch["order"])
    put("order_w016_ba_other", ot["ba"], O, "ba", "chosen no (order %s)" % ot["order"])
    put("order_w016_pixels", ch["pixels"], O, "pixels", "chosen yes")
    if float(ch["ba"]) <= float(ot["ba"]):
        sys.exit("v8in_summary.py: the chosen order does not have the higher ba")
    # the release
    H = "ink-v8in-0826/hf-files.csv"
    h = rd(os.path.join(EV, H))
    revs = {r["revision"] for r in h if r["repo"] == "YoussefMoNader/ink-8um-v8in" and r["revision"]}   # one row has no revision (the parameter count row)
    if len(revs) != 1:
        sys.exit("v8in_summary.py: %d revisions of the model repository" % len(revs))
    put("model_repo", "YoussefMoNader/ink-8um-v8in", H, "repo", "every row")
    put("model_revision_short", sorted(revs)[0][:7], H, "revision", "every row of the model repository")
    # the maps
    D = "ink-v8in-0826/describe-v2.csv"
    drows = rd(os.path.join(EV, D))
    col = [c for c in drows[0] if c.startswith("share_prob_ge_")]
    if len(col) != 1:
        sys.exit("v8in_summary.py: no single share column in describe-v2.csv")
    put("threshold", col[0][len("share_prob_ge_"):], D, "the column name %s" % col[0], "header")
    last = {}
    for r in drows:
        last[(r["square"], r["render_set"], r["order"], r["surface"])] = r
    for sq in ("s6273", "s5364"):
        for order, tag in (("normal", "otherorder"),):
            for surf in ("sheet", "plus", "minus"):
                k = (sq, "base", order, surf)
                if k not in last:
                    sys.exit("v8in_summary.py: describe-v2.csv has no row %s" % (k,))
                put("%s_%s_%s_share" % (sq, tag, surf), last[k][col[0]], D, col[0], "last row of square %s, set %s, order %s, surface %s" % k)
    faces = sorted({r["render_set"] for r in drows if r["render_set"].startswith("face")})
    offs = {re.sub(r"^face(plus|minus)", "", f) for f in faces}
    if faces != ["faceminus5", "faceplus5"] or len(offs) != 1:
        sys.exit("v8in_summary.py: the face render sets are %s" % faces)
    put("face_offset_vox", offs.pop(), D, "render_set (faceplus5, faceminus5)", "render set names")
    for f, tag in (("faceplus5", "plus"), ("faceminus5", "minus")):
        for order, otag in (("reverse", "w016order"), ("normal", "otherorder")):
            k = ("s6273", f, order, "sheet")
            if k not in last:
                sys.exit("v8in_summary.py: describe-v2.csv has no row %s" % (k,))
            put("s6273_face%s_%s_share" % (tag, otag), last[k][col[0]], D, col[0], "last row of s6273, %s, %s, sheet" % (f, order))
    # the ratio on known ink and on PHerc0826
    R = "ink-v8in-0826/ratio-calibration.csv"
    rrows = rd(os.path.join(EV, R))
    known = [r for r in rrows if r["scroll"] == "PHerc0139 w016" and r["pixel_set"].startswith("labelled")]
    if sorted(r["surface"] for r in known) != ["A", "Bx", "theirs"]:
        sys.exit("v8in_summary.py: the known ink rows are %s" % [r["surface"] for r in known])
    vals = [float(r["ratio_to_larger_copy"]) for r in known]
    lo = min(known, key=lambda r: float(r["ratio_to_larger_copy"])); hi = max(known, key=lambda r: float(r["ratio_to_larger_copy"]))
    put("ratio_known_rows", len(known), R, "surface", "scroll PHerc0139 w016, pixel set labelled")
    put("ratio_known_min", lo["ratio_to_larger_copy"], R, "ratio_to_larger_copy", "min over the %d known ink rows (%s)" % (len(known), lo["surface"]))
    put("ratio_known_max", hi["ratio_to_larger_copy"], R, "ratio_to_larger_copy", "max over the %d known ink rows (%s)" % (len(known), hi["surface"]))
    shared = []
    for sq in ("s6273", "s5364"):
        r = [x for x in rrows if x["surface"] == sq and x["scroll"] == "PHerc0826"]
        if len(r) != 1:
            sys.exit("v8in_summary.py: %d PHerc0826 rows of %s in ratio-calibration.csv" % (len(r), sq))
        # the order measured on w016: sheet and copies on the square's render pixels, the same pixel set as the ratio
        for surf in ("sheet", "plus", "minus"):
            put("%s_w016order_%s_share" % (sq, surf), r[0]["share_ge_0.5_%s" % surf], R, "share_ge_0.5_%s" % surf,
                "surface %s, scroll PHerc0826 (pixel set %s)" % (sq, r[0]["pixel_set"]))
        for c in ("plus_independence", "minus_independence"):
            m = re.search(r"\((\d+) of (\d+) layers shared\)", r[0][c])
            if not m:
                sys.exit("v8in_summary.py: %s of %s has no layer count" % (c, sq))
            shared.append((int(m.group(1)), int(m.group(2))))
        v = float(r[0]["ratio_to_larger_copy"])
        put("ratio_%s" % sq, r[0]["ratio_to_larger_copy"], R, "ratio_to_larger_copy", "surface %s, scroll PHerc0826" % sq)
        put("ratio_%s_inside_known" % sq, "yes" if min(vals) <= v <= max(vals) else "no", R, "ratio_to_larger_copy",
            "%s against the min and max of the known ink rows" % sq)
    if len({t for _, t in shared}) != 1:
        sys.exit("v8in_summary.py: the null copies do not all count the same layers")
    put("null_layers_shared_min", min(a for a, _ in shared), R, "plus_independence; minus_independence", "the PHerc0826 rows, both copies")
    put("null_layers_shared_max", max(a for a, _ in shared), R, "plus_independence; minus_independence", "the PHerc0826 rows, both copies")
    put("null_layers_total", shared[0][1], R, "plus_independence; minus_independence", "the PHerc0826 rows")
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", newline="") as fh:
        fh.write('"# written by src/tools/v8in_summary.py at %s from the copies of ink-v8in-0826 and selftrain-v8in-0826 in '
                 'src/evidence/studies; rows_covered says which rows a value is over; a repeated key of describe-v2.csv takes its last row"\n' % now)
        w = csv.DictWriter(fh, fieldnames=["quantity", "value", "source_file", "source_column", "rows_covered"])
        w.writeheader(); w.writerows(out)
    print("v8in_summary.py: %d rows to %s" % (len(out), a.out))


if __name__ == "__main__":
    main()
