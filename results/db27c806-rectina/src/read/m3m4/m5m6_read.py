#!/usr/bin/env python3
"""m5m6_read.py CHECKPOINT READS_JSON OUTDIR: the pod side read command of the M5/M6 chain (stdlib only; it starts the registered GPU read job).
It builds a job.json for gpr_podread.py (runs/rev1/gpu-read-s4clean/tools, byte copy shipped as gpr_podread.py) with the reader module gpr_rv2gpu.py (byte copy, a copy of
rv2read_ens_v6: the lattice follows the checkpoint's crop, 4 origins, 2 views (0,0) and (2,0), starts as in reads.json), reads every unit of reads.json and
copies out/<unit>/{map.npy,DONE,reads.csv} to OUTDIR/<unit>/ (job files in ../readjob). Environment: M5M6_READ_DEVICE (cuda default, cpu for tests), M5M6_VSRC (the vesuvius src tree whose
InkConfig and make_model build the model: the patched main tree), M5M6_STACKROOT (folder holding the stack files named in reads.json), M5M6_THREADS.
reads.json: {"starts": [0..6], "subsets": "2v", "depth": 17, "units": [{"unit", "stack": file name under M5M6_STACKROOT, "stack_sha256", "divisor", "arm", "source"}]}"""
import hashlib, json, os, shutil, subprocess, sys
ck, spec, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.getsize(p) < (1 << 31) else subprocess.check_output(["sha256sum", p], text=True).split()[0]
S = json.load(open(spec)); root = os.environ["M5M6_STACKROOT"]
jd = os.path.dirname(out.rstrip("/")) + "/readjob"; os.makedirs(jd, exist_ok=True); os.makedirs(out, exist_ok=True)      # job files beside OUTDIR, so only the maps are pulled
job = dict(device=os.environ.get("M5M6_READ_DEVICE", "cuda"), threads=int(os.environ.get("M5M6_THREADS", "4")), compile=False,
           reader=dict(path=here, vsrc=os.environ["M5M6_VSRC"]), weights={"m": dict(file=ck, sha=sha(ck))},
           reads=[dict(name=u["unit"], stack=root + "/" + u["stack"], stack_sha=u["stack_sha256"], divisor=u["divisor"], starts=S.get("starts", list(range(7))),
                       depth=S.get("depth", 17), subsets=S.get("subsets", "2v"), direction="forward", weights="m") for u in S["units"]])
json.dump(job, open(jd + "/job.json", "w"), indent=1)
SECRET = ("TOKEN", "KEY", "SECRET", "PASSWORD", "KAGGLE", "HF_", "AWS_", "RUNPOD_API")      # gpr_podread.py refuses a pod environment holding these
env = {k: v for k, v in os.environ.items() if not any(x in k.upper() for x in SECRET)}
rc = subprocess.run([sys.executable, here + "/gpr_podread.py", jd], env=env).returncode
for u in S["units"]:
    m = "%s/out/%s/map.npy" % (jd, u["unit"])
    if os.path.isfile(m):      # the layout m5_score.py reads: <maps>/<unit>/map.npy (+ DONE and reads.csv beside it)
        os.makedirs("%s/%s" % (out, u["unit"]), exist_ok=True)
        for f in ("map.npy", "DONE", "reads.csv"):
            if os.path.isfile("%s/out/%s/%s" % (jd, u["unit"], f)):
                shutil.copyfile("%s/out/%s/%s" % (jd, u["unit"], f), "%s/%s/%s" % (out, u["unit"], f))
sys.exit(rc)
