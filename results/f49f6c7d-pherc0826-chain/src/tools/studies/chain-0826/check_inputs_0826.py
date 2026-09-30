#!/usr/bin/env python3
"""check_inputs_0826.py: the input check of chain-0826 (DECLARATION.md part 1, written 2026-09-26T08:32:21Z).

Checks I1 to I6 on PHerc0826, with PHerc1447 beside as the known reference where the same quantity exists,
and controls that must fail (a flipped byte must change the md5, a truncated chunk must not decode). One CSV
per check under evidence/inputs/, the tool named in its first line; evidence/inputs/verdict.csv one row per
check and one overall. Bars are the declaration's, typed here once and printed into each CSV.

Run: nice -n 10 python check_inputs_0826.py   (at most 4 worker processes; TMPDIR=/data/tmp)
"""
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from multiprocessing import Pool

import numpy as np
import requests
import zarr

TOOL = "chain-0826/tools/check_inputs_0826.py"
S = "/data/scrollagent/runs/rev1/chain-0826"
OUT = os.path.join(S, "evidence", "inputs")
DS = "/data/scrollagent/data/datasets"
BUCKET = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com"
WORKERS = 4
TMP = "/data/tmp"
sys.path.insert(0, "/data/scrollagent/pipeline/datasets")
from voxel import voxel_um  # noqa: E402

SCROLLS = {
    "PHerc0826": dict(vol="PHerc0826/volumes/20250821151701-9.362um-1.2m-113keV-masked.zarr",
                      pred="PHerc0826/representations/predictions/surfaces/"
                           "20250821151701-surface-20260413222639-surface-m7-L0-th0.2.zarr",
                      name_um=9.362, known_um=9.362),
    "PHerc1447": dict(vol="PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr",
                      pred="PHerc1447/representations/predictions/surfaces/"
                           "20250521151220-surface-20260413222639-surface-m7-L0-th0.2.zarr",
                      name_um=8.640, known_um=8.640),
}
UMB_KEY = "PHerc0826/representations/umbilicus/20250821151701-umbilicus-20260808113303.json"
UMB_LOCAL = "/data/scrollagent/runs/rev1/field-0826-0800/scratch/20250821151701-umbilicus-20260808113303.json"
UMB_REF = "/data/scrollagent/runs/rev1/umbilicus-1447/evidence/reference-0826-summary.csv"
FL_REF = "/data/scrollagent/runs/rev1/first-light-0826-reference/evidence/reference.csv"
SRC = "/data/scrollagent/runs/rev1/seeds-at-scale-1447/scratch/src/build/delivered"

KEY = re.compile(r"<Key>([^<]*)</Key>")
SIZE = re.compile(r"<Size>(\d+)</Size>")
ETAG = re.compile(r"<ETag>&quot;([^&]*)&quot;</ETag>")
NEXT = re.compile(r"<NextContinuationToken>([^<]*)</NextContinuationToken>")

VERDICT = []


def utc():
    return subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()


def get(url, tries=5):
    last = None
    for i in range(tries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                return r
            last = RuntimeError("HTTP %d on %s" % (r.status_code, url))
        except requests.RequestException as exc:
            last = exc
        time.sleep(1 + i)
    raise last


def listing(prefix):
    out, token = [], None
    while True:
        url = "%s/?list-type=2&max-keys=1000&prefix=%s" % (BUCKET, urllib.parse.quote(prefix))
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        body = get(url).text
        out += list(zip(KEY.findall(body), (int(s) for s in SIZE.findall(body)), ETAG.findall(body)))
        m = NEXT.search(body)
        if not m:
            return out
        token = m.group(1)


def write(name, note, cols, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="") as f:
        f.write('"# written by %s at %s: %s"\n' % (TOOL, utc(), note.replace('"', "'")))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])
    return p


def verdict(check, scroll, passes, what, evidence):
    VERDICT.append(dict(check=check, scroll=scroll, passes="yes" if passes else "no", what=what, evidence=evidence))


