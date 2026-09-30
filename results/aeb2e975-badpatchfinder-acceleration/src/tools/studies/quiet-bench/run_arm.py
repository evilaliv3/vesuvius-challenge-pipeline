#!/usr/bin/env python3
"""Run the `c` stage of one seed on a FRESH COPY of its growth tree, with one of this bench's
binaries, and time it on a quiet machine.

This is c-stage-cost/tools/run_arm.py with the changes listed here and no others:

  1. S points at runs/rev1/quiet-bench, so the copy, the log and the CSV are this study's own.
     Nothing under c-stage-cost is written; its scratch/bin is only read.
  2. The binary is looked up in quiet-bench/scratch/bin/<label> first and in
     c-stage-cost/scratch/bin/<label> second, so the plain and c2 binaries this bench runs are the
     very files whose sha256 are in c-stage-cost/evidence/binaries.csv and are not rebuilt.
  3. cores_busy_at_start is taken TWICE: tools/machine.sh's own line is kept whole in the row, and
     a second one second difference of /proc/stat ticks is taken immediately before the binary
     starts, after machine.sh's `du` has finished, so the number beside the seconds is not the
     machine.sh reading of a minute earlier. Never from `ps -o pcpu`.
  4. The quiet bar is 1.0 cores busy of 24, not 22: this is a bench and a run taken beside other
     work is worth nothing. Dated addition of 2026-09-21T23:36Z, NOTE 2: the bar is not a refusal
     on the first reading, it is a WAIT. The agent sessions on this machine cost about one core
     while one of them is taking a turn and about 0.08 when none is, so a single reading can be
     over the bar for a reason that has nothing to do with the bench, and throwing the run away
     for that would lose a two hour measurement. The run waits up to WAIT_TRIES minutes for the
     reading to come under the bar and only then refuses, with the row saying how long it waited.
     Every reading is a five second difference of /proc/stat ticks, never one second and never
     ps -o pcpu.
  5. A cap is recorded in its own two columns, cap_seconds and cap_bit, so a bound can never be
     read as a time. run_arm.py of c-stage-cost had the cap and did not record it.
  6. The copied tree is removed as soon as the row is written, unless --keep-tree, because this
     bench runs nine to eleven of them and identity is not measured here.
  7. repeat_index and free space on /data before the copy are columns.

Usage:
  run_arm.py --binary <label> --attempt PHerc1447-seedNN --tag <tag> [--repeat-index N]
             [--threads 4] [--cap SECONDS] [--keep-tree]
"""
import argparse, csv, hashlib, os, re, shutil, subprocess, sys, time

S = "/data/scrollagent/runs/rev1/quiet-bench"
BIN_DIRS = [os.path.join(S, "scratch", "bin"),
            "/data/scrollagent/runs/rev1/c-stage-cost/scratch/bin"]
SEEDS = "/data/scrollagent/runs/rev1/seed-search-1447/out"
ZARR = "/data/scrollagent/data/datasets/PHerc1447/0"
CHUNKS = "/data/scrollagent/data/datasets/PHerc1447/chunks.txt"
MACHINE = "/data/scrollagent/tools/machine.sh"
CSV = os.path.join(S, "evidence", "c-stage-runs.csv")
QUIET_BAR = 1.0
WAIT_TRIES = 40        # minutes a run waits for the machine to come under the bar
WAIT_WINDOW = 5.0      # seconds each /proc/stat reading is taken over
MEM_FLOOR_GB = 20.0
HEADER = [
    "tag",                    # the arm, as this bench names it
    "attempt",                # the seed whose growth tree was copied and run
    "repeat_index",           # 1, 2, 3 within the arm on that seed
    "binary_label",           # which build was run
    "binary_path",            # where it was read from
    "binary_sha256",          # its sha256, read at the moment of the run
    "stage",                  # always c in this bench
    "seconds",                # wall clock, time.monotonic around the subprocess
    "return_code",            # what the stage returned, or refused-by-bar
    "cap_seconds",            # the timeout the run was given, empty when none
    "cap_bit",                # yes when the cap stopped it, so the seconds are a LOWER BOUND
    "omp_num_threads",        # the thread budget
    "cores_busy_at_start",    # /proc/stat ticks over five seconds, taken just before the binary
    "cores_busy_machine_sh",  # the same quantity as tools/machine.sh read it before the copy
    "minutes_waited_for_quiet",   # how long the run waited for the reading to come under the bar
    "quiet_bar",              # the bar in cores busy of 24 this run was held to
    "mem_available_gb_at_start",
    "data_free_gb_before_copy",
    "started_utc",
    "machine_line",
    "log",
    "out_dir",
]


def proc_stat_busy(window=WAIT_WINDOW):
    def read():
        with open("/proc/stat") as f:
            p = f.readline().split()
        u, n, s, i = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
        return u, n, s, i
    u1, n1, s1, i1 = read()
    time.sleep(window)
    u2, n2, s2, i2 = read()
    du, dn, ds, di = u2 - u1, n2 - n1, s2 - s1, i2 - i1
    t = du + dn + ds + di
    return 0.0 if t <= 0 else 24.0 * (du + dn + ds) / t


def wait_for_quiet(what):
    """Wait until the machine reads under the bar. Returns (busy, minutes waited) or (busy, None)
    when it never came under it, and the caller decides what that means."""
    for i in range(WAIT_TRIES):
        b = proc_stat_busy()
        if b <= QUIET_BAR:
            return b, i
        print("%s: cores busy %.2f above the bar of %.1f, waiting (%d of %d)"
              % (what, b, QUIET_BAR, i, WAIT_TRIES), flush=True)
        time.sleep(60)
    return proc_stat_busy(), None


