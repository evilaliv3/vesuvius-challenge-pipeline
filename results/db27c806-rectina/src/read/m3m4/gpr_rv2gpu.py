# COPY (credit) of runs/rev1/five-model-bench/tools/fmb_rv2read_2j.py sha256 7ab189b37e342e1e9d789ab670d6fbc6d0f2466e567daf63701b8fe043afc896 for gpu-read-s4clean, made by tools/gpr_copy.py; edits, and no others, listed in meta/gpr-rv2gpu-edits.csv: device (GPR_DEVICE, default cpu), vsrc path (GPR_VSRC), model .to(DEV), input .to(DEV), autocast on the device, output .cpu(). PRIVATE.
"""fmb_rv2read_2j.py: a copy of tools/rv2read/rv2read_ens_v6.py (sha256 ed2bbe6cf9d0923af88e8c0a398a9c7f323a060a4706d2361e3ba3995a94efd0) for five-model-bench part 2j; the read lattice FOLLOWS THE CHECKPOINT's crop: patch 128 (s1, s2), 256 (s3) or 384 (Reader v3 stock, s4); stride = round(patch x 0.5), the Hann window, the shifted-lattice ensemble (patch/4) and the compile warm-up use that patch; the guard stays: depth must be 17 and the patch one of 128, 256, 384, else STOP naming both. Everything else is the v6 text. New file, 2026-10-30, study agent."""
"""rv2read_ens_v6.py (CANDIDATE; becomes the research read default only after the owner's yes, rows owner-adopt-4-views and
owner-4-views-three-checks; gate «rv2read-ens-v6-registered»): v5 (rv2read_ens_v5.py, sha 1c99405a1bd4: v1 with the per-patch buffer float32)
plus the 4 dihedral views, as an option that is the DEFAULT of read(). Built as a COPY of rv2read_ens_v2.py (sha d6f61a3c1fdd, FROZEN, credit;
itself v1 copied unchanged plus the views) with v5's one change applied at the same place (the patch buffer np.float32 instead of np.uint8,
rv2read_ens.py:202 = rv2read_ens_v2.py:233), so:
  read(m, stack, ensemble=True, bf16=True, direction="forward", views=VIEWS4)
                 returns (float32 map, patches, predict seconds) like v1/v5; views=VIEWS4 (the four rotations, avg1's arm v2-4) by default;
                 views=VIEWS1 is v5's read (v2's code path with one view is v1's: same batches, order and arithmetic)
  read_subsets(m, stack, ..., subsets)   v2's read() unchanged: one map per view subset from one pass (the union of the subsets' views)
  compile_net(m, stack, subsets=(VIEWS4,))  the warm-up with the views that will be read
VIEWS1, VIEWS4, VIEWS8, view(), unview(), predict_shift() as in v2 (credit). Nothing is written at import. PRIVATE."""
import hashlib, os, re, sys, time
import numpy as np

S_RV2 = "/data/scrollagent/runs/rev1/reader-v2-trial"
VSRC = os.environ.get("GPR_VSRC", S_RV2 + "/scratch/vsrc")
WEIGHTS = S_RV2 + "/scratch/weights/reader-v2-step040000.pth"
FETCH_LOG = S_RV2 + "/scratch/weights/fetch.log"
SHA256 = "654ec5acec2b6c4788d9cb326e2f0b8c2c730584949a934ef775db7f6ab5d3a6"
SECRET_NAME = re.compile(r"TOKEN|KEY|SECRET|PASSWORD|KAGGLE", re.I)
PATCH, DEPTH, OVERLAP = 128, 17, 0.5
SHIFTS = ((0, 0), (32, 0), (0, 32), (32, 32))
DEFAULT = dict(ensemble=True, bf16=True)
DEV = os.environ.get("GPR_DEVICE", "cpu")      # gpu-read-s4clean: "cpu" (neutral, the original path) or "cuda"
AC_DEV = "cuda" if DEV.startswith("cuda") else "cpu"


class Refused(SystemExit):
    pass


