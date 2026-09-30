"""What the merged change is: the squash commit of pull request 1823 as it sits in ScrollPrize/villa.

Written 2026-09-30 on the referee's finding 4: the article described the fork's commit of the
pull request, and the squash that was merged differs from it. This reads the squash commit named
by evidence/upstream-status.csv from a clone of ScrollPrize/villa and writes one row per file it
touches and one row per test case it adds, each with the command that gave it.

    python3 tools/merged_patch.py [--clone /data/repositories/villa]

Writes evidence/merged-patch.csv. Stops if the clone does not hold the commit, or if the commit
is not the squash upstream-status.csv names for pull request 1823.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L    # noqa: E402

PR = 1823
OUT = os.path.join(L.EV, "merged-patch.csv")
COLS = ["pr", "squash_commit", "kind", "path", "added", "deleted", "name", "source"]


def git(clone, *args):
    return subprocess.check_output(["git", "-C", clone] + list(args), text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", default=os.environ.get("VILLA_UPSTREAM", "/data/repositories/villa"))
    a = ap.parse_args()
    up = {int(r["pr"]): r for r in L.read_csv(os.path.join(L.EV, "upstream-status.csv"))}
    sq = up[PR]["squash_commit"]
    if not sq:
        sys.exit("merged_patch.py: upstream-status.csv names no squash commit for %d" % PR)
    full = git(a.clone, "rev-parse", sq + "^{commit}").strip()
    if full != sq:
        sys.exit("merged_patch.py: the clone resolves %s to %s" % (sq, full))
    subj = git(a.clone, "show", "-s", "--format=%s", sq).strip()
    if "(#%d)" % PR not in subj:
        sys.exit("merged_patch.py: %s is not the squash of #%d: %s" % (sq, PR, subj))
    rows = []
    src = "git -C <villa clone> show --numstat %s" % sq[:9]
    for line in git(a.clone, "show", "--numstat", "--format=", sq).splitlines():
        if not line.strip():
            continue
        add, dele, path = line.split("\t")
        rows.append(dict(pr=PR, squash_commit=sq, kind="file", path=path, added=add, deleted=dele,
                         name="", source=src))
    tests = [r["path"] for r in rows if r["path"].endswith("test_normalgridtools.cpp")]
    if len(tests) != 1:
        sys.exit("merged_patch.py: %d test files in the squash, expected one" % len(tests))
    diff = git(a.clone, "show", "--format=", sq, "--", tests[0])
    for m in re.finditer(r'^\+TEST_CASE\("([^"]+)"\)', diff, flags=re.M):
        rows.append(dict(pr=PR, squash_commit=sq, kind="test_case_added", path=tests[0], added="",
                         deleted="", name=m.group(1),
                         source="git -C <villa clone> show %s -- %s, lines +TEST_CASE" % (sq[:9], tests[0])))
    L.write_csv(OUT, COLS, rows)
    print("files %d, test cases added %d" % (sum(r["kind"] == "file" for r in rows),
                                             sum(r["kind"] == "test_case_added" for r in rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
