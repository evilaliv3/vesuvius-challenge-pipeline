#!/usr/bin/env python3
"""identity_summary.py: evidence/identity-0826-summary.csv from every seed row of the G6 identity bar
(DECLARATION.md addition of 2026-09-26T19:46:28Z).

Reads evidence/identity-0826.csv (first run: seed109, seed300, seed43) and every evidence/identity-0826-PHerc0826-seed*.csv
(later runs, one per replacement seed). A seed whose growth failed on BOTH builds (variant_result and unchanged_result
both «growth <rc>» with rc not 0) is «not measurable, crashed on both builds» and is replaced, not counted. identity_holds
is «yes» only when at least three measurable seeds hold and no measurable seed fails; any other not measurable seed
(one build crashed, a stop at the deadline) makes it «no». Writes evidence/identity-0826-all.csv (every seed row with its
reading) and the summary in the form tools/deliver.sh reads (first column build, last column identity_holds); a ledger row.
"""
import csv
import glob
import subprocess

S = "/data/scrollagent/runs/rev1/chain-0826"
TOOL = "chain-0826/tools/identity_summary.py"
BUILD = "flathash+avx512"
NEED = 3


def rows(p):
    return list(csv.DictReader(l for l in open(p, newline="") if not l.startswith('"#')))


def utc():
    return subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip()


def crashed(x):
    return x.startswith("growth ") and not x.startswith("growth 0")


def main():
    files = [S + "/evidence/identity-0826.csv"] + sorted(glob.glob(S + "/evidence/identity-0826-PHerc0826-seed*.csv"))
    files = [f for f in files if not f.endswith(("-growth.csv", "-sheets.csv"))]
    allr = []
    for f in files:
        for r in rows(f):
            if crashed(r["variant_result"]) and crashed(r["unchanged_result"]):
                reading = "not measurable, crashed on both builds (replaced)"
            elif r["holds"] == "yes":
                reading = "holds"
            elif r["holds"] == "no":
                reading = "fails"
            else:
                reading = "not measurable (%s)" % r["holds"]
            allr.append(dict(r, source=f.split("/evidence/")[1], reading=reading))
    seen = [r["seed"] for r in allr]
    if len(seen) != len(set(seen)):
        raise SystemExit("a seed appears twice: %s" % seen)
    hold = [r["seed"] for r in allr if r["reading"] == "holds"]
    bad = [r["seed"] for r in allr if r["reading"] == "fails" or r["reading"].startswith("not measurable (")]
    verdict = "yes" if len(hold) >= NEED and not bad else "no"
    t = utc()
    cols = ["seed", "variant_result", "unchanged_result", "growth_identity", "sheets_identity", "stage_files_identity",
            "holds", "reading", "source"]
    with open(S + "/evidence/identity-0826-all.csv", "w", newline="") as f:
        f.write('"# written by %s at %s: every seed row of the G6 identity bar, %s against unchanged; reading per DECLARATION.md addition of 2026-09-26T19:46:28Z"\n' % (TOOL, t, BUILD))
        w = csv.DictWriter(f, cols, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(allr)
    with open(S + "/evidence/identity-0826-summary.csv", "w", newline="") as f:
        f.write("# written by %s at %s: read by tools/deliver.sh (G6): first column the build, last column identity_holds; "
                "yes only with at least %d measurable seeds holding and none failing\n" % (TOOL, t, NEED))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["build", "against", "seeds_holding", "seeds_failing_or_not_measurable", "seeds_replaced", "evidence", "identity_holds"])
        w.writerow([BUILD, "unchanged", ";".join(hold), ";".join(bad) or "none",
                    ";".join(r["seed"] for r in allr if r["reading"].startswith("not measurable, crashed")) or "none",
                    "evidence/identity-0826-all.csv", verdict])
    with open("/data/scrollagent/ledger/ledger.csv", "a", newline="") as f:
        csv.writer(f).writerow([t, "rev1", "coordinator-agent", "chain-0826-identity-summary",
                                "G6 summary rewritten: %s against unchanged, holding %s, failing or not measurable %s, replaced %s: identity_holds %s"
                                % (BUILD, ";".join(hold), ";".join(bad) or "none",
                                   ";".join(r["seed"] for r in allr if r["reading"].startswith("not measurable, crashed")) or "none", verdict),
                                TOOL, "", "", "0", "runs/rev1/chain-0826/evidence/identity-0826-summary.csv"])
    print("holding", hold, "bad", bad, "identity_holds", verdict)


if __name__ == "__main__":
    main()
