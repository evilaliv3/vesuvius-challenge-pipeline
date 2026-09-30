#!/usr/bin/env python3
"""The seed rule of 2026-09-23T19:14:15Z (director), read back per seed as columns.

A seed is a seed when ALL of these hold, each written as its own column:
  test_seed_voxel      the prediction voxel is 255 and its six face neighbours are 255 (the rule of
                       20 September, re read here, not copied from the draw's own file);
  test_raw_grey        the RAW masked scan at the seed, nearest voxel, is non zero and present. A
                       chunk the bucket answers 404 is masked away (absent), a stored 0 is the mask
                       value: both are «no». A chunk that could not be fetched gives raw_at_seed
                       «not measurable» and the test is «no» (the rule fails, it is not skipped);
  test_share_at_most_0_5  the prediction chunk holding the seed (the zarr's own chunk, 192 cubed on
                       both scrolls read so far) holds 255 on at most half of its voxels, exact
                       fraction, printed to four decimals.
passes_rule is «yes» only when the three are «yes».

RAW SOURCE. The published raw masked scan, level 0, on the open bucket, anonymous HTTPS, the method
of villa-tracer-build/tools/fetch_surface_chunks.py: uncompressed chunks (compressor null, C order,
z, y, x), one object per chunk of exactly chunk bytes. Only the ONE raw chunk under each seed is
fetched, whole, and cached under --cache so a rerun fetches nothing. Before any seed the raw .zarray
is fetched and its shape must equal the prediction's shape (so a prediction voxel is a raw voxel),
its dtype uint8, compressor null: otherwise this refuses. The raw chunk edge is read from .zarray.

REFERENCE. villa-tracer-build/evidence/seed-block-check.csv found raw_at_seed «not measurable» for
PHerc1447 seed38, seed40, seed11 and chunk shares 0.9973, 0.9936, 0.9903; this tool must reproduce
those (column ref_seed_block_check). The chunk share is also compared with
evidence/seed-chunk-share.csv where that file lists the attempt (column ref_seed_chunk_share).

usage:
  seed_rule_check.py --seeds <csv with attempt,seed_x,seed_y,seed_z> --group <name>
                     --pred <prediction zarr level 0> --raw <https url of raw zarr level 0>
                     --out <csv> [--attempts a,b,c | --attempts-file f] [--append] [--streams 16]
                     [--cache <dir>]
"""
import argparse, csv, json, os, sys, threading, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
import zarr

S = "/data/scrollagent/runs/rev1/seeds-at-scale-1447"
TOOL = "seeds-at-scale-1447/tools/seed_rule_check.py"
NM = "not measurable"
REF_BLOCK = "/data/scrollagent/runs/rev1/villa-tracer-build/evidence/seed-block-check.csv"
REF_SHARE = os.path.join(S, "evidence", "seed-chunk-share.csv")
COLUMNS = ["tool", "group", "attempt", "seed_x", "seed_y", "seed_z", "pred_value",
           "six_face_neighbours_255", "test_seed_voxel", "pred_chunk_zyx", "pred_chunk_share_255",
           "test_share_at_most_0_5", "raw_chunk_zyx", "raw_chunk_status", "raw_at_seed",
           "test_raw_grey", "passes_rule", "ref_seed_chunk_share", "ref_seed_block_check",
           "pred_path", "raw_url"]
NOTE = ('"# written by %s at %s: the seed rule of the director, 2026-09-23T19:14:15Z; one row per seed; '
        'the three test_ columns are the rule and passes_rule is yes only when all three are yes. '
        'raw_at_seed is the nearest voxel of the RAW masked scan; raw_chunk_status absent means the bucket '
        'answered 404 (masked away); a stored 0 is the mask value; both fail test_raw_grey. '
        'ref_ columns compare with earlier tools where they list the seed, else not listed."\n')


def rows_after_comment(path):
    lines = [l for l in open(path, newline="") if not l.lstrip().startswith('"#') and not l.startswith("#")]
    return list(csv.DictReader(lines))


_local = threading.local()


def session():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.mount("https://", requests.adapters.HTTPAdapter(pool_connections=1, pool_maxsize=2, max_retries=3))
        _local.s = s
    return s


