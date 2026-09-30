#!/usr/bin/env python3
"""Run the downstream of one seed on a FRESH COPY of its growth tree, with one of this study's
binaries, and time every stage.

The tree on disk is never run in place: it is copied to scratch/out/<tag>/<attempt>/C40 and the
copy is what the stage writes into. Nothing under seed-search-1447 is written.

Before it starts, it reads the whole machine with /data/scrollagent/tools/machine.sh and refuses
to start if cores busy is above the ceiling or MemAvailable below the floor, because the machine
is shared with other studies' growths. Both numbers are written into the row, so a time taken on
a loaded machine can be told from one taken on a quiet one.

Usage:
  run_arm.py --binary <label> --attempt PHerc1447-seedNN --tag <tag> [--stages c|all]
             [--threads N] [--perf] [--cap SECONDS]

Appends one row per stage to evidence/runs.csv.
"""
import argparse, csv, os, re, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/c-stage-cost"
SEEDS = "/data/scrollagent/runs/rev1/seed-search-1447/out"
ZARR = "/data/scrollagent/data/datasets/PHerc1447/0"
CHUNKS = "/data/scrollagent/data/datasets/PHerc1447/chunks.txt"
MACHINE = "/data/scrollagent/tools/machine.sh"
CSV = os.path.join(S, "evidence", "runs.csv")
ALL_STAGES = ["c", "l", "vm 10", "hm 10", "fm 30 10"]
CORES_CEILING = 22.0
MEM_FLOOR_GB = 20.0
HEADER = [
    "tag",                    # the name this study gives the arm
    "attempt",                # the seed whose growth tree was copied and run
    "binary_label",           # which build under scratch/bin was run
    "binary_sha256",          # its sha256, read at the moment of the run
    "stage",                  # the chain stage, as given on the command line
    "seconds",                # wall clock of that stage, time.monotonic around the subprocess
    "return_code",            # what the stage returned
    "omp_num_threads",        # the thread budget the stage was given
    "cores_busy_at_start",    # from tools/machine.sh, /proc/stat ticks over one second
    "mem_available_gb_at_start",  # from tools/machine.sh, MemAvailable of /proc/meminfo
    "started_utc",            # date -u at the start of the stage
    "log",                    # where the stage's own output went
    "out_dir",                # the copy of the tree it wrote into
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
    ap.add_argument("--binary", required=True)
    ap.add_argument("--attempt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--stages", default="c")
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--perf", action="store_true")
    ap.add_argument("--cap", type=int, default=0, help="seconds, 0 is no cap")
    ap.add_argument("--keep-tree", action="store_true")
    a = ap.parse_args()

    binary = os.path.join(S, "scratch", "bin", a.binary, "simpaper10")
    if not os.access(binary, os.X_OK):
        raise SystemExit("no binary at %s" % binary)
    bsha = sha256(binary)
    growth = os.path.join(SEEDS, a.attempt, "growth")
    if not os.path.isdir(os.path.join(growth, "patches")):
        raise SystemExit("no growth tree at %s" % growth)
    if len(os.listdir(os.path.join(growth, "patches"))) == 0:
        raise SystemExit("the growth tree at %s has no patch in it" % growth)

    busy, mem, line = machine()
    print("machine: " + line, flush=True)
    if busy > CORES_CEILING:
        raise SystemExit("cores busy %.1f is above the ceiling of %.1f, not starting"
                         % (busy, CORES_CEILING))
    if mem < MEM_FLOOR_GB:
        raise SystemExit("MemAvailable %.1f GB is below the floor of %.1f, not starting"
                         % (mem, MEM_FLOOR_GB))

    out = os.path.join(S, "scratch", "out", a.tag, a.attempt, "C40")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        shutil.rmtree(out)
    print("copying %s to %s" % (growth, out), flush=True)
    subprocess.check_call(["cp", "-a", growth, out])

    stages = ALL_STAGES if a.stages == "all" else [a.stages]
    env = dict(os.environ, SIMPAPER_OUTPUT_DIR=out, SIMPAPER_SURFACE_ZARR=ZARR,
               ZARR_MISSING_LIST=os.path.join(out, "missing-C40.txt"),
               ZARR_CHUNK_MANIFEST=CHUNKS, SIMPAPER_PATCH_LIMIT="40000",
               OMP_NUM_THREADS=str(a.threads), TMPDIR="/data/tmp")

    # the header goes in only when the file does not exist yet. The first version of this
    # tool tested that once per process, so the second process to write appended a second
    # header row in the middle of the file; tools/summarise_times.py skips any row whose
    # first field is the word tag, and the raw file is left as it was written.
    new = not os.path.exists(CSV)
    for st in stages:
        slug = st.replace(" ", "_")
        log = os.path.join(S, "log", "chain-%s-%s-%s.txt" % (a.tag, a.attempt, slug))
        cmd = [binary] + st.split()
        if a.perf and st == "c":
            data = os.path.join(S, "scratch", "perf-%s-%s.data" % (a.tag, a.attempt))
            cmd = ["perf", "record", "-F", "299", "-e", "cycles:u", "--no-buildid-cache",
                   "-o", data, "--"] + cmd
        if a.cap:
            cmd = ["timeout", "-s", "TERM", str(a.cap)] + cmd
        started = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
        t0 = time.monotonic()
        with open(log, "wb") as h:
            rc = subprocess.call(cmd, env=env, stdout=h, stderr=subprocess.STDOUT, cwd=out)
        secs = time.monotonic() - t0
        with open(CSV, "a", newline="") as f:
            w = csv.writer(f)
            if new and not os.path.getsize(CSV):
                f.write("# one row per chain stage run by tools/run_arm.py. seconds is wall clock "
                        "from time.monotonic around the subprocess, on a fresh copy of the seed's "
                        "growth tree; cores_busy_at_start and mem_available_gb_at_start are the "
                        "first line of /data/scrollagent/tools/machine.sh read just before the "
                        "copy, because this machine is shared with other studies. A row is written "
                        "whatever the return code.\n")
                w.writerow(HEADER)
                new = False
            w.writerow([a.tag, a.attempt, a.binary, bsha, st, "%.1f" % secs, rc, a.threads,
                        "%.1f" % busy, "%.1f" % mem, started, log, out])
        print("%s %s stage '%s' rc=%d in %.1f s" % (a.tag, a.attempt, st, rc, secs), flush=True)
        if rc != 0:
            print("stage returned non zero, stopping this arm", flush=True)
            break
    sheets = len([n for n in os.listdir(out)
                  if n.startswith("patch_") and n.endswith(".bin")])
    print("%s %s done, sheets %d" % (a.tag, a.attempt, sheets), flush=True)
    if not a.keep_tree and a.stages != "all":
        pass


if __name__ == "__main__":
    sys.exit(main())