# ---------------------------------------------------------------------------------------------- I1
def find_key(obj, key, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                yield path + "/" + k, v
            yield from find_key(v, key, path + "/" + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from find_key(v, key, path + "/%d" % i)


def i1():
    rows = []
    for sc, d in SCROLLS.items():
        url = "%s/%s/metadata.json" % (BUCKET, d["vol"])
        md = get(url).json()
        hits = list(find_key(md, "samplePixelSize"))
        vals = sorted({float(v) for _, v in hits})
        meta_um = vals[0] * 1000.0 if len(vals) == 1 else float("nan")
        name_um = float(re.search(r"-([0-9.]+)um-", d["vol"]).group(1))
        man_um, man_src = voxel_um(sc)
        fl = "not quoted for this scroll"
        if sc == "PHerc0826":
            fl = [r for r in csv.DictReader(open(FL_REF)) if r["quantity"] == "voxel_um"][0]["value"]
        cmp = [meta_um, name_um, man_um] + ([float(fl)] if sc == "PHerc0826" else [])
        eq = all(round(x, 4) == round(cmp[0], 4) for x in cmp)
        ref_ok = round(meta_um, 4) == round(d["known_um"], 4)
        rows.append(dict(scroll=sc, metadata_url=url, samplePixelSize_paths=";".join(p for p, _ in hits),
                         samplePixelSize_values_mm=";".join("%g" % v for v in vals),
                         voxel_um_from_metadata="%.4f" % meta_um, voxel_um_in_key_name="%.4f" % name_um,
                         voxel_um_house_manifest="%.4f" % man_um, voxel_um_miller_mueller=fl,
                         all_equal_4_decimals="yes" if eq else "no",
                         equals_known_value="%s (known %.3f)" % ("yes" if ref_ok else "no", d["known_um"]),
                         scanRadix=";".join(str(v) for _, v in find_key(md, "scanRadix"))))
        verdict("I1 voxel", sc, eq and ref_ok, "metadata %.4f um; key name, manifest%s equal to 4 decimals: %s"
                % (meta_um, ", Miller and Mueller" if sc == "PHerc0826" else "", "yes" if eq else "no"),
                "evidence/inputs/i1-voxel.csv")
    # the compiled VOXEL_SIZE of the chain: used anywhere but parameters.h?
    uses = []
    for root, _, files in os.walk(SRC):
        for fn in files:
            if fn.endswith((".cpp", ".h", ".c", ".hpp")) and fn != "parameters.h":
                p = os.path.join(root, fn)
                with open(p, errors="replace") as fh:
                    for n, line in enumerate(fh, 1):
                        if "VOXEL_SIZE" in line:
                            uses.append("%s:%d" % (os.path.relpath(p, SRC), n))
    rows.append(dict(scroll="chain", metadata_url=SRC + "/parameters.h",
                     samplePixelSize_paths="VOXEL_SIZE in compiled sources other than parameters.h",
                     samplePixelSize_values_mm="%d uses: %s" % (len(uses), ";".join(uses) or "none"),
                     all_equal_4_decimals="not applicable",
                     equals_known_value="yes: the chain never reads VOXEL_SIZE" if not uses else "no: read at " + ";".join(uses)))
    verdict("I1 voxel", "chain binary", not uses, "compiled sources reading VOXEL_SIZE besides parameters.h: %d" % len(uses),
            "evidence/inputs/i1-voxel.csv")
    write("i1-voxel.csv", "I1 of DECLARATION.md part 1: samplePixelSize read from the organisers' metadata.json of the "
          "masked volume (mm, converted to um), against the key name, pipeline/datasets manifest and, for 0826, Miller "
          "and Mueller's quote (first-light-0826-reference/evidence/reference.csv); PHerc1447 is the known reference "
          "(8.640). Bar: all equal to 4 decimals and the reference equal to its known value; the last row: VOXEL_SIZE "
          "must be read by no compiled source of the delivered chain but parameters.h",
          ["scroll", "metadata_url", "samplePixelSize_paths", "samplePixelSize_values_mm", "voxel_um_from_metadata",
           "voxel_um_in_key_name", "voxel_um_house_manifest", "voxel_um_miller_mueller", "all_equal_4_decimals",
           "equals_known_value", "scanRadix"], rows)


# ---------------------------------------------------------------------------------------------- I2
def i2():
    rows = []
    for sc, d in SCROLLS.items():
        pub = get("%s/%s/0/.zarray" % (BUCKET, d["pred"])).json()
        loc = json.load(open(os.path.join(DS, sc, "0", ".zarray")))
        raw = get("%s/%s/0/.zarray" % (BUCKET, d["vol"])).json()
        shapes_eq = pub["shape"] == loc["shape"] == raw["shape"]
        pred_ok = (pub["dtype"] == loc["dtype"] == "|u1" and pub["chunks"] == loc["chunks"] == [192, 192, 192]
                   and (pub.get("compressor") or {}).get("id") == "blosc")
        raw_ok = raw["dtype"] == "|u1" and raw.get("compressor") is None and raw.get("order") == "C"
        rows.append(dict(scroll=sc, pred_published_shape=pub["shape"], pred_local_shape=loc["shape"],
                         raw_level0_shape=raw["shape"], shapes_equal="yes" if shapes_eq else "no",
                         pred_dtype=pub["dtype"], pred_chunks=pub["chunks"], pred_compressor=json.dumps(pub["compressor"]),
                         pred_as_the_chain_needs="yes" if pred_ok else "no",
                         raw_dtype=raw["dtype"], raw_chunks=raw["chunks"], raw_compressor=str(raw.get("compressor")),
                         raw_order=raw.get("order"), raw_as_seed_rule_needs="yes" if raw_ok else "no",
                         chain_reads="SIMPAPER_SURFACE_ZARR=%s/%s/0 (prediction level 0, local)" % (DS, sc),
                         seed_rule_reads="%s/%s/0 (raw masked level 0, one chunk per seed, https)" % (BUCKET, d["vol"])))
        verdict("I2 shapes and levels", sc, shapes_eq and pred_ok and raw_ok,
                "shape %s on published and local prediction and raw level 0: %s; prediction uint8 blosc 192: %s; raw uint8 "
                "uncompressed C: %s" % (raw["shape"], "equal" if shapes_eq else "DIFFER", "yes" if pred_ok else "no",
                                        "yes" if raw_ok else "no"), "evidence/inputs/i2-shapes.csv")
    write("i2-shapes.csv", "I2 of DECLARATION.md part 1: the .zarray of the published prediction level 0, the local copy "
          "and the raw masked volume level 0; bar: shapes equal, prediction uint8 blosc 192 cubed, raw uint8 uncompressed C "
          "order (what seeds-at-scale-1447/tools/seed_rule_check.py refuses otherwise); PHerc1447 beside as reference",
          ["scroll", "pred_published_shape", "pred_local_shape", "raw_level0_shape", "shapes_equal", "pred_dtype",
           "pred_chunks", "pred_compressor", "pred_as_the_chain_needs", "raw_dtype", "raw_chunks", "raw_compressor",
           "raw_order", "raw_as_seed_rule_needs", "chain_reads", "seed_rule_reads"], rows)


# ---------------------------------------------------------------------------------------------- I3, I4
def md5_of(args):
    path, = args
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(1 << 22), b""):
                h.update(b)
    except FileNotFoundError:
        return path, "absent", -1
    return path, h.hexdigest(), os.path.getsize(path)


def i3_i4():
    sc = "PHerc0826"
    man = json.load(open(os.path.join(DS, sc, "manifest.json")))
    level0 = SCROLLS[sc]["pred"] + "/0/"
    t0 = time.time()
    lst = [(k, s, e) for k, s, e in listing(level0) if not k.endswith("/.zarray") and not k.endswith("/.zattrs")]
    t_list = time.time() - t0
    text = "".join("%s %d %s\n" % (k[len(level0):], s, e) for k, s, e in sorted(lst, key=lambda t: t[0]))
    sha_now = hashlib.sha256(text.encode()).hexdigest()
    local_txt = open(os.path.join(DS, sc, "chunks.txt")).read()
    sha_local_txt = hashlib.sha256(local_txt.encode()).hexdigest()
    listed = [l.split() for l in local_txt.splitlines() if l.strip()]
    total_now = sum(s for _, s, _ in lst)
    multipart = sum("-" in e for _, _, e in lst)
    rows = [
        dict(quantity="listed_keys_now", value=len(lst), expected=man["published"]["chunks"],
             equal="yes" if len(lst) == man["published"]["chunks"] else "no", what="keys under the level 0 prefix today (.zarray excluded), in %.1f s" % t_list),
        dict(quantity="listed_bytes_now", value=total_now, expected=man["published"]["bytes"],
             equal="yes" if total_now == man["published"]["bytes"] else "no", what="sum of listed sizes"),
        dict(quantity="listing_sha256_now", value=sha_now, expected=man["listing_sha256"],
             equal="yes" if sha_now == man["listing_sha256"] else "no", what="sha256 of the listing text in fetch_prediction.py's form"),
        dict(quantity="chunks_txt_sha256", value=sha_local_txt, expected=man["listing_sha256"],
             equal="yes" if sha_local_txt == man["listing_sha256"] else "no", what="chunks.txt on disk against the manifest"),
        dict(quantity="chunks_txt_lines", value=len(listed), expected=man["published"]["chunks"],
             equal="yes" if len(listed) == man["published"]["chunks"] else "no", what="lines of chunks.txt"),
        dict(quantity="multipart_etags", value=multipart, expected=0, equal="yes" if multipart == 0 else "no",
             what="ETags with a dash are not an md5; any would be compared by size only"),
    ]
    # every listed chunk on disk, size and md5
    root = os.path.join(DS, sc, "0")
    paths = [(os.path.join(root, k),) for k, _, _ in listed]
    t0 = time.time()
    with Pool(WORKERS) as pool:
        got = dict((p, (m, sz)) for p, m, sz in pool.imap_unordered(md5_of, paths, chunksize=64))
    t_md5 = time.time() - t0
    missing = size_diff = md5_diff = 0
    for k, s, e in listed:
        m, sz = got[os.path.join(root, k)]
        if m == "absent":
            missing += 1
        elif sz != int(s):
            size_diff += 1
        elif "-" not in e and m != e:
            md5_diff += 1
    on_disk = set()
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if fn.startswith("."):
                continue
            on_disk.add(os.path.relpath(os.path.join(dp, fn), root))
    not_listed = len(on_disk - {k for k, _, _ in listed})
    rows += [
        dict(quantity="listed_chunks_missing_on_disk", value=missing, expected=0, equal="yes" if missing == 0 else "no", what="listed in chunks.txt, no file"),
        dict(quantity="listed_chunks_size_differs", value=size_diff, expected=0, equal="yes" if size_diff == 0 else "no", what="file size against the listed size"),
        dict(quantity="listed_chunks_md5_differs", value=md5_diff, expected=0, equal="yes" if md5_diff == 0 else "no", what="md5 of the file against the listed ETag, %d files in %.1f s with %d workers" % (len(listed), t_md5, WORKERS)),
        dict(quantity="local_files_not_listed", value=not_listed, expected=0, equal="yes" if not_listed == 0 else "no", what="chunk files on disk that the listing does not name"),
    ]
    # control: a flipped byte must change the md5
    k0, s0, e0 = listed[0]
    cp = os.path.join(TMP, "chain-0826-md5-control.bin")
    b = bytearray(open(os.path.join(root, k0), "rb").read())
    b[len(b) // 2] ^= 0xFF
    open(cp, "wb").write(b)
    _, mc, _ = md5_of((cp,))
    os.remove(cp)
    rows.append(dict(quantity="control_flipped_byte_md5_differs", value="yes" if mc != e0 else "no", expected="yes",
                     equal="yes" if mc != e0 else "no", what="chunk %s with one byte flipped in a copy under /data/tmp: the md5 test can fail" % k0))
    # grid cells not listed: fill 0, «not measurable» for the chain
    shp, ch = man["shape"], man["chunks"]
    grid = [-(-a // c) for a, c in zip(shp, ch)]
    ncell = grid[0] * grid[1] * grid[2]
    rows.append(dict(quantity="grid_cells_not_listed", value=ncell - len(listed), expected="written, not judged",
                     equal="not applicable", what="grid %s = %d cells, %d listed; an unlisted cell reads the fill value 0" % ("x".join(map(str, grid)), ncell, len(listed))))
    ok3 = all(r["equal"] in ("yes", "not applicable") for r in rows)
    write("i3-manifest.csv", "I3 of DECLARATION.md part 1 on PHerc0826: the bucket's listing of the prediction level 0 taken again "
          "now against manifest.json and chunks.txt, then every listed chunk on disk by size and md5 against its ETag; a control "
          "with a flipped byte must change the md5. Bar: every row equal", ["quantity", "value", "expected", "equal", "what"], rows)
    verdict("I3 manifest", sc, ok3, "listing today %d keys, sha %s the manifest's; missing %d, size %d, md5 %d, unlisted %d; control %s"
            % (len(lst), "equal to" if sha_now == man["listing_sha256"] else "DIFFERENT from", missing, size_diff, md5_diff, not_listed,
               "can fail" if mc != e0 else "FAILED"), "evidence/inputs/i3-manifest.csv")

    # I4 decode
    rng = np.random.default_rng(20260926)
    pick = rng.choice(len(listed), size=400, replace=False)
    Z = zarr.open(root, mode="r")
    rows4, good = [], 0
    for i in sorted(pick):
        k = listed[i][0]
        cz, cy, cx = (int(v) for v in k.split("/"))
        sl = tuple(slice(c * n, min((c + 1) * n, a)) for c, n, a in zip((cz, cy, cx), ch, shp))
        want = tuple(s.stop - s.start for s in sl)
        try:
            blk = np.asarray(Z[sl])
            ok = blk.shape == want and blk.dtype == np.uint8
            n255 = int((blk == 255).sum())
            err = ""
        except Exception as exc:  # noqa: BLE001 - a failing decode is the row
            ok, n255, err = False, "not measurable", repr(exc)[:120]
        good += ok
        rows4.append(dict(chunk=k, shape_expected="x".join(map(str, want)), decoded="yes" if ok else "no",
                          voxels_255=n255, error=err))
    # control: a truncated copy must not decode
    import numcodecs
    comp = numcodecs.get_codec(man["published"]["compressor"])
    raw_bytes = open(os.path.join(root, listed[int(pick[0])][0]), "rb").read()
    try:
        comp.decode(raw_bytes[: len(raw_bytes) // 2])
        ctl = "decoded: the control did not fail"
    except Exception:  # noqa: BLE001
        ctl = "refused"
    rows4.append(dict(chunk="control_truncated_half_of_" + listed[int(pick[0])][0], shape_expected="not applicable",
                      decoded="no" if ctl == "refused" else "yes", voxels_255="not measurable", error=ctl))
    write("i4-decode.csv", "I4 of DECLARATION.md part 1: 400 listed chunks drawn with default_rng(20260926) decoded by zarr "
          "from the local level 0; the last row is a control, half of a chunk's bytes, which must not decode. Bar: 400 of 400 "
          "and the control refused", ["chunk", "shape_expected", "decoded", "voxels_255", "error"], rows4)
    verdict("I4 decode", sc, good == 400 and ctl == "refused", "%d of 400 decoded; truncated control %s" % (good, ctl),
            "evidence/inputs/i4-decode.csv")
    return listed, grid


# ---------------------------------------------------------------------------------------------- I5, I6
def level5(url_zarr, cache):
    meta = get(url_zarr + "/5/.zarray").json()
    shp, ch = meta["shape"], meta["chunks"]
    comp = meta.get("compressor")
    import numcodecs
    codec = numcodecs.get_codec(comp) if comp else None
    out = np.zeros(shp, dtype=np.uint8)
    sep = meta.get("dimension_separator", ".")
    os.makedirs(cache, exist_ok=True)
    for cz in range(-(-shp[0] // ch[0])):
        for cy in range(-(-shp[1] // ch[1])):
            for cx in range(-(-shp[2] // ch[2])):
                key = sep.join(map(str, (cz, cy, cx)))
                fp = os.path.join(cache, key.replace("/", "_"))
                if not os.path.exists(fp):
                    r = requests.get("%s/5/%s" % (url_zarr, key), timeout=120)
                    if r.status_code == 404:
                        open(fp + ".absent", "w").close() if not os.path.exists(fp + ".absent") else None
                        continue
                    r.raise_for_status()
                    open(fp, "wb").write(r.content)
                data = open(fp, "rb").read()
                arr = np.frombuffer(codec.decode(data) if codec else data, dtype=np.uint8).reshape(ch)
                z0, y0, x0 = cz * ch[0], cy * ch[1], cx * ch[2]
                dz, dy, dx = min(ch[0], shp[0] - z0), min(ch[1], shp[1] - y0), min(ch[2], shp[2] - x0)
                out[z0:z0 + dz, y0:y0 + dy, x0:x0 + dx] = arr[:dz, :dy, :dx]
    return out, meta


def i5_i6(listed0826):
    rows, masks = [], {}
    for sc, d in SCROLLS.items():
        raw5, _ = level5("%s/%s" % (BUCKET, d["vol"]), os.path.join(S, "scratch", "level5", sc, "raw"))
        pr5, _ = level5("%s/%s" % (BUCKET, d["pred"]), os.path.join(S, "scratch", "level5", sc, "pred"))
        mask = raw5 > 0
        masks[sc] = mask
        pred = pr5 > 0
        n = int(pred.sum())
        in_mask = float((pred & mask).sum()) / n if n else float("nan")
        sw = np.swapaxes(pred, 1, 2)
        in_mask_sw = float((sw & mask).sum()) / n if n else float("nan")
        # listed level 0 chunks (192) against the mask at level 5 (scale 32): one chunk = 6 level 5 voxels
        if sc == "PHerc0826":
            keys = [l[0] for l in listed0826]
        else:
            keys = [l.split()[0] for l in open(os.path.join(DS, sc, "chunks.txt")) if l.strip()]
        lg = np.zeros(mask.shape, dtype=bool)
        for k in keys:
            cz, cy, cx = (int(v) for v in k.split("/"))
            lg[cz * 6:(cz + 1) * 6, cy * 6:(cy + 1) * 6, cx * 6:(cx + 1) * 6] = True
        mcount = int(mask.sum())
        cov = float((mask & lg).sum()) / mcount if mcount else float("nan")
        zs_m = np.where(mask.any(axis=(1, 2)))[0]
        zs_l = np.where(lg.any(axis=(1, 2)))[0]
        zs_p = np.where(pred.any(axis=(1, 2)))[0]
        ok = in_mask >= 0.95 and in_mask_sw <= in_mask - 0.20 and cov >= 0.90
        rows.append(dict(scroll=sc, level5_shape="x".join(map(str, raw5.shape)), mask_voxels=mcount,
                         predicted_voxels=n, predicted_in_mask_share="%.4f" % in_mask,
                         predicted_in_mask_share_swapped_xy="%.4f" % in_mask_sw,
                         mask_under_listed_chunks_share="%.4f" % cov,
                         mask_z_range_level0="%d..%d" % (zs_m[0] * 32, zs_m[-1] * 32 + 31),
                         predicted_z_range_level0="%d..%d" % (zs_p[0] * 32, zs_p[-1] * 32 + 31),
                         listed_chunks_z_range_level0="%d..%d" % (zs_l[0] * 32, min(zs_l[-1] * 32 + 31, raw5.shape[0] * 32 - 1)),
                         listed_chunks=len(keys), passes="yes" if ok else "no"))
        verdict("I5 coverage", sc, ok, "predicted in mask %.4f (swapped %.4f); mask under listed chunks %.4f"
                % (in_mask, in_mask_sw, cov), "evidence/inputs/i5-coverage.csv")
        np.save(os.path.join(S, "scratch", "level5", sc, "mask.npy"), mask)
    write("i5-coverage.csv", "I5 of DECLARATION.md part 1: raw masked level 5 and prediction level 5 fetched whole from the bucket "
          "(scale 32); mask = raw above 0; bar: predicted in mask at least 0.95, the swapped x/y frame at least 0.20 lower, "
          "listed level 0 chunks cover at least 0.90 of the mask; PHerc1447 is the reference that must pass",
          ["scroll", "level5_shape", "mask_voxels", "predicted_voxels", "predicted_in_mask_share",
           "predicted_in_mask_share_swapped_xy", "mask_under_listed_chunks_share", "mask_z_range_level0",
           "predicted_z_range_level0", "listed_chunks_z_range_level0", "listed_chunks", "passes"], rows)

    # I6 the umbilicus
    r = get("%s/%s" % (BUCKET, UMB_KEY))
    body = r.content
    lm = r.headers.get("Last-Modified", "not returned")
    sha_now = hashlib.sha256(body).hexdigest()
    sha_loc = hashlib.sha256(open(UMB_LOCAL, "rb").read()).hexdigest()
    pts = json.loads(body)["control_points"]
    xs = np.array([p["x"] for p in pts]); ys = np.array([p["y"] for p in pts]); zs = np.array([p["z"] for p in pts])
    shp = [16920, 8169, 8169]
    inside = int(((zs >= 0) & (zs < shp[0]) & (ys >= 0) & (ys < shp[1]) & (xs >= 0) & (xs < shp[2])).sum())
    incr = bool(np.all(np.diff(zs) > 0))
    mask = masks["PHerc0826"]
    # in the mask slice at level 5; «filled» = inside the slice's filled outline (holes of the mask closed per slice)
    from scipy import ndimage
    def share(xx, yy):
        hit = fill = 0
        for x, y, z in zip(xx, yy, zs):
            k = min(int(z) // 32, mask.shape[0] - 1)
            sl = mask[k]
            yi, xi = min(int(y) // 32, sl.shape[0] - 1), min(int(x) // 32, sl.shape[1] - 1)
            hit += bool(sl[yi, xi])
            fill += bool(ndimage.binary_fill_holes(sl)[yi, xi])
        return hit / len(xx), fill / len(xx)
    in_r, fill_r = share(xs, ys)
    in_s, fill_s = share(ys, xs)
    fl = {q["quantity"]: q["value"] for q in csv.DictReader(open(FL_REF))}
    fl_txt = fl.get("umbilicus_points_z_range", "")
    fl_n = int(re.search(r"(\d+)\s*pts", fl_txt).group(1))
    fl_z = [int(v) for v in re.search(r"z\s*(\d+)\D+(\d+)", fl_txt).groups()]
    ref = list(csv.reader([l for l in open(UMB_REF) if not l.startswith('"#') and not l.startswith("#")]))
    ref_txt = "; ".join("%s=%s" % (h, v) for h, v in zip(ref[0], ref[1])) if len(ref) > 1 else "not read"
    zm = np.where(mask.any(axis=(1, 2)))[0]
    band = (max(int(zs.min()), int(zm[0] * 32)), min(int(zs.max()), int(zm[-1] * 32 + 31)))
    rows6 = [
        dict(quantity="sha256_now_equals_copy_of_2026_09_24", value=sha_now[:16], expected=sha_loc[:16], equal="yes" if sha_now == sha_loc else "no"),
        dict(quantity="last_modified", value=lm, expected="published 2026-09-03 (director's note)", equal="yes" if "03 Sep 2026" in lm else "no"),
        dict(quantity="points", value=len(pts), expected=fl_n, equal="yes" if len(pts) == fl_n else "no"),
        dict(quantity="z_range", value="%d..%d" % (zs.min(), zs.max()), expected="%d..%d" % tuple(fl_z),
             equal="yes" if [int(zs.min()), int(zs.max())] == fl_z else "no"),
        dict(quantity="points_inside_volume", value=inside, expected=len(pts), equal="yes" if inside == len(pts) else "no"),
        dict(quantity="z_strictly_increasing", value="yes" if incr else "no", expected="yes", equal="yes" if incr else "no"),
        dict(quantity="in_mask_slice_share_right_frame", value="%.4f" % in_r, expected=">= 0.90", equal="yes" if in_r >= 0.90 else "no"),
        dict(quantity="in_mask_slice_share_swapped_xy", value="%.4f" % in_s, expected="lower than the right frame", equal="yes" if in_s < in_r else "no"),
        dict(quantity="in_filled_mask_slice_share_right_frame", value="%.4f" % fill_r, expected="information (holes of the slice closed)", equal="not applicable"),
        dict(quantity="in_filled_mask_slice_share_swapped_xy", value="%.4f" % fill_s, expected="information", equal="not applicable"),
        dict(quantity="seed_z_band_level0", value="%d..%d" % band, expected="umbilicus z range within the mask z range", equal="not applicable"),
        dict(quantity="house_estimator_against_it", value=ref_txt[:300], expected="read back from umbilicus-1447/evidence/reference-0826-summary.csv", equal="not applicable"),
    ]
    ok6 = all(x["equal"] in ("yes", "not applicable") for x in rows6)
    write("i6-umbilicus.csv", "I6 of DECLARATION.md part 1: the published 0826 umbilicus fetched again (%s), against the copy of "
          "2026-09-24, Miller and Mueller's quote (first-light-0826-reference) and the raw mask at level 5 in both frames" % UMB_KEY,
          ["quantity", "value", "expected", "equal"], rows6)
    verdict("I6 umbilicus", "PHerc0826", ok6, "%d points z %d..%d, sha %s; in mask slice %.4f right, %.4f swapped"
            % (len(pts), zs.min(), zs.max(), "equal" if sha_now == sha_loc else "DIFFERENT", in_r, in_s),
            "evidence/inputs/i6-umbilicus.csv")


def main():
    os.makedirs(OUT, exist_ok=True)
    os.environ.setdefault("TMPDIR", TMP)
    t0 = time.time()
    i1(); print("I1 done %.0f s" % (time.time() - t0), flush=True)
    i2(); print("I2 done %.0f s" % (time.time() - t0), flush=True)
    listed, _ = i3_i4(); print("I3 I4 done %.0f s" % (time.time() - t0), flush=True)
    i5_i6(listed); print("I5 I6 done %.0f s" % (time.time() - t0), flush=True)
    allok = all(v["passes"] == "yes" for v in VERDICT)
    VERDICT.append(dict(check="overall", scroll="PHerc0826", passes="yes" if allok else "no",
                        what="inputs hold" if allok else "inputs do not hold: " + "; ".join(
                            "%s %s" % (v["check"], v["scroll"]) for v in VERDICT if v["passes"] != "yes"),
                        evidence="evidence/inputs/"))
    write("verdict.csv", "verdict of DECLARATION.md part 1: one row per check and scroll, then overall; «inputs hold» only if "
          "every row passes, the PHerc1447 reference rows included", ["check", "scroll", "passes", "what", "evidence"], VERDICT)
    for v in VERDICT:
        print(v["check"], v["scroll"], v["passes"], v["what"])


if __name__ == "__main__":
    main()
