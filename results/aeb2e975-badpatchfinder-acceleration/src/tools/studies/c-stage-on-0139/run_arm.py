#!/usr/bin/env python3
"""Run the downstream of one PHerc0139 growth tree on a FRESH COPY of it, with one arm's binary.

Adapted from runs/rev1/c-stage-cost/tools/run_arm.py. What was adapted, and nothing else:

  * the trees are named in tools/tree_inventory.py and live under several studies, so --tree takes
    an id and the path comes from that list, instead of a single seed folder;
  * the zarr, the chunk manifest and the scroll are PHerc0139's;
  * --repeat gives each timing run its own output folder, so two repeats never collide;
  * --drop removes the output copy when the run is over, which the timing runs use and the
    identity runs do not, because the identity runs are hashed afterwards;
  * the CSV is this study's evidence/runs.csv, with the tree id and the repeat index added.

Unchanged and deliberately so: the tree on disk is never run in place, the machine is read with
/data/scrollagent/tools/machine.sh before the copy and the run refuses to start above the ceiling
of cores busy or below the memory floor, both numbers go into the row, a row is written whatever
the return code, and the whole thing writes only inside this study's folder.

Usage:
  run_arm.py --arm <plain|guarded|c2> --tree <id> --tag <tag> [--stages c|all]
             [--threads N] [--repeat N] [--drop]
"""
import argparse, csv, os, re, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/c-stage-on-0139"
ZARR = "/data/scrollagent/data/datasets/PHerc0139/0"
CHUNKS = "/data/scrollagent/data/datasets/PHerc0139/chunks.txt"
MACHINE = "/data/scrollagent/tools/machine.sh"
CSV = os.path.join(S, "evidence", "runs.csv")
TREES_CSV = os.path.join(S, "evidence", "trees.csv")
ALL_STAGES = ["c", "l", "vm 10", "hm 10", "fm 30 10"]
PATCH_LIMIT = "40000"
CORES_CEILING = 22.0
MEM_FLOOR_GB = 20.0
HEADER = [
    "tag",                    # the name this study gives the run
    "arm",                    # plain, guarded or c2
    "tree",                   # the PHerc0139 growth tree that was copied and run
    "repeat",                 # which repetition of that arm on that tree this is
    "binary_sha256",          # sha256 of the binary, read at the moment of the run
    "stage",                  # the chain stage, as given on the command line
    "seconds",                # wall clock of that stage, time.monotonic around the subprocess
    "return_code",            # what the stage returned
    "patch_limit",            # SIMPAPER_PATCH_LIMIT the stage was given
    "omp_num_threads",        # the thread budget the stage was given
    "cores_busy_at_start",    # from tools/machine.sh, /proc/stat ticks over one second
    "mem_available_gb_at_start",  # from tools/machine.sh, MemAvailable of /proc/meminfo
    "started_utc",            # date -u at the start of the stage
    "log",                    # where the stage's own output went
    "out_dir",                # the copy of the tree it wrote into
]


def tree_path(tid):
    with open(TREES_CSV) as f:
        for r in csv.DictReader(l for l in f if not l.startswith("#")):
            if r["tree"] == tid:
                if r["exists"] != "yes":
                    raise SystemExit("tree %s is not runnable: %s" % (tid, r["note"]))
                return r["path"]
    raise SystemExit("no tree %s in %s" % (tid, TREES_CSV))


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
    growth = tree_path(a.tree)
    pdir = os.path.join(growth, "patches")
    if not os.path.isdir(pdir) or len(os.listdir(pdir)) == 0:
        raise SystemExit("the growth tree at %s has no patch in it" % growth)
    if not os.path.isfile(os.path.join(growth, "rel.csv")) or \
            os.path.getsize(os.path.join(growth, "rel.csv")) == 0:
        raise SystemExit("the growth tree at %s has no rel.csv" % growth)

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
    subprocess.check_call(["cp", "-a", growth, out])

    stages = ALL_STAGES if a.stages == "all" else [a.stages]
    env = dict(os.environ, SIMPAPER_OUTPUT_DIR=out, SIMPAPER_SURFACE_ZARR=ZARR,
               ZARR_MISSING_LIST=os.path.join(out, "missing-C40.txt"),
               ZARR_CHUNK_MANIFEST=CHUNKS, SIMPAPER_PATCH_LIMIT=PATCH_LIMIT,
               OMP_NUM_THREADS=str(a.threads), TMPDIR="/data/tmp")

    new = not os.path.exists(CSV)
    for st in stages:
        slug = st.replace(" ", "_")
        log = os.path.join(S, "log", "chain-%s-%s-r%d-%s.txt"
                           % (a.tag, a.tree, a.repeat, slug))
        cmd = [binary] + st.split()
        started = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
        t0 = time.monotonic()
        with open(log, "wb") as h:
            rc = subprocess.call(cmd, env=env, stdout=h, stderr=subprocess.STDOUT, cwd=out)
        secs = time.monotonic() - t0
        with open(CSV, "a", newline="") as f:
            w = csv.writer(f)
            if new and not os.path.getsize(CSV):
                f.write("# one row per chain stage run by tools/run_arm.py on a fresh copy of a "
                        "PHerc0139 growth tree. seconds is wall clock from time.monotonic around "
                        "the subprocess; cores_busy_at_start and mem_available_gb_at_start are "
                        "the first line of /data/scrollagent/tools/machine.sh read just before "
                        "the copy, because this machine is shared. A row is written whatever the "
                        "return code, and the copy is what the stage wrote into: the tree on disk "
                        "is never run in place.\n")
                w.writerow(HEADER)
                new = False
            w.writerow([a.tag, a.arm, a.tree, a.repeat, bsha, st, "%.1f" % secs, rc,
                        PATCH_LIMIT, a.threads, "%.1f" % busy, "%.1f" % mem, started, log, out])
        print("%s %s %s r%d stage '%s' rc=%d in %.1f s"
              % (a.tag, a.arm, a.tree, a.repeat, st, rc, secs), flush=True)
        if rc != 0:
            print("stage returned non zero, stopping this arm", flush=True)
            break
    sheets = len([n for n in os.listdir(out)
                  if n.startswith("patch_") and n.endswith(".bin")])
    print("%s %s %s r%d done, sheets %d" % (a.tag, a.arm, a.tree, a.repeat, sheets), flush=True)
    if a.drop:
        shutil.rmtree(out, ignore_errors=True)
        print("dropped %s" % out, flush=True)


if __name__ == "__main__":
    sys.exit(main())