def machine():
    line = subprocess.check_output(["bash", MACHINE]).decode().splitlines()[0]
    busy = float(re.search(r"cores busy ([0-9.]+)", line).group(1))
    mem = float(re.search(r"MemAvailable ([0-9.]+)", line).group(1))
    return busy, mem, line


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def data_free_gb():
    out = subprocess.check_output(["df", "-B1G", "/data"]).decode().splitlines()[1].split()
    return int(out[3])


def append(row):
    new = not os.path.exists(CSV)
    with open(CSV, "a", newline="") as f:
        if new:
            f.write("# one row per `c` stage run of the quiet bench of PLAN 58. seconds is wall "
                    "clock from time.monotonic around the subprocess, on a FRESH COPY of the "
                    "seed's growth tree made with cp -a; nothing under seed-search-1447 is "
                    "written. cores_busy_at_start is a FIVE second difference of /proc/stat ticks "
                    "taken immediately before the binary starts, never ps -o pcpu; "
                    "cores_busy_machine_sh is the same quantity as tools/machine.sh read it "
                    "before the copy. A row with cap_bit=yes has seconds that are a LOWER BOUND "
                    "and not a time: the run was stopped by timeout -s TERM at cap_seconds. A row "
                    "with return_code=refused-by-bar never ran: cores busy was above this study's "
                    "quiet bar of 1.0 of 24.\n")
            csv.writer(f).writerow(HEADER)
        csv.writer(f).writerow(row)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--attempt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--repeat-index", type=int, default=1)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--cap", type=int, default=0, help="seconds, 0 is no cap")
    ap.add_argument("--keep-tree", action="store_true")
    a = ap.parse_args()

    binary = None
    for d in BIN_DIRS:
        p = os.path.join(d, a.binary, "simpaper10")
        if os.access(p, os.X_OK):
            binary = p
            break
    if binary is None:
        raise SystemExit("no binary called %s under %s" % (a.binary, BIN_DIRS))
    bsha = sha256(binary)
    growth = os.path.join(SEEDS, a.attempt, "growth")
    patches = os.path.join(growth, "patches")
    if not os.path.isdir(patches) or len(os.listdir(patches)) == 0:
        raise SystemExit("no growth tree with patches in it at %s" % growth)

    busy_m, mem, line = machine()
    free_before = data_free_gb()
    print("machine: " + line, flush=True)
    if mem < MEM_FLOOR_GB:
        raise SystemExit("MemAvailable %.1f GB is below the floor of %.1f" % (mem, MEM_FLOOR_GB))
    # the gate, before the copy: wait for the machine, and only refuse when it never comes quiet
    gate_busy, gate_waited = wait_for_quiet("gate")
    if gate_waited is None:
        append([a.tag, a.attempt, a.repeat_index, a.binary, binary, bsha, "c", "", "refused-by-bar",
                a.cap or "", "", a.threads, "%.2f" % gate_busy, "%.1f" % busy_m, WAIT_TRIES,
                QUIET_BAR, "%.1f" % mem, free_before,
                subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip(), line, "", ""])
        raise SystemExit("cores busy %.2f never came under this bench's bar of %.1f in %d minutes,"
                         " refused" % (gate_busy, QUIET_BAR, WAIT_TRIES))

    out = os.path.join(S, "scratch", "out", a.tag, a.attempt, "C40")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        shutil.rmtree(out)
    print("copying %s to %s" % (growth, out), flush=True)
    subprocess.check_call(["cp", "-a", growth, out])

    env = dict(os.environ, SIMPAPER_OUTPUT_DIR=out, SIMPAPER_SURFACE_ZARR=ZARR,
               ZARR_MISSING_LIST=os.path.join(out, "missing-C40.txt"),
               ZARR_CHUNK_MANIFEST=CHUNKS, SIMPAPER_PATCH_LIMIT="40000",
               OMP_NUM_THREADS=str(a.threads), TMPDIR="/data/tmp")
    log = os.path.join(S, "log", "c-%s-%s-r%d.txt" % (a.tag, a.attempt, a.repeat_index))
    cmd = [binary, "c"]
    if a.cap:
        cmd = ["timeout", "-s", "TERM", str(a.cap)] + cmd

    # the copy is 1 to 3 GB of our own input output and its tail is still on the machine when it
    # returns, so the reading that goes in the row is taken after it and is waited for like the
    # gate. If it never comes under the bar the run is taken anyway and the row carries the
    # reading it was taken at: a measurement with its machine written beside it is worth more
    # than no measurement, and the column says which it is.
    busy, waited = wait_for_quiet("before the binary")
    started = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    t0 = time.monotonic()
    with open(log, "wb") as h:
        rc = subprocess.call(cmd, env=env, stdout=h, stderr=subprocess.STDOUT, cwd=out)
    secs = time.monotonic() - t0
    # timeout returns 124 when it fired; -15 would be a TERM this process did not send
    cap_bit = "yes" if (a.cap and rc in (124, 137, -15)) else ("no" if a.cap else "")
    append([a.tag, a.attempt, a.repeat_index, a.binary, binary, bsha, "c", "%.1f" % secs, rc,
            a.cap or "", cap_bit, a.threads, "%.2f" % busy, "%.1f" % busy_m,
            gate_waited + (waited if waited is not None else WAIT_TRIES), QUIET_BAR,
            "%.1f" % mem, free_before, started, line, log, out])
    print("%s %s r%d rc=%d in %.1f s, cores busy at start %.2f, cap_bit=%s"
          % (a.tag, a.attempt, a.repeat_index, rc, secs, busy, cap_bit), flush=True)
    if not a.keep_tree:
        shutil.rmtree(out, ignore_errors=True)
        print("copy removed", flush=True)


if __name__ == "__main__":
    sys.exit(main())
