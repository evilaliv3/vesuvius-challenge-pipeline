# This file is a copy of tools/regression_test_result.py of the working tree and differs from it
# in one way only: the logs of the test run are read from evidence/regression-test/ in this
# folder, where the audit's files are kept (the commit hash as sources-commit.txt, the OpenCV
# version header the build read as opencv-version.hpp, the compiler's own version line as
# compiler.log, written by the same g++ on the same machine), and the fork carrying the patch is
# named by VILLA_FORK. Nothing else is changed.
"""The regression test of the patch, as built and run on this machine, read from its logs.

The audit of 2026-09-17 built the test target of the patch
commit from the commit's own sources, with the system g++ and a stock OpenCV, and ran it twice in
fresh processes. The paper quotes the outcome: the pass count, the distance each new case landed
at against the tolerance it asserts, the side the thinned case leans to, the build and run times,
and the two departures from the project's own build (the flags and the OpenCV). Every one of
those numbers is read here from the logs the audit left, not retyped: distances.log (the companion
that recomputes the four calls and prints the margins), run.log and run2.log (the test binary's
own output and timing), build.log (the build timing), sources-commit.txt (the commit the sources were
archived from), the compiler and the OpenCV headers the build used.

The patch commit is found by what it touches, the only commit of the branch that changes
core/src/normalgridtools.cpp, and not by reading HEAD: since 2026-09-18 the branch carries the
failing case and the driver on top of the patch, so HEAD is the driver and would have been
written into the evidence as the patch. The generator of the article's macros finds it the
same way.

Output: evidence/regression-test-run.csv, one row per case plus one row of the run.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rev1_lib as L        # noqa: E402

W = os.path.join(L.EV, "regression-test")
OCV_VERSION = os.path.join(W, "opencv-version.hpp")
VILLA = os.environ.get("VILLA_FORK") or os.path.join(L.SRC, "villa-fork")
# The one file the patch changes, which is how the patch commit is recognised on a branch that
# now carries two commits above it.
PATCHED_FILE = "volume-cartographer/core/src/normalgridtools.cpp"


def wall(path):
    """The wall time of a log's own `time` line, to two decimals.

    Two decimals and not one because the build and the run took 5.765 s and 5.780 s, five seconds
    apart: rounded to one decimal both print 5.8 and the sentence reads as a copy and paste.
    """
    m = re.search(r"^real\s+(\d+)m([\d.]+)s", open(path).read(), re.M)
    return f"{60 * int(m.group(1)) + float(m.group(2)):.2f}"


def main():
    rows = []
    for ln in open(os.path.join(W, "distances.log")):
        name = ln.split()[0]
        kv = dict(re.findall(r"(\w+)=(\S+(?: mm)?)", ln))
        est = re.search(r"estimate=\(([\d.]+), ([\d.]+)\)", ln)
        rows.append(dict(row="case", case=name, segments=kv.get("segments", ""),
                         estimate_x=est.group(1) if est else "", estimate_y=est.group(2) if est else "",
                         inside=kv.get("inside", ""), identical=kv.get("identical", ""),
                         distance_mm=kv["distance"].split()[0] if "distance" in kv else "",
                         tolerance_mm=kv["tolerance"].split()[0] if "tolerance" in kv else "",
                         margin_mm=kv["margin"].split()[0] if "margin" in kv else "",
                         result=ln.split()[-1]))
    run1, run2 = open(os.path.join(W, "run.log")).read(), open(os.path.join(W, "run2.log")).read()
    est1 = re.findall(r"estimate: \[([\d.]+), ([\d.]+)\]", run1)
    est2 = re.findall(r"estimate: \[([\d.]+), ([\d.]+)\]", run2)
    passed = int(re.search(r"(\d+) test case\(s\) passed", run1).group(1))
    src_commit = open(os.path.join(W, "sources-commit.txt")).read().strip()
    patch = subprocess.check_output(["git", "-C", VILLA, "log", "-1", "--format=%H", "--", PATCHED_FILE],
                                    text=True).strip()
    same_tree = subprocess.check_output(["git", "-C", VILLA, "rev-parse", f"{src_commit}^{{tree}}", f"{patch}^{{tree}}"],
                                        text=True).split()
    gpp = re.search(r"\) ([\d.]+)", open(os.path.join(W, "compiler.log")).read()).group(1)
    v = open(OCV_VERSION).read()
    ocv = ".".join(re.search(rf"CV_VERSION_{k}\s+(\d+)", v).group(1) for k in ("MAJOR", "MINOR", "REVISION"))
    rows.append(dict(row="run", case="all", cases_passed=passed, cases_failed=0 if "exit=0" in run1 else "",
                     build_seconds=wall(os.path.join(W, "build.log")), run_seconds=wall(os.path.join(W, "run.log")),
                     second_run_identical="yes" if est1 == est2 and est1 else "no", estimates_printed=len(est1),
                     sources_commit=src_commit[:9], patch_commit=patch[:9],
                     tree=same_tree[1][:8], same_tree="yes" if same_tree[0] == same_tree[1] else "no",
                     compiler=f"g++ {gpp}", opencv=ocv, flags="-std=c++23 -O2, not the project's CMake flags",
                     qt="not needed by this target"))
    cols = sorted({k for r in rows for k in r}, key=lambda k: (k != "row", k != "case", k))
    for r in rows:
        print("  " + " ".join(f"{k}={r[k]}" for k in cols if r.get(k, "") != ""), flush=True)
    L.write_csv(os.path.join(L.EV, "regression-test-run.csv"), cols, rows)


if __name__ == "__main__":
    main()
