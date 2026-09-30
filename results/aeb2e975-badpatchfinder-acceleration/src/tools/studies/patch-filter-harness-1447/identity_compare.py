#!/usr/bin/env python3
"""identity_compare.py <seed> <rerun-out-dir> [<dest-csv>]: the rerun with an empty drop list against the delivery.

Rows, to evidence/identity-<seed>.csv:
  kind sheet: sha256 of delivered C40/patch_<n>.bin, of the rerun view/patch_<n>.bin, equal yes/no;
  kind squares_row: every column of the delivered squares row against the rerun row, the differing columns named;
  kind stage_file: the small outputs of the stages (bad patches, orders, positions, coordinates), sha256 equal or not;
  kind area: the delivered area CSV against the rerun one, byte equal or not.
Then a verdict row: bytes (every sheet sha256 equal and every squares row equal), squares_only (rows equal apart from
sha256 and sheets differ), or fail. A missing file raises.
"""
import csv, glob, hashlib, os, sys

R1 = "/data/scrollagent/runs/rev1"
S = R1 + "/seeds-at-scale-1447"
H = R1 + "/patch-filter-harness-1447"
TOOL = "patch-filter-harness-1447/tools/identity_compare.py"
STAGE_FILES = ["badpatches.csv", "badpatchscores.csv", "patchVolCoords.csv", "alignmentorders.txt", "neighbourss.csv",
               "badbridgess_out.csv", "patchorder.csv", "patchorders.csv"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows_of(p):
    return list(csv.DictReader(l for l in open(p, newline="") if not l.startswith('"#') and not l.startswith("#")))


def main():
    a, o = sys.argv[1], sys.argv[2]
    C = S + "/out/%s/C40" % a
    V = o + "/view"
    out = []
    ds = sorted(glob.glob(C + "/patch_[0-9]*.bin"), key=lambda p: int(os.path.basename(p)[6:-4]))
    rs = sorted(glob.glob(V + "/patch_[0-9]*.bin"), key=lambda p: int(os.path.basename(p)[6:-4]))
    if [os.path.basename(p) for p in ds] != [os.path.basename(p) for p in rs]:
        out.append(["sheet_set", "", "delivered %d, rerun %d" % (len(ds), len(rs)), "", "no", ""])
    sheq = 0
    for p in ds:
        n = os.path.basename(p)
        q = V + "/" + n
        d = sha(p); r = sha(q) if os.path.exists(q) else "absent"
        eq = d == r
        sheq += eq
        out.append(["sheet", n, d, r, "yes" if eq else "no",
                    "" if eq else "sizes %d and %s" % (os.path.getsize(p), os.path.getsize(q) if os.path.exists(q) else "absent")])
    dq = {r["sheet"]: r for r in rows_of(S + "/evidence/squares-%s.csv" % a)}
    rq = {r["sheet"]: r for r in rows_of(o + "/squares.csv")}
    rows_eq = rows_eq_but_sha = 0
    for k in sorted(dq, key=int):
        d, r = dq[k], rq[k]
        diff = [c for c in d if d[c] != r[c]]
        rows_eq += not diff
        rows_eq_but_sha += not [c for c in diff if c != "sha256"]
        out.append(["squares_row", k, d["square_mm_min_step"], r["square_mm_min_step"], "yes" if not diff else "no",
                    "differs: " + " ".join(diff) if diff else ""])
    for f in STAGE_FILES + sorted(os.path.basename(p) for p in glob.glob(C + "/patchPositions_*.txt")):
        p, q = C + "/" + f, V + "/" + f
        if not os.path.exists(p) and not os.path.exists(q):
            continue
        d = sha(p) if os.path.exists(p) else "absent"; r = sha(q) if os.path.exists(q) else "absent"
        out.append(["stage_file", f, d, r, "yes" if d == r else "no", ""])
    pa, qa = S + "/evidence/area-%s.csv" % a, o + "/area.csv"
    da, ra = sha(pa), sha(qa)
    out.append(["area", os.path.basename(pa), da, ra, "yes" if da == ra else "no",
                "" if da == ra else "rows differ: %s" % ([x for x in zip(rows_of(pa), rows_of(qa)) if x[0] != x[1]][:1])])
    n = len(ds)
    if sheq == n and rows_eq == len(dq) == n and len(rs) == n:
        v = "bytes"
    elif rows_eq_but_sha == len(dq) == n:
        v = "squares_only"
    else:
        v = "fail"
    out.append(["verdict", "", "sheets sha equal %d of %d" % (sheq, n), "squares rows equal %d of %d (apart from sha256: %d)"
                % (rows_eq, len(dq), rows_eq_but_sha), v, ""])
    dest = sys.argv[3] if len(sys.argv) > 3 else H + "/evidence/identity-%s.csv" % a
    with open(dest, "w", newline="") as fh:
        fh.write('"# written by %s: rerun %s with an empty drop list against seeds-at-scale-1447/out/%s/C40 and '
                 'evidence/squares-%s.csv, area-%s.csv. delivered and rerun are sha256 (or square_mm_min_step for '
                 'squares_row)."\n' % (TOOL, os.path.relpath(o, R1), a, a, a))
        w = csv.writer(fh)
        w.writerow(["kind", "item", "delivered", "rerun", "equal", "note"])
        for r in out:
            w.writerow(r)
    print(a, v, "sheets equal %d/%d, squares rows equal %d/%d" % (sheq, n, rows_eq, len(dq)))


if __name__ == "__main__":
    main()
