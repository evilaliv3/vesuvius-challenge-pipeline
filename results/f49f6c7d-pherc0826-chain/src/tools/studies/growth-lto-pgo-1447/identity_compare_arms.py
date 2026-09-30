#!/usr/bin/env python3
"""identity_compare_arms.py <arm> [<seed> ...]: growth-lto-pgo-1447 bar 1 (DECLARATION.md addition of
2026-09-27T06:49:40Z). The comparison part of chain-0826/tools/identity_0826_v2.sh and the reading of
chain-0826/tools/identity_summary.py, for arm MN or MLP against unchanged, on this study's scratch/identity trees.

Per seed: growth-memory-1447/tools/tree_identity.py growth (patches/ and rel.csv) and sheets (C40 patch_<n>.bin), and the
sha256 of the C40 stage files of patch-filter-harness-1447's identity_compare.py STAGE_FILES. Rows (chain-0826's columns)
to evidence/identity-0826-<arm lower>.csv, per file rows to evidence/identity-0826-<arm>-<seed>-growth.csv / -sheets.csv.
Reading as identity_summary.py: crashed on both builds = «not measurable, crashed on both builds (replaced)»; yes only with
at least three measurable seeds holding and none failing or otherwise not measurable. The summary
evidence/identity-0826-summary.csv holds one row per arm compared so far (chain-0826's columns: build first,
identity_holds last); a ledger row.
"""
import csv
import hashlib
import os
import subprocess
import sys

M = "/data/scrollagent/runs/rev1/growth-lto-pgo-1447"
TI = "/data/scrollagent/runs/rev1/growth-memory-1447/tools/tree_identity.py"
TOOL = "growth-lto-pgo-1447/tools/identity_compare_arms.py"
SF = "badpatches.csv badpatchscores.csv patchVolCoords.csv alignmentorders.txt neighbourss.csv badbridgess_out.csv patchorder.csv patchorders.csv".split()
BUILD = {"MN": "flathash+avx512 -march=native (MN)", "MLP": "flathash+avx512 -march=native -flto=auto PGO (MLP)"}
NEED = 3


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def res(arm, a):
    p = "%s/scratch/identity/%s/%s/RESULT" % (M, arm, a)
    return open(p).read().strip() if os.path.exists(p) else "absent"


def crashed(x):
    return x.startswith("growth ") and not x.startswith("growth 0")


def utc():
    return subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()