# ---- the checkpoint (load_rv2.py:25-57, credit)
def check(path=WEIGHTS, fetch_log=FETCH_LOG, env=None, home=None, sha=SHA256):
    env = dict(os.environ) if env is None else env
    home = env.get("HOME", "") if home is None else home
    if not os.path.isfile(fetch_log):
        raise Refused("REFUSED: %s absent" % fetch_log)
    lines = [l.strip() for l in open(fetch_log) if l.strip()]
    last = lines[-1].split() if lines else []
    if not last or last[-1] != "ok" or (len(last) > 1 and sha not in last):
        raise Refused("REFUSED: fetch.log does not end with «ok»")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    if h.hexdigest() != sha:
        raise Refused("REFUSED: sha256 %s differs from the published %s" % (h.hexdigest(), sha))
    bad = sorted(k for k in env if SECRET_NAME.search(k))
    if bad:
        raise Refused("REFUSED: token like variables in the environment: %s" % ", ".join(bad))
    for p in (os.path.join(home, ".kaggle", "kaggle.json"), os.path.join(home, ".cache", "huggingface", "token")):
        if home and os.access(p, os.R_OK):
            raise Refused("REFUSED: a token file is readable from this process: %s" % p)
    return h.hexdigest()


def load(path=WEIGHTS):
    check(path)
    import torch
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except Exception as e:
        raise Refused("STOP: torch.load(weights_only=True) failed: %s: %s" % (type(e).__name__, e))


# ---- the lattice (rv2_lattice.py:24-54, credit)
def stride(overlap=OVERLAP, patch=PATCH):
    if not 0.0 <= overlap < 1.0:
        raise ValueError("overlap must be in [0, 1)")
    return max(1, int(round(float(patch) * (1.0 - overlap))))


def centre_layers(n, depth=DEPTH):
    idx = np.arange(int(n), dtype=np.int64)
    if idx.size <= depth:
        return idx
    s = idx.size // 2 - depth // 2
    return idx[s:s + depth]


def positions(length, patch=PATCH, st=None):
    st = stride(patch=patch) if st is None else int(st)      # 2j: the default stride follows the patch
    length = int(length)
    if length <= patch:
        return [0]
    p = list(range(0, max(1, length - patch + 1), st))
    if p[-1] != length - patch:
        p.append(length - patch)
    return p


def hann(patch=PATCH):
    n = np.arange(patch, dtype=np.float64)
    w = 0.5 - 0.5 * np.cos(2.0 * np.pi * n / (patch - 1))
    m = np.outer(w, w).astype(np.float32)
    m /= max(float(m.max()), float(np.finfo(np.float32).eps))
    return np.maximum(m, np.float32(1e-3))


PATCHES = (128, 256, 384)      # 2j: the patch sizes a checkpoint may carry; the lattice follows it


def check_crop(depth, patch, crop=None):
    """2j: the guard (it was: crop must equal (17, 128, 128)); now depth 17 and a patch of PATCHES, a square crop"""
    if depth != DEPTH or patch not in PATCHES:
        raise SystemExit("STOP: checkpoint crop %s is not (17, P, P) with P in %s: the lattice follows the checkpoint only for these" % (crop if crop is not None else (depth, patch, patch), PATCHES))


# ---- the model (rv2_infer.py:32-66, credit)
class Model:
    pass


def build(threads=6):
    import torch
    torch.set_num_threads(int(threads))
    payload = load()
    if VSRC not in sys.path:
        sys.path.insert(0, VSRC)
    from vesuvius.ink_detection.config import InkConfig
    from vesuvius.ink_detection.models.model import make_model
    from vesuvius.ink_detection.inference.inference_runtime import TargetModel
    if not isinstance(payload, dict) or not isinstance(payload.get("config"), dict):
        raise SystemExit("STOP: checkpoint has no config mapping")
    for key in ("state_dict", "model_state_dict", "model"):
        if isinstance(payload.get(key), dict):
            state = payload[key]; break
    else:
        raise SystemExit("STOP: no supported state in the checkpoint: keys %s" % sorted(payload))
    if state and all(str(k).startswith("module.") for k in state):
        state = {str(k)[7:]: v for k, v in state.items()}
    cfg = InkConfig.from_mapping(payload["config"])
    if cfg.data.mode != "flat":
        raise SystemExit("STOP: checkpoint mode %r is not flat" % cfg.data.mode)
    base = make_model(cfg)
    base.load_state_dict(state, strict=True)
    m = Model()
    m.net = TargetModel(base.eval(), input_pad_depth_to=cfg.model.input_pad_depth_to).eval().to(DEV)
    m.depth, m.patch = int(cfg.model.crop_size[0]), int(cfg.model.crop_size[1])
    m.norm = cfg.data.normalization
    check_crop(m.depth, m.patch, cfg.model.crop_size)
    if m.norm.mode != "robust_mad" or (m.norm.percentile_lower, m.norm.percentile_upper) != (1.0, 99.0):
        raise SystemExit("STOP: normalisation %r is not robust_mad 1/99" % (m.norm,))
    m.normalize = None
    return m


