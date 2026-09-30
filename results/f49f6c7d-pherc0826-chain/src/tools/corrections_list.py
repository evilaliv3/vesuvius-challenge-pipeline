#!/usr/bin/env python3
"""corrections_list.py: what the chain as delivered ran beyond arm C, listed from the shipped patches.

Arm X of stevens-changes-0826-91 is the chain as delivered: arm C plus the six output changing corrections and the
three inert ones of the laboratory's patch series (src/prereg/stevens-changes-0826-91.md, arm X). The nine patches are
shipped under src/inputs/chain-0826-corrections/, one folder per group, with their sha256 in SHA256SUMS there. This
tool checks those sums, lists each patch with the source files it touches, and sets the chain's delivered trees beside
arm C's on the same seeds (the snapshot of per-run.csv, rows X and C), so the text can say that the two differ.

Writes src/evidence/derived/corrections.csv (key, group, what, value, source). Standard library only.
"""
import csv, hashlib, os, re, statistics, subprocess, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(SRC, "inputs", "chain-0826-corrections")
PR = os.path.join(SRC, "evidence", "studies", "stevens-changes-0826-91", "per-run.csv")
OUT = os.path.join(SRC, "evidence", "derived", "corrections.csv")
GROUPS = (("corrections", "changes output", "yes"), ("corrections-inert", "inert", "no"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    sums = {}
    for l in open(os.path.join(IN, "SHA256SUMS")):
        if l.startswith("#") or not l.strip():
            continue
        h, f = l.split(None, 1)
        sums[f.strip()] = h
    rows = []

    def put(key, group, what, value, source):
        rows.append(dict(key=key, group=group, what=what, value=value, source=source))

    counts = {}
    for folder, label, changes in GROUPS:
        names = sorted(f for f in os.listdir(os.path.join(IN, folder)) if f.endswith(".patch"))
        counts[folder] = len(names)
        for f in names:
            rel = "%s/%s" % (folder, f)
            p = os.path.join(IN, rel)
            if sums.get(rel) != sha(p):
                sys.exit("corrections_list.py: %s does not match SHA256SUMS" % rel)
            touched = sorted({os.path.basename(m) for m in re.findall(r"^\+\+\+ b/(\S+)", open(p).read(), re.M)})
            put(f[:-len(".patch")], label, "source files touched; changes output: %s" % changes, ";".join(touched),
                "inputs/chain-0826-corrections/" + rel)
    put("count_changes_output", "corrections", "patches that change output", counts["corrections"],
        "inputs/chain-0826-corrections/corrections")
    put("count_inert", "corrections-inert", "patches measured inert", counts["corrections-inert"],
        "inputs/chain-0826-corrections/corrections-inert")
    if (counts["corrections"], counts["corrections-inert"]) != (6, 3):
        sys.exit("corrections_list.py: the declaration names six and three, the folders hold %d and %d"
                 % (counts["corrections"], counts["corrections-inert"]))
    with open(PR, newline="") as fh:
        pr = list(csv.DictReader(l for l in fh if not l.lstrip('"').startswith("#")))
    x = {r["attempt"]: r for r in pr if r["arm"] == "X"}
    c = {r["attempt"]: r for r in pr if r["arm"] == "C" and r["outcome"] == "completed"}
    both = sorted(set(x) & set(c))
    diff = [s for s in both if x[s]["growth_patches"] != c[s]["growth_patches"]]
    src = "evidence/studies/stevens-changes-0826-91/per-run.csv"
    put("x_c_seeds", "X against C", "seeds with both a delivered tree (X) and an arm C run", len(both), src)
    put("x_c_seeds_growth_differs", "X against C", "of them, seeds whose growth patch count differs", len(diff), src)
    for col, k in (("growth_patches", "growth_patches"), ("stevens_formula_cm2", "formula_cm2"), ("best_square_mm", "square_mm")):
        for arm, d in (("x", x), ("c", c)):
            v = statistics.median(float(d[s][col]) for s in both)
            put("median_%s_%s" % (k, arm), "X against C", "median over those seeds of %s, arm %s" % (col, arm.upper()),
                ("%d" % v) if col == "growth_patches" and v == int(v) else ("%.1f" % v if col == "growth_patches" else "%.4f" % v), src)
    now = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(OUT, "w", newline="") as fh:
        fh.write('"# written by src/tools/corrections_list.py at %s: the nine corrections the chain as delivered ran '
                 'beyond arm C (src/prereg/stevens-changes-0826-91.md, arm X), from the patches shipped under '
                 'src/inputs/chain-0826-corrections, and the chain\'s trees beside arm C\'s on the same seeds"\n' % now)
        w = csv.DictWriter(fh, fieldnames=["key", "group", "what", "value", "source"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print("corrections_list.py: %d rows, %d of %d seeds differ" % (len(rows), len(diff), len(both)))


if __name__ == "__main__":
    main()
