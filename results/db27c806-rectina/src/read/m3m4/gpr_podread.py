#!/usr/bin/env python3
"""gpr_podread.py JOBDIR (gpu-read-s4clean): runs ON THE POD (or in the mock's fake pod). Reads JOBDIR/job.json and performs its reads with the reader module
(tools/gpr_rv2gpu.py, GPR_DEVICE=cuda; or tools/gpr_stubreader.py when GPR_READER=stub, mock only). Copies, with credit, the read loop of
runs/rev1/reader-m80r-s2/tools/rs2_v2read.py read_flat (per start: read_subsets over the subsets, mean of the subset maps; final map = mean over the starts).
job.json: {"device", "reader": {"path": dir with the module, "vsrc": dir}, "weights": {label: {"file", "sha"}}, "compile": false,
           "reads": [{"name", "stack", "stack_sha", "divisor": null|number, "starts": [..], "depth": 17, "subsets": "2v"|"4v"|"1v", "direction", "weights": label}]}
Per read, under JOBDIR/out/NAME/: start<S>.npy (float32 map of that start), map.npy (mean over the starts), reads.csv (start, seconds, patches, device,
peak GPU MiB), DONE (json with the sha256 of every file). A read whose DONE exists and whose files match it is skipped (resume). Writes JOBDIR/status
(running | done | failed rc N at X) and JOBDIR/heartbeat.json after every start. Writes nothing at import. PRIVATE."""
import csv, hashlib, importlib, json, os, sys, time
import numpy as np
SUBS = {"2v": (((0, 0),), ((2, 0),)), "4v": (((0, 0), (1, 0), (2, 0), (3, 0)),), "1v": (((0, 0),),)}
SECRET = ("TOKEN", "KEY", "SECRET", "PASSWORD", "KAGGLE", "HF_", "AWS_", "RUNPOD_API")
def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()
def status(jd, txt):
    open(jd + "/status.tmp", "w").write(txt + "\n"); os.replace(jd + "/status.tmp", jd + "/status")
def fail(jd, rc, at, msg):
    status(jd, "failed rc %d at %s" % (rc, at)); print("FAILED:", at, msg, flush=True); sys.exit(rc)