def fetch(url, base, nbytes):
    """Returns 'present', 'absent' or 'failed'; the chunk lands at base.bin, a 404 as base.absent."""
    if os.path.exists(base + ".bin"):
        return "present"
    if os.path.exists(base + ".absent"):
        return "absent"
    for attempt in range(5):
        try:
            r = session().get(url, timeout=60)
        except requests.RequestException:
            time.sleep(1 + attempt)
            continue
        if r.status_code == 404:
            open(base + ".absent", "w").close()
            return "absent"
        if r.status_code == 200 and len(r.content) == nbytes:
            with open(base + ".part", "wb") as fh:
                fh.write(r.content)
            os.replace(base + ".part", base + ".bin")
            return "present"
        time.sleep(1 + attempt)
    return "failed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--group", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--attempts", default="")
    ap.add_argument("--attempts-file", default="")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--streams", type=int, default=16)
    ap.add_argument("--cache", default="")
    a = ap.parse_args()

    seeds = {r["attempt"]: r for r in rows_after_comment(a.seeds)}
    if a.attempts_file:
        want = [l.strip() for l in open(a.attempts_file) if l.strip()]
    elif a.attempts:
        want = [x.strip() for x in a.attempts.split(",") if x.strip()]
    else:
        want = list(seeds)
    missing = [w for w in want if w not in seeds]
    if missing:
        raise SystemExit("REFUSED: not in %s: %s" % (a.seeds, missing))
    print("expected %d seeds for group %s" % (len(want), a.group), flush=True)

    P = zarr.open(a.pred, mode="r")
    pshape = tuple(P.shape)
    pz, py, px = P.chunks
    raw_meta = requests.get(a.raw.rstrip("/") + "/.zarray", timeout=60)
    if raw_meta.status_code != 200:
        raise SystemExit("REFUSED: raw .zarray answered %d" % raw_meta.status_code)
    rm = json.loads(raw_meta.text)
    if tuple(rm["shape"]) != pshape:
        raise SystemExit("REFUSED: raw shape %r differs from prediction shape %r" % (rm["shape"], pshape))
    if rm.get("compressor") is not None or rm.get("dtype") != "|u1" or rm.get("order") != "C":
        raise SystemExit("REFUSED: raw is not uncompressed uint8 C order: %r" % rm)
    rc = tuple(rm["chunks"])
    nbytes = int(np.prod(rc))
    sep = rm.get("dimension_separator", ".")
    print("raw %s: shape %r equals prediction, chunks %r, %d bytes per chunk, separator %r"
          % (a.raw, rm["shape"], rc, nbytes, sep), flush=True)

    cache = a.cache or os.path.join(S, "scratch", "raw-chunks-" + a.raw.rstrip("/").split("/")[-2].split("-")[0])
    os.makedirs(cache, exist_ok=True)

    ref_share = {}
    if os.path.exists(REF_SHARE):
        ref_share = {r["attempt"]: r["chunk_share_255"] for r in rows_after_comment(REF_SHARE)}
    ref_block = {}
    if os.path.exists(REF_BLOCK):
        for r in rows_after_comment(REF_BLOCK):
            ref_block[r["seed"]] = (r["pred_chunk_share_255"], r["raw_at_seed"])

    plan = []
    for w in want:
        r = seeds[w]
        x, y, z = int(float(r["seed_x"])), int(float(r["seed_y"])), int(float(r["seed_z"]))
        if not (0 <= z < pshape[0] and 0 <= y < pshape[1] and 0 <= x < pshape[2]):
            raise SystemExit("REFUSED: %s outside the volume" % w)
        c = (z // rc[0], y // rc[1], x // rc[2])
        plan.append((w, x, y, z, c))
    chunks = sorted({p[4] for p in plan})
    status = {}

    def one(c):
        key = sep.join(str(i) for i in c)
        status[c] = fetch("%s/%s" % (a.raw.rstrip("/"), key), "%s/%d_%d_%d" % ((cache,) + c), nbytes)

    t0 = time.time()
    with ThreadPoolExecutor(a.streams) as ex:
        list(ex.map(one, chunks))
    print("raw chunks: %d needed, %d present, %d absent, %d failed, %.1f s"
          % (len(chunks), sum(v == "present" for v in status.values()),
             sum(v == "absent" for v in status.values()), sum(v == "failed" for v in status.values()),
             time.time() - t0), flush=True)

    out_rows = []
    for w, x, y, z, c in plan:
        z0, y0, x0 = (z // pz) * pz, (y // py) * py, (x // px) * px
        ch = np.asarray(P[z0:z0 + pz, y0:y0 + py, x0:x0 + px])
        n255, ntot = int((ch == 255).sum()), int(ch.size)
        share = n255 / ntot
        lz, ly, lx = z - z0, y - y0, x - x0
        val = int(ch[lz, ly, lx])
        nb = []
        for dz, dy, dx in ((-1, 0, 0), (1, 0, 0), (0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1)):
            zz, yy, xx = z + dz, y + dy, x + dx
            if 0 <= zz - z0 < ch.shape[0] and 0 <= yy - y0 < ch.shape[1] and 0 <= xx - x0 < ch.shape[2]:
                nb.append(int(ch[zz - z0, yy - y0, xx - x0]))
            else:
                nb.append(int(P[zz, yy, xx]))
        six = sum(v == 255 for v in nb)
        st = status[c]
        if st == "present":
            blk = np.fromfile("%s/%d_%d_%d.bin" % ((cache,) + c), dtype=np.uint8)
            if blk.size != nbytes:
                raise SystemExit("REFUSED: cached chunk %r has %d bytes, not %d" % (c, blk.size, nbytes))
            blk = blk.reshape(rc)
            raw = int(blk[z % rc[0], y % rc[1], x % rc[2]])
            raw_s = str(raw)
            grey = "yes" if raw != 0 else "no"
        else:
            raw_s = NM
            grey = "no"
        t_seed = "yes" if (val == 255 and six == 6) else "no"
        t_share = "yes" if share <= 0.5 else "no"
        passes = "yes" if (t_seed == "yes" and grey == "yes" and t_share == "yes") else "no"
        rs = ref_share.get(w)
        ref_s = "not listed" if rs is None else ("%s equal" % rs if rs == "%.4f" % share else "%s DIFFERENT" % rs)
        rb = ref_block.get(w)
        if rb is None:
            ref_b = "not listed"
        else:
            ok = rb[0] == "%.4f" % share and rb[1] == raw_s
            ref_b = "share %s raw %s %s" % (rb[0], rb[1], "equal" if ok else "DIFFERENT")
        out_rows.append({
            "tool": TOOL, "group": a.group, "attempt": w, "seed_x": x, "seed_y": y, "seed_z": z,
            "pred_value": val, "six_face_neighbours_255": six, "test_seed_voxel": t_seed,
            "pred_chunk_zyx": "%d/%d/%d" % (z0 // pz, y0 // py, x0 // px),
            "pred_chunk_share_255": "%.4f" % share, "test_share_at_most_0_5": t_share,
            "raw_chunk_zyx": "%d/%d/%d" % c,
            "raw_chunk_status": {"present": "present", "absent": "absent (404, masked away)",
                                 "failed": "failed to fetch"}[st],
            "raw_at_seed": raw_s, "test_raw_grey": grey, "passes_rule": passes,
            "ref_seed_chunk_share": ref_s, "ref_seed_block_check": ref_b,
            "pred_path": a.pred, "raw_url": a.raw})

    if len(out_rows) != len(want):
        raise SystemExit("REFUSED: expected %d rows, built %d" % (len(want), len(out_rows)))
    bad = [r["attempt"] for r in out_rows if "DIFFERENT" in r["ref_seed_chunk_share"] + r["ref_seed_block_check"]]
    if bad:
        raise SystemExit("REFUSED: a reference differs for %s; nothing written" % bad)

    if a.append and os.path.exists(a.out):
        with open(a.out, newline="") as fh:
            lines = fh.read().splitlines()
        hdr = next(csv.reader([lines[1] if lines[0].startswith('"#') else lines[0]]))
        if hdr != COLUMNS:
            raise SystemExit("REFUSED: %s header %s differs from %s" % (a.out, hdr, COLUMNS))
        done = {(r["group"], r["attempt"]) for r in rows_after_comment(a.out)}
        dup = [r["attempt"] for r in out_rows if (a.group, r["attempt"]) in done]
        if dup:
            raise SystemExit("REFUSED: %s already holds group %s rows for %s" % (a.out, a.group, dup))
        fh = open(a.out, "a", newline="")
    else:
        if os.path.exists(a.out):
            raise SystemExit("REFUSED: %s exists; use --append" % a.out)
        fh = open(a.out, "w", newline="")
        fh.write(NOTE % (TOOL, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
        csv.writer(fh).writerow(COLUMNS)
    w = csv.DictWriter(fh, fieldnames=COLUMNS)
    for r in out_rows:
        w.writerow(r)
    fh.close()
    npass = sum(r["passes_rule"] == "yes" for r in out_rows)
    print("group %s: expected %d, wrote %d rows, %d pass the rule" % (a.group, len(want), len(out_rows), npass))


if __name__ == "__main__":
    main()
