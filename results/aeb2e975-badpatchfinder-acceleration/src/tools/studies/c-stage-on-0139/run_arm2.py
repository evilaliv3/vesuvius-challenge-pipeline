#!/usr/bin/env python3
"""Run the downstream of one PHerc0139 growth tree on a fresh working copy, with one arm's binary.

This is tools/run_arm.py with one thing changed, and it is a new file because the first was
running when the change was wanted (a script is never edited while it executes).

What changed: the working copy is made from this study's own pristine copy of the tree, with
`cp -al`, so the patch files are hard links and the copy costs a second instead of two minutes.
Why that is safe, and how it is checked:

  * the pristine copy under scratch/pristine/<tree> is itself a real `cp -a` of the tree, made
    once by tools/make_pristine.sh. The tree that belongs to another study is read once, by that
    copy, and is never opened again by this study;
  * so a stage that wrote in place would damage this study's pristine copy and nothing else;
  * and it would be caught: tools/check_pristine.py re-reads every pristine copy and compares its
    content sha256 with the value tools/tree_inventory.py took from the original tree before
    anything ran. That check is run after the first full downstream and again at the end.

Everything else is tools/run_arm.py unchanged: the machine is read before the copy and the run
refuses to start above the ceiling of cores busy or below the memory floor, both numbers go into
the row, a row is written whatever the return code, the same SIMPAPER_PATCH_LIMIT is given to
every arm, and the tool writes only inside this study's folder.

Usage:
  run_arm2.py --arm <plain|guarded|c2> --tree <id> --tag <tag> [--stages c|all]
              [--threads N] [--repeat N] [--drop]
"""
import argparse, csv, os, re, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
ZARR = "/data/scrollagent/data/datasets/PHerc0139/0"
CHUNKS = "/data/scrollagent/data/datasets/PHerc0139/chunks.txt"
MACHINE = "/data/scrollagent/tools/machine.sh"
CSV = os.path.join(S, "evidence", "runs.csv")
PRISTINE = os.path.join(S, "scratch", "pristine")
ALL_STAGES = ["c", "l", "vm 10", "hm 10", "fm 30 10"]
PATCH_LIMIT = "40000"
CORES_CEILING = 22.0
MEM_FLOOR_GB = 20.0
HEADER = [
    "tag", "arm", "tree", "repeat", "binary_sha256", "stage", "seconds", "return_code",
    "patch_limit", "omp_num_threads", "cores_busy_at_start", "mem_available_gb_at_start",
    "started_utc", "log", "out_dir",
]


def machine():
    line = subprocess.check_output(["bash", MACHINE]).decode().splitlines()[0]
    busy = float(re.search(r"cores busy ([0-9.]+)", line).group(1))
    mem = float(re.search(r"MemAvailable ([0-9.]+)", line).group(1))
    return busy, mem, line


def sha256(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--stages", default="c")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--drop", action="store_true")
    a = ap.parse_args()

    binary = os.path.join(S, "scratch", "bin", a.arm, "simpaper10")
    if not os.access(binary, os.X_OK):
        raise SystemExit("no binary at %s" % binary)
    bsha = sha256(binary)
    src = os.path.join(PRISTINE, a.tree)
    pdir = os.path.join(src, "patches")
    if not os.path.isdir(pdir) or len(os.listdir(pdir)) == 0:
        raise SystemExit("no pristine copy with patches at %s" % src)
    rel = os.path.join(src, "rel.csv")
    if not os.path.isfile(rel) or os.path.getsize(rel) == 0:
        raise SystemExit("no rel.csv in %s" % src)

    busy, mem, line = machine()
    print("machine: " + line, flush=True)
    if busy > CORES_CEILING:
        raise SystemExit("cores busy %.1f is above the ceiling of %.1f, not starting"
                         % (busy, CORES_CEILING))
    if mem < MEM_FLOOR_GB:
        raise SystemExit("MemAvailable %.1f GB is below the floor of %.1f, not starting"
                         % (mem, MEM_FLOOR_GB))

    out = os.path.join(S, "scratch", "out", a.tag, "%s-r%d" % (a.tree, a.repeat), "C40")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        shutil.rmtree(out)
    subprocess.check_call(["cp", "-al", src, out])

    stages = ALL_STAGES if a.stages == "all" else [a.stages]
    env = dict(os.environ, SIMPAPER_OUTPUT_DIR=out, SIMPAPER_SURFACE_ZARR=ZARR,
               ZARR_MISSING_LIST=os.path.join(out, "missing-C40.txt"),
               ZARR_CHUNK_MANIFEST=CHUNKS, SIMPAPER_PATCH_LIMIT=PATCH_LIMIT,
               OMP_NUM_THREADS=str(a.threads), TMPDIR="/data/tmp")

    for st in stages:
        slug = st.replace(" ", "_")
        log = os.path.join(S, "log", "chain-%s-%s-r%d-%s.txt" % (a.tag, a.tree, a.repeat, slug))
        cmd = [binary] + st.split()
        started = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
        t0 = time.monotonic()
        with open(log, "wb") as h:
            rc = subprocess.call(cmd, env=env, stdout=h, stderr=subprocess.STDOUT, cwd=out)
        secs = time.monotonic() - t0
        with open(CSV, "a", newline="") as f:
            csv.writer(f).writerow(
                [a.tag, a.arm, a.tree, a.repeat, bsha, st, "%.1f" % secs, rc, PATCH_LIMIT,
                 a.threads, "%.1f" % busy, "%.1f" % mem, started, log, out])
        print("%s %s %s r%d stage '%s' rc=%d in %.1f s"
              % (a.tag, a.arm, a.tree, a.repeat, st, rc, secs), flush=True)
        if rc != 0:
            print("stage returned non zero, stopping this arm", flush=True)
            break
    sheets = len([n for n in os.listdir(out) if n.startswith("patch_") and n.endswith(".bin")])
    print("%s %s %s r%d done, sheets %d" % (a.tag, a.arm, a.tree, a.repeat, sheets), flush=True)
    if a.drop:
        shutil.rmtree(out, ignore_errors=True)
        print("dropped %s" % out, flush=True)


if __name__ == "__main__":
    sys.exit(main())