def save_npy(p, a):
    if os.path.exists(p):
        raise SystemExit("REFUSED: %s exists" % p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    np.save(p[:-4] + ".part.npy", a); os.replace(p[:-4] + ".part.npy", p)
def parity(rd, fin, job, jd):
    """the known reference gate: the read against its reference (a stored CPU map, sha256 checked, or an earlier read of this job); max abs, mean abs and Pearson r against the declared tolerance"""
    ref = rd["ref"]
    if ref["kind"] == "file":
        if sha(ref["path"]) != ref["sha"]:
            fail(jd, 9, "parity", "reference %s sha256 differs" % ref["path"])
        R = np.load(ref["path"])
        src = "stored CPU map"
    else:
        R = np.load("%s/out/%s/map.npy" % (jd, ref["name"]))
        src = "earlier read " + ref["name"]
    tol = job["tol"]
    if R.shape != fin.shape:
        fail(jd, 9, "parity", "shape %s against reference %s" % (fin.shape, R.shape))
    a, b = fin.astype(np.float64), R.astype(np.float64)
    d = np.abs(a - b)
    r = float(np.corrcoef(a.ravel(), b.ravel())[0, 1]) if a.std() > 0 and b.std() > 0 else float("nan")
    w = bool(d.max() <= tol["max_abs"] and d.mean() <= tol["mean_abs"] and r == r and r >= tol["pearson_min"])
    return dict(reference=src, max_abs=float(d.max()), mean_abs=float(d.mean()), pearson=r, tol=tol, within=w)


def main(jd):
    job = json.load(open(jd + "/job.json"))
    bad = sorted(k for k in os.environ if any(s in k.upper() for s in SECRET))
    if bad:
        fail(jd, 9, "env", "token like variables in the environment: " + ",".join(bad))
    os.environ["GPR_DEVICE"] = job["device"]; os.environ["GPR_VSRC"] = job["reader"]["vsrc"]
    sys.path.insert(0, job["reader"]["path"])
    status(jd, "running")
    modname = "gpr_stubreader" if os.environ.get("GPR_READER") == "stub" else "gpr_rv2gpu"
    E = importlib.import_module(modname)
    stub = modname == "gpr_stubreader"
    torch = None
    if not stub:
        import torch
        if job["device"].startswith("cuda") and not torch.cuda.is_available():
            fail(jd, 8, "cuda", "torch.cuda.is_available() is False")
        torch.set_num_threads(int(job.get("threads", 4)))
    models = {}
    def model(label):
        if label in models:
            return models[label]
        w = job["weights"][label]
        h = sha(w["file"])
        if h != w["sha"]:
            fail(jd, 9, "weights", "sha256 %s of %s differs from %s" % (h[:12], w["file"], w["sha"][:12]))
        if stub:
            models[label] = E.build(1)
        else:
            payload = torch.load(w["file"], map_location="cpu", weights_only=True)
            E.load = lambda *a, **k: payload          # the copy of rs2_v2read.py v2_model: the weights are swapped at the load function only, sha256 checked above
            models[label] = E.build(int(job.get("threads", 4)))
        return models[label]
    t_all = time.time(); n_done = 0
    for rd in job["reads"]:
        od = "%s/out/%s" % (jd, rd["name"])
        if os.path.exists(od + "/DONE"):
            d = json.load(open(od + "/DONE"))
            if all(os.path.isfile(od + "/" + f) and sha(od + "/" + f) == h for f, h in d["files"].items()):
                print(now(), "skip (done)", rd["name"], flush=True); n_done += 1; continue
            fail(jd, 9, "resume", "%s has a DONE file whose files differ" % rd["name"])
        if sha(rd["stack"]) != rd["stack_sha"]:
            fail(jd, 9, "stack", "sha256 of %s differs" % rd["stack"])
        Z = np.load(rd["stack"], mmap_mode="r")
        subs = SUBS[rd["subsets"]]; depth = int(rd["depth"]); M = model(rd["weights"])
        rows, per = [], []
        for s in rd["starts"]:
            a = np.asarray(Z[s:s + depth])
            if a.shape[0] != depth:
                fail(jd, 9, "stack", "%s start %d: %d planes of %d" % (rd["name"], s, a.shape[0], depth))
            st = np.ascontiguousarray(a if rd.get("divisor") in (None, 0) else a.astype(np.float32) / np.float32(rd["divisor"]))
            if job.get("compile") and not stub and not getattr(M, "_gpr_compiled", False):
                E.compile_net(M, st[:, :256, :256], subsets=subs); M._gpr_compiled = True
            t0 = time.time()
            try:
                maps, npatch, _ = E.read_subsets(M, st, ensemble=True, bf16=True, direction=rd.get("direction", "forward"), subsets=subs)
            except RuntimeError as ex:
                if "802" in str(ex) or "not yet initialized" in str(ex):
                    fail(jd, 16, "cuda802", str(ex)[:200])
                raise
            m = np.mean(maps, 0).astype(np.float32)
            sec = round(time.time() - t0, 3)
            peak = int(torch.cuda.max_memory_allocated() // (1 << 20)) if (torch and job["device"].startswith("cuda")) else 0
            per.append(m)
            rows.append([s, sec, npatch, job["device"], peak])
            open(jd + "/heartbeat.json", "w").write(json.dumps(dict(t=now(), read=rd["name"], start=s, seconds=sec)))
            print(now(), rd["name"], "start", s, sec, flush=True)
        fin = np.mean(per, 0).astype(np.float32)
        save_npy(od + "/map.npy", fin)
        par = None
        if rd.get("ref"):
            par = parity(rd, fin, job, jd)
            open(od + "/parity.json", "w").write(json.dumps(par))
        with open(od + "/reads.csv", "w", newline="") as f:
            f.write("# written by tools/gpr_podread.py on the pod\n"); w = csv.writer(f); w.writerow(["start", "seconds", "patches", "device", "peak_gpu_mib"]); w.writerows(rows)
        files = sorted(x for x in os.listdir(od) if x != "DONE")
        _dn = {x: sha(od + "/" + x) for x in files}
        with open(jd + "/outputs.sha256", "a") as lf:      # (d) a partial list, appended as each read finishes (the pod job rewrites the whole list at the end)
            for x, h_ in sorted(_dn.items()):
                lf.write("%s  out/%s/%s\n" % (h_, rd["name"], x))
            lf.flush(); os.fsync(lf.fileno())
        open(od + "/DONE", "w").write(json.dumps(dict(t=now(), reads=rd["name"], files={x: sha(od + "/" + x) for x in files}, starts=len(rd["starts"]))))
        with open(jd + "/outputs.sha256", "a") as lf:
            lf.write("%s  out/%s/DONE\n" % (sha(od + "/DONE"), rd["name"])); lf.flush(); os.fsync(lf.fileno())
        n_done += 1
        if par is not None and not par["within"]:
            fail(jd, 14, "parity", "read %s against its reference: %s" % (rd["name"], json.dumps(par)))
    if n_done != len(job["reads"]):
        fail(jd, 9, "count", "%d of %d reads finished" % (n_done, len(job["reads"])))
    open(jd + "/summary.json", "w").write(json.dumps(dict(t=now(), reads_finished=n_done, reads_declared=len(job["reads"]), wall_s=round(time.time() - t_all, 1),
        torch=getattr(torch, "__version__", "stub"), cuda=getattr(getattr(torch, "version", None), "cuda", "stub"),
        gpu=(torch.cuda.get_device_name(0) if (torch and job["device"].startswith("cuda")) else "none"))))
    status(jd, "done %d of %d" % (n_done, len(job["reads"])))
if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except SystemExit:
        raise
    except Exception as e:
        import traceback; traceback.print_exc()
        status(sys.argv[1], "failed rc 1 at exception %s" % type(e).__name__); sys.exit(1)
