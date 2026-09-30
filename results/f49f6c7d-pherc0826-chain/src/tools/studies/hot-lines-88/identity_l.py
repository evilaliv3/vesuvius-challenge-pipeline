"""identity_l.py <copy tag> <copy root> <codec code>: hot-lines-88 (DECLARATION.md, B, «Identity»).
codec-z-0826/tools/identity.py (second version) with only these changes: the copy root, the tag in the evidence names
(evidence/identity-<tag>.csv, identity-<tag>-summary.csv, scratch/<tag>-chunks.txt), the expected codec code in the
blosc2 extended header byte 22 (1 lz4, 2 lz4hc; 5 zstd there) and blosc2_cbuffer_complib's name recorded, and the
.zarray keys allowed to differ (compressor.cname, compressor.clevel, compressor.shuffle). Independent of the recoder:
the source decoded by numcodecs (c-blosc 1), the copy by /data/opt/blosc2/lib/libblosc2.so through ctypes; every chunk
of the union of the three lists (source files, copy files, manifest), 7077888 bytes each and byte identical. Six
processes at nice 10."""
import csv, ctypes, datetime, hashlib, json, os, sys
from multiprocessing import Pool
from numcodecs import Blosc

LIB = "/data/opt/blosc2/lib/libblosc2.so"
H = "/data/scrollagent/runs/rev1/hot-lines-88"
SRC = "/data/scrollagent/data/datasets/PHerc0826/0"
MAN = "/data/scrollagent/data/datasets/PHerc0826/chunks.txt"
TOOL = "hot-lines-88/tools/identity_l.py"
CB = 192 ** 3
BL = Blosc()
TAG, DST, CODE = sys.argv[1], sys.argv[2], int(sys.argv[3])
_b2 = None


def lib():
    global _b2
    if _b2 is None:
        _b2 = ctypes.CDLL(LIB); _b2.blosc2_init()
        _b2.blosc2_decompress.argtypes = [ctypes.c_char_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_int32]
        _b2.blosc2_decompress.restype = ctypes.c_int
        _b2.blosc2_cbuffer_complib.argtypes = [ctypes.c_char_p]
        _b2.blosc2_cbuffer_complib.restype = ctypes.c_char_p
    return _b2


def b2decode(buf):
    out = ctypes.create_string_buffer(CB)
    n = lib().blosc2_decompress(buf, len(buf), out, CB)
    if n < 0: raise RuntimeError(f"blosc2_decompress {n}")
    return out.raw[:n]


def files(root):
    out = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if not f.startswith(".z"):
                out.append(os.path.relpath(os.path.join(d, f), root))
    return sorted(out)


def one(c):
    r = {"chunk": c}
    a = b = None
    try:
        sa = open(f"{SRC}/{c}", "rb").read(); r["src_bytes"] = len(sa); r["src_md5"] = hashlib.md5(sa).hexdigest()
        a = bytes(BL.decode(sa)); r["src_decoded"] = len(a)
    except Exception as e:
        r["error"] = f"src {type(e).__name__}"
    try:
        sb = open(f"{DST}/{c}", "rb").read(); r["copy_bytes"] = len(sb); r["copy_md5"] = hashlib.md5(sb).hexdigest()
        r["copy_version"] = sb[0]; r["copy_filters"] = "".join(str(x) for x in sb[16:22]); r["copy_codec_code"] = sb[22]
        r["copy_complib"] = lib().blosc2_cbuffer_complib(sb).decode()
        b = b2decode(sb); r["copy_decoded"] = len(b)
    except Exception as e:
        r["error"] = (r.get("error", "") + f" copy {type(e).__name__}").strip()
    r["equal"] = "yes" if a is not None and b is not None and len(a) == CB and a == b else "no"
    return r