def normalizer(m):
    """villa's normalize_robust from VSRC (rv2_infer.py:71, credit), or the model's own stand-in in tests"""
    if getattr(m, "normalize", None) is not None:
        return m.normalize
    if VSRC not in sys.path:
        sys.path.insert(0, VSRC)
    from vesuvius.image_proc.intensity.normalization import normalize_robust
    return normalize_robust




VIEWS1 = ((0, 0),)
VIEWS4 = ((0, 0), (1, 0), (2, 0), (3, 0))
VIEWS8 = ((0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1))


def view(a, v):
    """forward view (k, f) on the last two axes: mirror x if f, then k quarter turns"""
    k, f = v
    if f:
        a = a[..., ::-1]
    return np.rot90(a, k, axes=(-2, -1))


def unview(a, v):
    """the inverse of view(): -k quarter turns, then the same mirror"""
    k, f = v
    a = np.rot90(a, -k, axes=(-2, -1))
    if f:
        a = a[..., ::-1]
    return a


# ---- one lattice with views (rv2read_ens.predict_shift, credit; views added)
def predict_shift(m, stack_dhw, shift, direction="forward", batch=8, st=None, bf16=False, subsets=(VIEWS1,)):
    """returns ([one map per subset], patches, seconds); the model sees every view of the union of the subsets once"""
    import torch
    norm = normalizer(m)
    allv = []
    for sub in subsets:
        for v in sub:
            if v not in allv:
                allv.append(v)
    pos = {v: i for i, v in enumerate(allv)}
    oy, ox = int(shift[0]), int(shift[1])
    if oy < 0 or ox < 0:
        raise SystemExit("REFUSED: shift %s" % (shift,))
    if oy or ox:
        stack_dhw = np.pad(np.asarray(stack_dhw), ((0, 0), (oy, 0), (ox, 0)))
    D, H, W = stack_dhw.shape
    idx = centre_layers(D, m.depth)
    if direction == "reverse":
        idx = idx[::-1]
    elif direction != "forward":
        raise SystemExit("REFUSED: direction %r" % direction)
    if idx.size != m.depth:
        raise SystemExit("REFUSED: %d layers, the model needs %d" % (D, m.depth))
    P = m.patch
    st = stride(patch=P) if st is None else st     # 2j: the stride follows the patch (it was the 128 px default)
    hw = hann(P)
    ps = [np.zeros((H, W), np.float32) for _ in subsets]; ws = np.zeros((H, W), np.float32)
    pts = [(y, x) for y in positions(H, P, st) for x in positions(W, P, st)]
    n = 0; t0 = time.time()
    buf, meta = [], []

    def flush():
        nonlocal n
        if not buf:
            return
        x = np.stack([np.ascontiguousarray(view(b, v)) for b in buf for v in allv]) if allv != [(0, 0)] else np.stack(buf)
        with torch.inference_mode():
            if bf16:
                with torch.autocast(AC_DEV, dtype=torch.bfloat16):
                    lg = m.net(torch.from_numpy(x)[:, None].to(DEV))
            else:
                lg = m.net(torch.from_numpy(x)[:, None].to(DEV))
            if lg.ndim != 4:
                raise SystemExit("STOP: logits shape %s" % (tuple(lg.shape),))
            pr = lg.float().sigmoid().cpu().numpy()[:, 0]
        if pr.shape[-2:] != (P, P):
            raise SystemExit("STOP: output %s is not %d x %d" % (pr.shape, P, P))
        nv = len(allv)
        for j, (y, x0, h, w) in enumerate(meta):
            back = {v: (pr[j * nv + pos[v]] if allv == [(0, 0)] else unview(pr[j * nv + pos[v]], v)) for v in allv}
            for si, sub in enumerate(subsets):
                t = back[sub[0]] if len(sub) == 1 else np.mean([back[v] for v in sub], 0).astype(np.float32)
                ps[si][y:y + h, x0:x0 + w] += t[:h, :w] * hw[:h, :w]
            ws[y:y + h, x0:x0 + w] += hw[:h, :w]
        n += len(buf); buf.clear(); meta.clear()

    for (y, x) in pts:
        h, w = min(P, H - y), min(P, W - x)
        raw = np.zeros((m.depth, P, P), np.float32)   # v5's change (rv2read_ens.py:202, rv2read_ens_v5.py): a float stack is not truncated
        raw[:, :h, :w] = np.asarray(stack_dhw[idx, y:y + h, x:x + w]) if direction == "forward" else \
            np.asarray(stack_dhw[np.sort(idx), y:y + h, x:x + w])[::-1]
        if not raw.any():
            continue
        buf.append(np.ascontiguousarray(norm(raw.astype(np.float32)), dtype=np.float32))
        meta.append((y, x, h, w))
        if len(buf) >= batch:
            flush()
    flush()
    outs = []
    for p in ps:
        prob = np.zeros((H, W), np.float32)
        np.divide(p, ws, out=prob, where=ws > 1e-6)
        np.clip(prob, 0.0, 1.0, out=prob)
        outs.append(prob[oy:, ox:])
    return outs, n, time.time() - t0


