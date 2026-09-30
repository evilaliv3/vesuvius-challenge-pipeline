#!/usr/bin/env python3
"""build_objects_check.py <path of the build_variant_seed.py to check> [variant ...]

chain-0826 (DECLARATION.md addition of 2026-09-26, director 16:17:03Z): checks the one object per seed build against the
full per seed build, for every variant (default unchanged, flathash, flathash+avx512), on the first four seeds of
evidence/seeds-PHerc0826-draw400.csv. The tool under check is imported unchanged; its S and SRC are pointed at
scratch/objects-check/ so the chain's own tree, stocks and bins are never touched. Per variant: lay_down (the tree, the
pinned patches, the stock and the known 1447 seed1111 reference, all its own gates), then per seed the chain's build
(mode auto) and, in the same tree right after, a forced full build; the two sha256 must be equal. The first seed of a
variant is expected full (the base for 0826's shape), the next three objects_only. Writes
evidence/build-objects-check.csv and exits 1 unless every variant has at least three objects_only seeds equal to full and
no row differs. nice 10 (the make lines carry it), make -j4.
"""
import csv, hashlib, importlib.util, os, shutil, sys

S = "/data/scrollagent/runs/rev1/chain-0826"
TOOL = "chain-0826/tools/build_objects_check.py"
OUT = S + "/evidence/build-objects-check.csv"
DRAW = S + "/evidence/seeds-PHerc0826-draw400.csv"
CK = S + "/scratch/objects-check"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    path = sys.argv[1]
    variants = sys.argv[2:] or ["unchanged", "flathash", "flathash+avx512"]
    spec = importlib.util.spec_from_file_location("bvs", path)
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
    shutil.rmtree(CK, ignore_errors=True); os.makedirs(CK + "/log"); os.makedirs(CK + "/scratch")
    B.S, B.SRC = CK, CK + "/src"
    L = [l for l in open(DRAW) if not l.lstrip('"').startswith("#")]
    seeds = list(csv.DictReader(L))[:4]
    rows, ok = [], True
    for v in variants:
        with open(CK + "/gate-%s.csv" % v.replace("+", "-"), "w", newline="") as g:
            w = csv.writer(g)
            build, stock = B.lay_down(v, w)
        gate = open(CK + "/gate-%s.csv" % v.replace("+", "-")).read()
        ref_ok = "reference_build_equals_known" in gate and ",no," not in gate
        n_obj = 0
        for r in seeds:
            a = r["attempt"]
            log = CK + "/log/%s-%s.txt" % (v.replace("+", "-"), a)
            p = B.make_for(build, B.SCROLL, r, log)
            mode, why = list(B.LAST_MODE)
            s_auto = sha(p)
            p = B.make_for(build, B.SCROLL, r, log, mode="full")
            s_full = sha(p)
            eq = s_auto == s_full
            ok &= eq
            n_obj += eq and mode == "objects_only"
            rows.append([TOOL, v, a, mode, why, s_auto, s_full, "yes" if eq else "no", "yes" if s_full != stock else "no",
                         "yes" if ref_ok else "no", sha(path)])
            print(v, a, mode, s_auto[:12], s_full[:12], "equal" if eq else "DIFFERS", flush=True)
        ok &= ref_ok and n_obj >= 3
    with open(OUT, "w", newline="") as f:
        f.write('"# written by %s: per variant and seed, the build of the tool under check (mode auto) against a full '
                'make of the same seed in the same tree; tree in scratch/objects-check, never the chain\'s"\n' % TOOL)
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["tool", "variant", "attempt", "build_mode", "mode_reason", "sha256_build", "sha256_full_build",
                    "equal", "differs_from_stock", "tree_gates_pass", "sha256_of_tool_checked"])
        w.writerows(rows)
    print("verdict:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