def main():
    os.nice(10)
    now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = now()
    man = {}
    for l in open(MAN):
        p = l.split()
        if p: man[p[0]] = (int(p[1]), p[2])
    ls, ld, lm = files(SRC), files(DST), sorted(man)
    sha = lambda L: hashlib.sha256("\n".join(L).encode()).hexdigest()
    union = sorted(set(ls) | set(ld) | set(lm))
    with Pool(6) as pool:
        rows = pool.map(one, union, chunksize=64)
    cols = ["chunk", "src_bytes", "copy_bytes", "src_decoded", "copy_decoded", "src_md5_matches_manifest", "copy_version",
            "copy_filters", "copy_codec_code", "copy_complib", "equal", "error"]
    bad_md5 = 0
    with open(f"{H}/evidence/identity-{TAG}.csv", "w", newline="") as f:
        f.write(f"# written by {TOOL}, started {t0}; source decoded by numcodecs Blosc, copy by {LIB} (ctypes), not by the recoder\n")
        w = csv.writer(f, lineterminator="\n"); w.writerow(cols)
        for r in rows:
            m = man.get(r["chunk"])
            mm = "not listed" if m is None else ("yes" if r.get("src_md5") == m[1] and r.get("src_bytes") == m[0] else "no")
            bad_md5 += mm != "yes"
            r["src_md5_matches_manifest"] = mm
            w.writerow([r.get(k, "") for k in cols])
    cm = f"{H}/scratch/{TAG}-chunks.txt"
    with open(cm, "w") as f:
        for r in rows:
            if "copy_md5" in r: f.write(f"{r['chunk']} {r['copy_bytes']} {r['copy_md5']}\n")
    za, zb = json.load(open(f"{SRC}/.zarray")), json.load(open(f"{DST}/.zarray"))
    diff = []
    for k in sorted(set(za) | set(zb)):
        if za.get(k) != zb.get(k):
            if k == "compressor":
                diff += [f"compressor.{kk}" for kk in sorted(set(za[k]) | set(zb[k])) if za[k].get(kk) != zb[k].get(kk)]
            else:
                diff.append(k)
    allowed = {"compressor.cname", "compressor.clevel", "compressor.shuffle"}
    eq = sum(r["equal"] == "yes" for r in rows)
    filt = sum(r.get("copy_filters") != "000000" for r in rows)
    code = sum(r.get("copy_codec_code") == CODE for r in rows)
    v5 = sum(r.get("copy_version") == 5 for r in rows)
    libs = sorted(set(r.get("copy_complib", "") for r in rows))
    cbytes = sum(r.get("copy_bytes", 0) for r in rows); sbytes = sum(r.get("src_bytes", 0) for r in rows)
    ok = (ls == ld == lm and eq == len(union) and bad_md5 == 0 and set(diff) <= allowed and filt == 0 and code == len(union))
    verdict = "identical" if ok else "NOT identical"
    with open(f"{H}/evidence/identity-{TAG}-summary.csv", "w", newline="") as f:
        f.write(f"# written by {TOOL} from {t0} to {now()}\n")
        w = csv.writer(f, lineterminator="\n"); w.writerow(["quantity", "value", "note"])
        for r in (("manifest_chunks", len(lm), MAN),
                  ("source_chunk_files", len(ls), SRC),
                  ("copy_chunk_files", len(ld), DST),
                  ("lists_equal", "yes" if ls == ld == lm else "no", "source files, copy files and manifest, sorted"),
                  ("sha256_manifest_list", sha(lm), "sorted first column, newline joined"),
                  ("sha256_source_list", sha(ls), "sorted chunk paths, newline joined"),
                  ("sha256_copy_list", sha(ld), "sorted chunk paths, newline joined"),
                  ("sha256_copy_manifest_file", hashlib.sha256(open(cm, "rb").read()).hexdigest(), f"scratch/{TAG}-chunks.txt"),
                  ("chunks_checked", len(union), "union of the three lists"),
                  ("decoded_byte_identical", eq, f"both decoded to {CB} bytes and equal; source by numcodecs (c-blosc 1), copy by {LIB} (ctypes)"),
                  ("differing_or_error", len(union) - eq, ""),
                  ("source_md5_not_matching_manifest", bad_md5, "manifest column 3 against the source file"),
                  ("copy_chunks_with_a_filter", filt, "blosc2 extended header bytes 16 to 21 not all 0"),
                  ("copy_chunks_codec_code_%d" % CODE, code, "blosc2 extended header byte 22 == %d" % CODE),
                  ("copy_complib", " ".join(libs), "blosc2_cbuffer_complib over all chunks"),
                  ("copy_chunks_blosc2_format", v5, "header byte 0 == 5"),
                  ("zarray_keys_differing", " ".join(diff) or "none", "allowed: " + " ".join(sorted(allowed))),
                  ("source_bytes", sbytes, "sum of file sizes"),
                  ("copy_bytes", cbytes, "sum of file sizes"),
                  ("copy_over_source", f"{cbytes / sbytes:.6f}" if sbytes else "", ""),
                  ("verdict", verdict, "lists equal, every chunk identical, md5 all match, only codec keys differ in .zarray, no filter, codec code as expected in every chunk")):
            w.writerow(r)
    print(open(f"{H}/evidence/identity-{TAG}-summary.csv").read())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
