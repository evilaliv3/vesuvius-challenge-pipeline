#!/usr/bin/env python3
"""fetch_level_slice.py (papyrus-figures-2026-09-28): the chunks of ONE z plane of a coarse level of the PHerc. 1447
raw masked scan, into the home's shared raw chunk cache (tools/raw_chunk_cache.py), so that figure S7 of work
aeb2e975 can draw that plane without fetching anything itself.

    fetch_level_slice.py <level> <z in level-0 voxels> [<z> ...] [--streams 8]

The plane of level L that holds level-0 voxel z is z // 2**L (the scale factors 1, 2, 4, 8, 16, 32 of the zarr's own
.zattrs multiscales, read 2026-09-28T06:5xZ). Every chunk (z // 2**L // 128, cy, cx) for cy, cx over the level's
shape is fetched once; a 404 is recorded absent (the scan is masked and whole chunks outside the mask are absent).
Writes evidence/level-slice-fetch.csv, one row per plane, with the counts that must add up.
"""
import argparse, csv, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

import requests

sys.path.insert(0, "/data/scrollagent/tools")
import raw_chunk_cache as RC  # noqa: E402

TOOL = "papyrus-figures-2026-09-28/tools/fetch_level_slice.py"
BASE = "https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHerc1447/volumes/20250521151220-8.640um-1.2m-116keV-masked.zarr"
OUT = "/data/scrollagent/runs/rev1/papyrus-figures-2026-09-28/evidence/level-slice-fetch.csv"
CH = 128


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level", type=int)
    ap.add_argument("z", type=int, nargs="+")
    ap.add_argument("--streams", type=int, default=8)
    a = ap.parse_args()
    meta = requests.get("%s/%d/.zarray" % (BASE, a.level), timeout=60).json()
    shape = meta["shape"]
    if meta["chunks"] != [CH, CH, CH] or meta["compressor"] is not None:
        raise SystemExit("level %d: chunks %r compressor %r, not the raw 128 cubed layout" % (a.level, meta["chunks"], meta["compressor"]))
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        if new:
            fh.write("# written by %s. One row per plane: chunks_needed = chunks_already_cached + chunks_fetched + "
                     "chunks_absent_404 + chunks_failed, checked in adds_up. level_shape is the .zarray shape of that level.\n" % TOOL)
        w = csv.writer(fh)
        if new:
            w.writerow(["utc", "level", "z_level0", "z_level", "chunk_z", "level_shape", "chunks_needed", "chunks_already_cached",
                        "chunks_fetched", "chunks_absent_404", "chunks_failed", "bytes_over_wire", "adds_up"])
        for z0 in a.z:
            zl = z0 // (2 ** a.level)
            cz = zl // CH
            need = [(cz, cy, cx) for cy in range((shape[1] + CH - 1) // CH) for cx in range((shape[2] + CH - 1) // CH)]
            todo = [c for c in need if not RC.lookup("PHerc1447", None, a.level, *c)]
            t = {"ok": 0, "absent": 0, "failed": 0, "bytes": 0}

            def one(c):
                for attempt in range(5):
                    try:
                        r = requests.get("%s/%d/%d/%d/%d" % ((BASE, a.level) + c), timeout=60)
                    except requests.RequestException:
                        time.sleep(1 + attempt)
                        continue
                    if r.status_code == 404:
                        RC.store_absent("PHerc1447", None, a.level, *c)
                        t["absent"] += 1
                        return
                    if r.status_code == 200 and len(r.content) == CH ** 3:
                        RC.store("PHerc1447", None, a.level, *c, r.content)
                        t["ok"] += 1
                        t["bytes"] += len(r.content)
                        return
                    time.sleep(1 + attempt)
                t["failed"] += 1

            with ThreadPoolExecutor(a.streams) as ex:
                list(ex.map(one, todo))
            utc = subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True).stdout.strip()
            adds = len(need) == (len(need) - len(todo)) + t["ok"] + t["absent"] + t["failed"]
            w.writerow([utc, a.level, z0, zl, cz, json.dumps(shape), len(need), len(need) - len(todo), t["ok"], t["absent"],
                        t["failed"], t["bytes"], "yes" if adds else "no"])
            print("level %d z0 %d plane %d: %d needed, %d fetched, %d absent, %d failed" % (a.level, z0, zl, len(need), t["ok"], t["absent"], t["failed"]))


if __name__ == "__main__":
    main()
