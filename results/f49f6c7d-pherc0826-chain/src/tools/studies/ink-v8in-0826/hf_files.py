#!/usr/bin/env python3
"""hf_files.py (ink-v8in-0826): sha256 and size of every downloaded file of the pinned HF revision (scratch/hf/repo and
scratch/hf/ds1447), beside the API JSON's size and LFS sha256 where it gives one; a match column; and the parameter count
of model.safetensors summed over its tensors. Writes evidence/hf-files.csv (overwrites: a listing, not a measurement)."""
import csv, hashlib, json, os, subprocess, sys
S = "/data/scrollagent/runs/rev1/ink-v8in-0826"
now = subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip()
rows = []
for repo, api, root in (("YoussefMoNader/ink-8um-v8in", "api-model.json", "repo"), ("YoussefMoNader/ink-8um-pherc1447-surfaces", "api-dataset.json", "ds1447")):
    A = json.load(open(f"{S}/scratch/hf/{api}"))
    sib = {s["rfilename"]: s for s in A["siblings"]}
    base = f"{S}/scratch/hf/{root}"
    for dp, dn, fn in os.walk(base):
        if "/.cache" in dp or dp.endswith(".cache"):
            continue
        for f in sorted(fn):
            p = os.path.join(dp, f); rel = os.path.relpath(p, base)
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                for b in iter(lambda: fh.read(1 << 24), b""):
                    h.update(b)
            s = sib.get(rel, {})
            lfs = (s.get("lfs") or {}).get("sha256", "")
            size_ok = "yes" if s.get("size") == os.path.getsize(p) else ("not in API list" if not s else "NO")
            rows.append([now, repo, A["sha"], rel, os.path.getsize(p), h.hexdigest(), s.get("size", ""), lfs,
                         ("yes" if lfs == h.hexdigest() else "NO") if lfs else "no LFS sha in API (git blob %s)" % s.get("blobId", "?"), size_ok])
from safetensors import safe_open
n = 0; k = 0
with safe_open(f"{S}/scratch/hf/repo/model.safetensors", "pt") as f:
    for key in f.keys():
        t = f.get_slice(key); sh = t.get_shape(); m = 1
        for d in sh:
            m *= d
        n += m; k += 1
out = f"{S}/evidence/hf-files.csv"
with open(out, "w", newline="") as fh:
    fh.write("# written by ink-v8in-0826/tools/hf_files.py: sha256 of every downloaded file of the pinned revisions, API size and LFS sha beside\n")
    w = csv.writer(fh)
    w.writerow(["read_at", "repo", "revision", "file", "bytes", "sha256", "api_bytes", "api_lfs_sha256", "sha_matches_api", "size_matches_api"])
    w.writerows(rows)
    w.writerow([now, "YoussefMoNader/ink-8um-v8in", "", "model.safetensors PARAMETERS", n, "tensors %d" % k, "", "", "", ""])
print(len(rows), "files; parameters", n, "in", k, "tensors")
