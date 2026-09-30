#!/usr/bin/env python3
"""identity_compare_runtime.py: runtime-params-96's bar (DECLARATION.md, «Bar»). growth-lto-pgo-1447/tools/
identity_compare_arms.py's comparison and reading, for arm runtime against arm perseed (the per seed MLP binaries),
on this study's scratch/identity trees, plus one check: the runtime arm's growth log carries «Seed at run time: x y z
(environment)» with the draw row's x y z.

Per seed: growth-memory-1447/tools/tree_identity.py growth (patches/ and rel.csv) and sheets (C40 patch_<n>.bin), and
the sha256 of the C40 stage files of patch-filter-harness-1447's identity_compare.py STAGE_FILES. Rows to
evidence/identity-0826-runtime.csv, per file rows to evidence/identity-0826-runtime-<seed>-growth.csv / -sheets.csv.
Summary evidence/identity-summary.csv in chain-0826/evidence/identity-0826-summary.csv's columns (build first,
identity_holds last): yes only with all three seeds holding. A ledger row.
"""
import csv
import hashlib
import os
import re
import subprocess
import sys

P = "/data/scrollagent/runs/rev1/runtime-params-96"
TI = "/data/scrollagent/runs/rev1/growth-memory-1447/tools/tree_identity.py"
DRAW = "/data/scrollagent/runs/rev1/chain-0826/evidence/seeds-PHerc0826-draw400.csv"
TOOL = "runtime-params-96/tools/identity_compare_runtime.py"
SF = "badpatches.csv badpatchscores.csv patchVolCoords.csv alignmentorders.txt neighbourss.csv badbridgess_out.csv patchorder.csv patchorders.csv".split()
BUILD = "flathash+avx512+lto+pgo+native+runtime-seed"
AGAINST = "flathash+avx512+lto+pgo+native (per seed MLP binaries)"
SEEDS = ["PHerc0826-seed109", "PHerc0826-seed300", "PHerc0826-seed237"]
NEED = 3


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def res(arm, a):
    p = "%s/scratch/identity/%s/%s/RESULT" % (P, arm, a)
    return open(p).read().strip() if os.path.exists(p) else "absent"


def utc():
    return subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()


def seed_check(a):
    r = [x for x in csv.DictReader(l for l in open(DRAW) if not l.startswith('"#')) if x["attempt"] == a][0]
    want = "Seed at run time: %s %s %s (environment)" % (r["seed_x"], r["seed_y"], r["seed_z"])
    log = "%s/log/identity-runtime-%s.txt" % (P, a)
    txt = open(log, errors="replace").read() if os.path.exists(log) else ""
    got = re.findall(r"^Seed at run time: .*$", txt, re.M)
    ok = bool(got) and all(g.startswith(want) for g in got)
    return ok, "%d of %d start lines read [%s]" % (sum(g.startswith(want) for g in got), len(got), want)


def main():
    rows = []
    for a in SEEDS:
        rv, ru = res("runtime", a), res("perseed", a)
        row = dict(seed=a, runtime_result=rv.replace(",", ";"), perseed_result=ru.replace(",", ";"))
        sok, snote = seed_check(a)
        row["seed_from_environment"] = ("yes; " if sok else "no; ") + snote
        if not (rv.startswith("0 ") and ru.startswith("0 ")):
            row.update(growth_identity="not measurable", sheets_identity="not measurable", stage_files_identity="not measurable",
                       holds="not measurable (a run did not finish: %s / %s)" % (rv.split()[0], ru.split()[0]))
        else:
            du, dv = "%s/scratch/identity/perseed/%s" % (P, a), "%s/scratch/identity/runtime/%s" % (P, a)
            out = {}
            for kind, sub in (("growth", "growth"), ("sheets", "C40")):
                dest = "%s/evidence/identity-0826-runtime-%s-%s.csv" % (P, a, kind)
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
            ok = out["growth_rc"] == 0 and out["sheets_rc"] == 0 and eq == n and n > 0 and sok
            row.update(growth_identity=out["growth"].replace(",", ";"), sheets_identity=out["sheets"].replace(",", ";"),
                       stage_files_identity=sf, holds="yes" if ok else "no")
        row["reading"] = {"yes": "holds", "no": "fails"}.get(row["holds"], "not measurable (%s)" % row["holds"])
        rows.append(row)
    t = utc()
    cols = ["seed", "runtime_result", "perseed_result", "growth_identity", "sheets_identity", "stage_files_identity",
            "seed_from_environment", "holds", "reading"]
    with open("%s/evidence/identity-0826-runtime.csv" % P, "w", newline="") as f:
        f.write('"# written by %s at %s: the runtime binary (SIMPAPER_SEED_X/Y/Z) against the per seed MLP binaries, chain-0826 settings environment (cap 512, F3), growth on the hot-lines-88 lz4hc copy, stages on the original; growth and sheets by growth-memory-1447/tools/tree_identity.py, stage files by sha256"\n' % (TOOL, t))
        w = csv.DictWriter(f, cols, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    hold = [r["seed"] for r in rows if r["reading"] == "holds"]
    bad = [r["seed"] for r in rows if r["reading"] != "holds"]
    verdict = "yes" if len(hold) >= NEED and not bad else "no"
    with open(P + "/evidence/identity-summary.csv", "w", newline="") as f:
        f.write("# written by %s at %s: chain-0826/evidence/identity-0826-summary.csv's columns (read by tools/deliver.sh G6: "
                "first column the build, last column identity_holds); yes only with all %d seeds holding\n" % (TOOL, t, NEED))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["build", "against", "seeds_holding", "seeds_failing_or_not_measurable", "seeds_replaced", "evidence", "identity_holds"])
        w.writerow([BUILD, AGAINST, ";".join(hold), ";".join(bad) or "none", "none",
                    "runs/rev1/runtime-params-96/evidence/identity-0826-runtime.csv", verdict])
    with open("/data/scrollagent/ledger/ledger.csv", "a", newline="") as f:
        csv.writer(f).writerow([t, "rev1", "coordinator-agent", "runtime-params-96-identity",
                                "PLAN 96 bar: the one runtime simpaper10 (seed from SIMPAPER_SEED_X/Y/Z) against the per seed MLP binaries on 0826 seeds 109, 300, 237 (chain settings, lz4hc growth copy): holding %s, failing or not measurable %s: identity_holds %s; per seed %s"
                                % (";".join(hold) or "none", ";".join(bad) or "none", verdict,
                                   " | ".join("%s %s/%s/%s" % (r["seed"], r["growth_identity"], r["sheets_identity"], r["stage_files_identity"]) for r in rows)),
                                TOOL, "", "", "0", "runs/rev1/runtime-params-96/evidence/identity-0826-runtime.csv; runs/rev1/runtime-params-96/evidence/identity-summary.csv"])
    for r in rows:
        print(r["seed"], r["runtime_result"], "|", r["perseed_result"], "|", r["growth_identity"], "|", r["sheets_identity"],
              "|", r["stage_files_identity"], "|", r["seed_from_environment"], "|", r["reading"])
    print("identity_holds", verdict)


if __name__ == "__main__":
    main()