def main():
    arm = sys.argv[1]
    if arm not in BUILD:
        raise SystemExit(__doc__)
    seeds = sys.argv[2:] or ["PHerc0826-seed109", "PHerc0826-seed300", "PHerc0826-seed237"]
    rows = []
    for a in seeds:
        rv, ru = res(arm, a), res("unchanged", a)
        row = dict(seed=a, variant_result=rv.replace(",", ";"), unchanged_result=ru.replace(",", ";"))
        if not (rv.startswith("0 ") and ru.startswith("0 ")):
            row.update(growth_identity="not measurable", sheets_identity="not measurable", stage_files_identity="not measurable",
                       holds="not measurable (a run did not finish: %s / %s)" % (rv.split()[0], ru.split()[0]))
        else:
            du, dv = "%s/scratch/identity/unchanged/%s" % (M, a), "%s/scratch/identity/%s/%s" % (M, arm, a)
            out = {}
            for kind, sub in (("growth", "growth"), ("sheets", "C40")):
                dest = "%s/evidence/identity-0826-%s-%s-%s.csv" % (M, arm, a, kind)
                p = subprocess.run([sys.executable, TI, "%s/%s" % (du, sub), "%s/%s" % (dv, sub), dest, kind],
                                   capture_output=True, text=True)
                out[kind] = (p.stdout.strip().splitlines() or ["no output rc %d" % p.returncode])[-1]
                out[kind + "_rc"] = p.returncode
            eq = n = 0
            miss = []
            for f in SF:
                pu, pv = os.path.join(du, "C40", f), os.path.join(dv, "C40", f)
                if not os.path.exists(pu) and not os.path.exists(pv):
                    continue
                n += 1
                if os.path.exists(pu) and os.path.exists(pv) and sha(pu) == sha(pv):
                    eq += 1
                else:
                    miss.append(f)
            sf = "identical %d of %d" % (eq, n) if eq == n else "differs %s" % ";".join(miss)
            ok = out["growth_rc"] == 0 and out["sheets_rc"] == 0 and eq == n and n > 0
            row.update(growth_identity=out["growth"].replace(",", ";"), sheets_identity=out["sheets"].replace(",", ";"),
                       stage_files_identity=sf, holds="yes" if ok else "no")
        if crashed(row["variant_result"]) and crashed(row["unchanged_result"]):
            row["reading"] = "not measurable, crashed on both builds (replaced)"
        elif row["holds"] == "yes":
            row["reading"] = "holds"
        elif row["holds"] == "no":
            row["reading"] = "fails"
        else:
            row["reading"] = "not measurable (%s)" % row["holds"]
        rows.append(row)
    t = utc()
    cols = ["seed", "variant_result", "unchanged_result", "growth_identity", "sheets_identity", "stage_files_identity",
            "holds", "reading"]
    with open("%s/evidence/identity-0826-%s.csv" % (M, arm.lower()), "w", newline="") as f:
        f.write('"# written by %s at %s: %s against unchanged, per seed, chain-0826 settings environment (cap 512, F3); growth and sheets by growth-memory-1447/tools/tree_identity.py, stage files by sha256; reading as chain-0826/tools/identity_summary.py"\n' % (TOOL, t, arm))
        w = csv.DictWriter(f, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    hold = [r["seed"] for r in rows if r["reading"] == "holds"]
    bad = [r["seed"] for r in rows if r["reading"] == "fails" or r["reading"].startswith("not measurable (")]
    repl = [r["seed"] for r in rows if r["reading"].startswith("not measurable, crashed")]
    verdict = "yes" if len(hold) >= NEED and not bad else "no"
    sp = M + "/evidence/identity-0826-summary.csv"
    keep = []
    if os.path.exists(sp):
        keep = [r for r in csv.reader(l for l in open(sp) if not l.startswith("#")) if r and r[0] not in ("build", BUILD[arm])]
    with open(sp, "w", newline="") as f:
        f.write("# written by %s at %s: one row per arm, chain-0826/evidence/identity-0826-summary.csv's columns; yes only "
                "with at least %d measurable seeds holding and none failing\n" % (TOOL, t, NEED))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["build", "against", "seeds_holding", "seeds_failing_or_not_measurable", "seeds_replaced", "evidence", "identity_holds"])
        w.writerows(keep)
        w.writerow([BUILD[arm], "unchanged", ";".join(hold), ";".join(bad) or "none", ";".join(repl) or "none",
                    "evidence/identity-0826-%s.csv" % arm.lower(), verdict])
    with open("/data/scrollagent/ledger/ledger.csv", "a", newline="") as f:
        csv.writer(f).writerow([t, "rev1", "coordinator-agent", "growth-lto-pgo-1447-identity-%s" % arm.lower(),
                                "G6-style identity on 0826, %s against unchanged (chain settings, cap 512, F3): holding %s, failing or not measurable %s, replaced %s: identity_holds %s; per seed %s"
                                % (arm, ";".join(hold) or "none", ";".join(bad) or "none", ";".join(repl) or "none", verdict,
                                   " | ".join("%s %s/%s/%s" % (r["seed"], r["growth_identity"], r["sheets_identity"], r["stage_files_identity"]) for r in rows)),
                                TOOL, "", "", "0", "runs/rev1/growth-lto-pgo-1447/evidence/identity-0826-%s.csv; runs/rev1/growth-lto-pgo-1447/evidence/identity-0826-summary.csv" % arm.lower()])
    for r in rows:
        print(r["seed"], r["variant_result"], "|", r["unchanged_result"], "|", r["growth_identity"], "|", r["sheets_identity"],
              "|", r["stage_files_identity"], "|", r["reading"])
    print(arm, "identity_holds", verdict)


if __name__ == "__main__":
    main()