# ---- compile (rv2read_ens.compile_net, credit)
def compile_net(m, stack_dhw, subsets=(VIEWS4,)):
    import torch
    base_net = m.net
    m.net = torch.compile(base_net)
    tw = time.time()
    predict_shift(m, np.asarray(stack_dhw)[:, :2 * m.patch, :2 * m.patch], (0, 0), "forward", bf16=True, subsets=subsets)
    if type(m.net) is type(base_net):
        raise SystemExit("REFUSED: torch.compile returned the module unchanged")
    return round(time.time() - tw, 1), "%s wraps %s" % (type(m.net).__name__, type(base_net).__name__)


# ---- the read (rv2read_ens.read, credit; subsets added)
def read_subsets(m, stack_dhw, ensemble=True, bf16=True, direction="forward", subsets=(VIEWS4,)):
    """rv2read_ens_v2.read (credit): one float32 map per view subset: the mean of the four lattice maps (ensemble) or the shift-0 map"""
    q = m.patch // 4                                   # 2j: the ensemble shifts are a quarter patch (32 px at 128, 64 at 256, 96 at 384)
    shifts = ((0, 0), (q, 0), (0, q), (q, q)) if ensemble else ((0, 0),)
    per = [[] for _ in subsets]; npatch, sec = 0, 0.0
    for sh in shifts:
        maps, n, s = predict_shift(m, stack_dhw, sh, direction, bf16=bf16, subsets=subsets)
        for i, p in enumerate(maps):
            per[i].append(p)
        npatch += n; sec += s
    out = [(L[0] if len(L) == 1 else np.mean(L, 0).astype(np.float32)) for L in per]
    return out, npatch, sec


# ---- v6: the default read with the 4 views
def read(m, stack_dhw, ensemble=True, bf16=True, direction="forward", views=VIEWS4):
    """v1/v5's signature and return (map, patches, seconds); views VIEWS4 by default, VIEWS1 = v5"""
    if tuple(views) not in (VIEWS1, VIEWS4, VIEWS8):
        raise SystemExit("REFUSED: views %r" % (views,))
    out, npatch, sec = read_subsets(m, stack_dhw, ensemble, bf16, direction, subsets=(tuple(views),))
    return out[0], npatch, sec
