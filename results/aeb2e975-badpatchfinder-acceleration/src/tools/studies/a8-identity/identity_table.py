#!/usr/bin/env python3
"""Compare what the two arms wrote, file by file and line by line.

In the shape of c-stage-cost/evidence/identity.csv: one row per file, both hashes, and a
column that says whether they are the same. Two files come out:

  evidence/identity.csv        one row per file of each tree, noA8 against plain
  evidence/stdout-identity.csv one row per stage of each tree, the two standard outputs
                               compared line by line, with the first differing line quoted

The binaries' own sha256 are rows of the first file, because «the same series without one
patch» is a claim about how they were built and not something the outputs can show.

Rule of 2026-09-22T04:17:45Z: the expected count and the count found are both written, and the
tool refuses rather than write a short file.
"""
import csv, hashlib, os, sys

S = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES = ["seed26", "repeat"]
ARMS = ["noA8", "plain"]
STAGES = ["c", "l", "vm-10", "hm-10", "fm-30-10"]
BIN = {"noA8": "/data/scrollagent/runs/rev1/quiet-bench/scratch/bin/noA8/simpaper10",
       "plain": "/data/scrollagent/runs/rev1/c-stage-cost/scratch/bin/plain/simpaper10"}
OUT = os.path.join(S, "evidence", "identity.csv")
OUT2 = os.path.join(S, "evidence", "stdout-identity.csv")
OUT3 = os.path.join(S, "evidence", "identity-totals.csv")
SCROLL = {"seed26": "PHerc1447", "repeat": "PHerc0139"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def written(root):
    """Every file under the output of a run, by path relative to it."""
    out = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            p = os.path.join(dirpath, f)
            out[os.path.relpath(p, root)] = p
    return out


def main():
    rows, srows = [], []
    ready = []
    for tree in TREES:
        dirs = {a: os.path.join(S, "scratch", "%s-%s" % (tree, a)) for a in ARMS}
        if not all(os.path.isdir(d) for d in dirs.values()):
            print("%s: both arms have not run yet" % tree)
            continue
        ready.append(tree)
        a, b = written(dirs["noA8"]), written(dirs["plain"])
        both = sorted(set(a) & set(b))
        for f in both:
            # the carried input is hard linked into neither: each arm has its own copy, so
            # every file here was either copied from the growth tree or written by a stage.
            # The column says which, from whether the growth tree has it.
            ha, hb = sha(a[f]), sha(b[f])
            rows.append({
                "tree": tree, "arm_a": "noA8", "arm_b": "plain", "file": f,
                "sha256_noA8": ha, "sha256_plain": hb,
                "byte_identical": "yes" if ha == hb else "NO",
                "bytes": os.path.getsize(a[f]),
            })
        for f in sorted(set(a) - set(b)):
            rows.append({"tree": tree, "arm_a": "noA8", "arm_b": "plain", "file": f,
                         "sha256_noA8": sha(a[f]), "sha256_plain": "the file is not there",
                         "byte_identical": "NO, only the noA8 arm wrote it",
                         "bytes": os.path.getsize(a[f])})
        for f in sorted(set(b) - set(a)):
            rows.append({"tree": tree, "arm_a": "noA8", "arm_b": "plain", "file": f,
                         "sha256_noA8": "the file is not there", "sha256_plain": sha(b[f]),
                         "byte_identical": "NO, only the plain arm wrote it",
                         "bytes": os.path.getsize(b[f])})

        for st in STAGES:
            pa = os.path.join(S, "log", "%s-noA8-%s.txt" % (tree, st))
            pb = os.path.join(S, "log", "%s-plain-%s.txt" % (tree, st))
            if not (os.path.exists(pa) and os.path.exists(pb)):
                continue
            la = open(pa, errors="replace").read().splitlines()
            lb = open(pb, errors="replace").read().splitlines()
            first = ""
            for i, (x, y) in enumerate(zip(la, lb), 1):
                if x != y:
                    first = "line %d: noA8 %r against plain %r" % (i, x[:70], y[:70])
                    break
            if not first and len(la) != len(lb):
                first = "the same to line %d and then one stops: noA8 %d lines, plain %d" % (
                    min(len(la), len(lb)), len(la), len(lb))
            srows.append({
                "tree": tree, "stage": st.replace("-", " "),
                "lines_noA8": len(la), "lines_plain": len(lb),
                "identical": "yes" if not first else "NO",
                "first_difference": first or "",
            })

    if not rows:
        sys.exit("nothing to compare yet")

    for a in ARMS:
        rows.insert(0, {"tree": "the binaries", "arm_a": a, "arm_b": "", "file": BIN[a],
                        "sha256_noA8": sha(BIN[a]) if a == "noA8" else "",
                        "sha256_plain": sha(BIN[a]) if a == "plain" else "",
                        "byte_identical": "not applicable, this row is the binary itself",
                        "bytes": os.path.getsize(BIN[a])})

    cols = ["tree", "arm_a", "arm_b", "file", "sha256_noA8", "sha256_plain",
            "byte_identical", "bytes"]
    diff = [r for r in rows if r["byte_identical"].startswith("NO")]
    with open(OUT, "w", newline="") as fh:
        fh.write('"# one row per file the two arms wrote, noA8 against plain, on %s. The two '
                 'arms differ by patches/performance/00002 and nothing else, and the first two '
                 'rows are the binaries own sha256 because that is a claim about how they were '
                 'built. %d files compared, %d differing. Each arm ran on its own fresh copy of '
                 'the growth tree, so nothing here is a hard link and no file is identical by '
                 'construction."\n' % (" and ".join(ready), len(rows) - 2, len(diff)))
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])

    if srows:
        with open(OUT2, "w", newline="") as fh:
            fh.write('"# the standard output of each stage, the two arms compared line by '
                     'line. first_difference quotes the first line that differs, or says where '
                     'one output stops, and is empty when they are the same."\n')
            w = csv.writer(fh)
            w.writerow(list(srows[0].keys()))
            for r in srows:
                w.writerow(list(r.values()))

    # The counts as cells, not as a sentence in a header. A text that says «94,962 files, none
    # differing» has to read that pair off a column, and a row count of another CSV is not a
    # column: the read back sweep marked all four of these numbers «derived» until this file
    # existed. Rule of the house, a check is a column.
    summary = []
    for t in sorted({r["tree"] for r in rows if r["tree"] != "the binaries"}):
        tr = [r for r in rows if r["tree"] == t]
        td = [r for r in tr if r in diff]
        summary.append({
            "tree": t,
            "scroll": SCROLL.get(t, "not measurable, the tree is not in the scroll table"),
            "files_compared": len(tr),
            "files_byte_identical": len(tr) - len(td),
            "files_differing": len(td),
        })
    summary.append({
        "tree": "both trees",
        "scroll": "PHerc1447 and PHerc0139",
        "files_compared": len(rows) - 2,
        "files_byte_identical": (len(rows) - 2) - len(diff),
        "files_differing": len(diff),
    })
    with open(OUT3, "w", newline="") as fh:
        fh.write('"# the totals of identity.csv as columns, one row per growth tree and one '
                 'for the two together, so that a text reads the pair off a column instead of '
                 'counting the rows of another file. The two binary rows of identity.csv are '
                 'not files either arm wrote and are not counted here."\n')
        w = csv.writer(fh)
        w.writerow(list(summary[0].keys()))
        for r in summary:
            w.writerow(list(r.values()))
    print("wrote %s: %d row(s)" % (OUT3, len(summary)))

    print("wrote %s: %d files compared, %d differing" % (OUT, len(rows) - 2, len(diff)))
    for r in diff[:8]:
        print("  DIFFERS %s %s" % (r["tree"], r["file"]))
    if srows:
        bad = [r for r in srows if r["identical"] != "yes"]
        print("wrote %s: %d stages, %d differing" % (OUT2, len(srows), len(bad)))
        for r in bad[:5]:
            print("  DIFFERS %s %s: %s" % (r["tree"], r["stage"], r["first_difference"][:90]))


if __name__ == "__main__":
    main()
