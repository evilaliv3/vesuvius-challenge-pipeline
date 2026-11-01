#!/usr/bin/env python3
"""rectina_read: read a rendered surface stack with a Rectina ink checkpoint (m1 or m2) and write an ink score map.

MIT licence. The read recipe is the one that produced the maps of the Rectina article: per start, a window of 17 consecutive planes of
the stack, a lattice of square patches (patch 128 for m1, 384 for m2, taken from the checkpoint), four lattices shifted by a quarter
patch, two views (as is and turned by 180 degrees), a Hann blend, bf16 on the GPU; the map is the mean over the starts.
The map is a ranking score between 0 and 1. It is not a calibrated probability.

Commands
  rectina_read.py read    --stack S --checkpoint C --out DIR --villa-src DIR [--device cuda|cpu] [--starts 0 1 2 3 4 5 6]
  rectina_read.py compare MAP REFERENCE [--max-abs 0.05 --mean-abs 0.005 --pearson 0.995]
  rectina_read.py info    --checkpoint C

Model code: the architecture is built by villa's ink_detection package (see README.md for the pinned commit); this file only
supplies the lattice, the views, the blend and the files.
"""
import argparse, csv, hashlib, json, os, sys, time
import numpy as np

DEPTH = 17
PATCHES = (128, 256, 384)
OVERLAP = 0.5
VIEWS = {"2v": ((0, 0), (2, 0)), "1v": ((0, 0),), "4v": ((0, 0), (1, 0), (2, 0), (3, 0))}
DIVISOR_UINT16 = 65280.0
TOLERANCE = dict(max_abs=0.05, mean_abs=0.005, pearson=0.995)


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


# ---- lattice -----------------------------------------------------------------------------------------------------------
def stride(patch):
    return max(1, int(round(patch * (1.0 - OVERLAP))))


def positions(length, patch):
    if length <= patch:
        return [0]
    p = list(range(0, max(1, length - patch + 1), stride(patch)))
    if p[-1] != length - patch:
        p.append(length - patch)
    return p


def centre_layers(n, depth=DEPTH):
    idx = np.arange(int(n), dtype=np.int64)
    if idx.size <= depth:
        return idx
    s = idx.size // 2 - depth // 2
    return idx[s:s + depth]


def hann(patch):
    n = np.arange(patch, dtype=np.float64)
    w = 0.5 - 0.5 * np.cos(2.0 * np.pi * n / (patch - 1))
    m = np.outer(w, w).astype(np.float32)
    m /= max(float(m.max()), float(np.finfo(np.float32).eps))
    return np.maximum(m, np.float32(1e-3))


def view(a, v):
    k, f = v
    if f:
        a = a[..., ::-1]
    return np.rot90(a, k, axes=(-2, -1))


def unview(a, v):
    k, f = v
    a = np.rot90(a, -k, axes=(-2, -1))
    if f:
        a = a[..., ::-1]
    return a


# ---- one shifted lattice -----------------------------------------------------------------------------------------------
def predict_shift(model, stack, shift, views, batch=8, bf16=False):
    """returns ([one map per view], patches). model needs: depth, patch, normalize(raw float32 DHW) and predict(batch NDHW float32, bf16) -> N x P x P in [0, 1]"""
    oy, ox = int(shift[0]), int(shift[1])
    if oy or ox:
        stack = np.pad(np.asarray(stack), ((0, 0), (oy, 0), (ox, 0)))
    D, H, W = stack.shape
    idx = centre_layers(D, model.depth)
    if idx.size != model.depth:
        raise SystemExit("REFUSED: %d planes, the model needs %d" % (D, model.depth))
    P = model.patch
    hw = hann(P)
    ps = [np.zeros((H, W), np.float32) for _ in views]
    ws = np.zeros((H, W), np.float32)
    buf, meta = [], []
    n = 0

    def flush():
        nonlocal n
        if not buf:
            return
        x = np.stack([np.ascontiguousarray(view(b, v)) for b in buf for v in views])
        pr = model.predict(x, bf16)
        if pr.shape[-2:] != (P, P):
            raise SystemExit("STOP: output %s is not %d x %d" % (pr.shape, P, P))
        nv = len(views)
        for j, (y, x0, h, w) in enumerate(meta):
            for i, v in enumerate(views):
                t = unview(pr[j * nv + i], v)
                ps[i][y:y + h, x0:x0 + w] += t[:h, :w] * hw[:h, :w]
            ws[y:y + h, x0:x0 + w] += hw[:h, :w]
        n += len(buf)
        buf.clear(); meta.clear()

    for y in positions(H, P):
        for x in positions(W, P):
            h, w = min(P, H - y), min(P, W - x)
            raw = np.zeros((model.depth, P, P), np.float32)
            raw[:, :h, :w] = np.asarray(stack[idx, y:y + h, x:x + w])
            if not raw.any():
                continue
            buf.append(np.ascontiguousarray(model.normalize(raw), dtype=np.float32))
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
    return outs, n


def read_window(model, window, views, ensemble=True, bf16=False, batch=8):
    """one start: 4 lattices shifted by a quarter patch (ensemble) and the views; returns (map, patches)"""
    q = model.patch // 4
    shifts = ((0, 0), (q, 0), (0, q), (q, q)) if ensemble else ((0, 0),)
    per = [[] for _ in views]
    npatch = 0
    for sh in shifts:
        maps, n = predict_shift(model, window, sh, views, batch, bf16)
        for i, m in enumerate(maps):
            per[i].append(m)
        npatch += n
    vmaps = [np.mean(L, 0).astype(np.float32) if len(L) > 1 else L[0] for L in per]
    return np.mean(vmaps, 0).astype(np.float32), npatch


def read_stack(model, stack, starts, views, divisor=None, ensemble=True, bf16=False, batch=8, log=print):
    """the map is the mean over the starts; returns (map, rows of [start, seconds, patches])"""
    maps, rows = [], []
    for s in starts:
        a = np.asarray(stack[s:s + model.depth])
        if a.shape[0] != model.depth:
            raise SystemExit("REFUSED: start %d gives %d planes of %d" % (s, a.shape[0], model.depth))
        if divisor:
            a = a.astype(np.float32) / np.float32(divisor)
        t0 = time.time()
        m, n = read_window(model, np.ascontiguousarray(a), views, ensemble, bf16, batch)
        sec = round(time.time() - t0, 3)
        maps.append(m); rows.append([s, sec, n])
        log("%s start %d: %.1f s, %d patches" % (now(), s, sec, n))
    return np.mean(maps, 0).astype(np.float32), rows


# ---- real model (villa ink_detection code, imported from --villa-src) ------------------------------------------------------
class RectinaModel:
    def __init__(self, checkpoint, villa_src, device="cpu", threads=None):
        import torch
        self.torch = torch
        self.device = device
        if threads:
            torch.set_num_threads(int(threads))
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise SystemExit("REFUSED: device %s asked and torch.cuda.is_available() is False" % device)
        payload = torch.load(checkpoint, map_location="cpu", weights_only=True)
        sys.path.insert(0, villa_src)
        from vesuvius.ink_detection.config import InkConfig
        from vesuvius.ink_detection.models.model import make_model
        from vesuvius.ink_detection.inference.inference_runtime import TargetModel
        from vesuvius.image_proc.intensity.normalization import normalize_robust
        cfg = InkConfig.from_mapping(payload["config"])
        state = payload["model"]
        if all(str(k).startswith("module.") for k in state):
            state = {str(k)[7:]: v for k, v in state.items()}
        if cfg.data.mode != "flat":
            raise SystemExit("STOP: checkpoint mode %r is not flat" % cfg.data.mode)
        base = make_model(cfg)
        base.load_state_dict(state, strict=True)
        self.net = TargetModel(base.eval(), input_pad_depth_to=cfg.model.input_pad_depth_to).eval().to(device)
        self.depth, self.patch = int(cfg.model.crop_size[0]), int(cfg.model.crop_size[1])
        nm = cfg.data.normalization
        if self.depth != DEPTH or self.patch not in PATCHES or nm.mode != "robust_mad" or (nm.percentile_lower, nm.percentile_upper) != (1.0, 99.0):
            raise SystemExit("STOP: crop %s or normalisation %r is not the one this reader supports" % (cfg.model.crop_size, nm))
        self._norm = normalize_robust
        self.tensors = len(state)

    def normalize(self, raw):
        return self._norm(raw)

    def predict(self, x, bf16):
        t = self.torch
        with t.inference_mode():
            xt = t.from_numpy(x)[:, None].to(self.device)
            if bf16:
                with t.autocast("cuda" if self.device.startswith("cuda") else "cpu", dtype=t.bfloat16):
                    lg = self.net(xt)
            else:
                lg = self.net(xt)
            if lg.ndim != 4:
                raise SystemExit("STOP: logits shape %s" % (tuple(lg.shape),))
            return lg.float().sigmoid().cpu().numpy()[:, 0]


# ---- files ----------------------------------------------------------------------------------------------------------
def open_stack(path):
    """an array (planes, rows, columns): a .npy file, or an OME-Zarr folder (array '0' of the group, or a plain zarr array)"""
    if os.path.isdir(path):
        import zarr
        g = zarr.open(path, mode="r")
        a = g if hasattr(g, "shape") else g["0"]
    else:
        a = np.load(path, mmap_mode="r")
    if a.ndim != 3:
        raise SystemExit("REFUSED: stack has shape %s, (planes, rows, columns) expected" % (a.shape,))
    return a


def default_divisor(dtype):
    return DIVISOR_UINT16 if np.dtype(dtype) == np.uint16 else None


def compare_maps(a, b, tol=TOLERANCE):
    if a.shape != b.shape:
        raise SystemExit("REFUSED: shapes %s and %s differ" % (a.shape, b.shape))
    x, y = a.astype(np.float64), b.astype(np.float64)
    d = np.abs(x - y)
    r = float(np.corrcoef(x.ravel(), y.ravel())[0, 1]) if x.std() > 0 and y.std() > 0 else float("nan")
    ok = bool(d.max() <= tol["max_abs"] and d.mean() <= tol["mean_abs"] and r == r and r >= tol["pearson"])
    return dict(max_abs=float(d.max()), mean_abs=float(d.mean()), pearson=r, tolerance=tol, within=ok)


def write_outputs(out, fin, rows, meta, device):
    if os.path.exists(out + "/DONE"):
        raise SystemExit("REFUSED: %s/DONE exists" % out)
    os.makedirs(out, exist_ok=True)
    np.save(out + "/map.part.npy", fin); os.replace(out + "/map.part.npy", out + "/map.npy")
    with open(out + "/reads.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["start", "seconds", "patches", "device"])
        w.writerows([r + [device] for r in rows])
    files = {x: sha256(out + "/" + x) for x in ("map.npy", "reads.csv")}
    with open(out + "/DONE", "w") as f:
        json.dump(dict(t=now(), starts=len(rows), files=files, **meta), f, sort_keys=True)


def cmd_read(a):
    stack = open_stack(a.stack)
    div = a.divisor if a.divisor is not None else default_divisor(stack.dtype)
    if a.crop:
        r0, r1, c0, c1 = a.crop
        stack = np.asarray(stack[:, r0:r1, c0:c1])
    m = RectinaModel(a.checkpoint, a.villa_src, a.device, a.threads)
    bf16 = a.bf16 if a.bf16 is not None else a.device.startswith("cuda")
    fin, rows = read_stack(m, stack, a.starts, VIEWS[a.views], div, True, bf16, a.batch)
    write_outputs(a.out, fin, rows, dict(checkpoint_sha256=sha256(a.checkpoint), patch=m.patch, tensors=m.tensors, views=a.views,
                                         divisor=div, bf16=bool(bf16), stack_shape=list(stack.shape), crop=a.crop), a.device)
    print("wrote", a.out + "/map.npy", fin.shape, "min %.4f max %.4f" % (fin.min(), fin.max()))


def cmd_compare(a):
    r = compare_maps(np.load(a.map), np.load(a.reference), dict(max_abs=a.max_abs, mean_abs=a.mean_abs, pearson=a.pearson))
    print(json.dumps(r))
    return 0 if r["within"] else 14


def cmd_info(a):
    import torch
    p = torch.load(a.checkpoint, map_location="cpu", weights_only=True)
    c = p["config"]
    print(json.dumps(dict(sha256=sha256(a.checkpoint), step=p.get("step"), model_type=c.get("model_type"), crop_size=c.get("crop_size"),
                          tensors=len(p["model"]), normalization=c.get("image_normalization"))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("read")
    r.add_argument("--stack", required=True); r.add_argument("--checkpoint", required=True); r.add_argument("--out", required=True)
    r.add_argument("--villa-src", required=True, help="folder holding the 'vesuvius' package (villa/vesuvius/src at the pinned commit)")
    r.add_argument("--device", default="cpu"); r.add_argument("--threads", type=int)
    r.add_argument("--starts", type=int, nargs="+", default=list(range(7)))
    r.add_argument("--views", choices=sorted(VIEWS), default="2v")
    r.add_argument("--divisor", type=float, help="default 65280 for uint16 stacks, none otherwise")
    r.add_argument("--bf16", dest="bf16", action="store_true", default=None); r.add_argument("--fp32", dest="bf16", action="store_false")
    r.add_argument("--batch", type=int, default=8)
    r.add_argument("--crop", type=int, nargs=4, metavar=("R0", "R1", "C0", "C1"), help="read only rows R0:R1 and columns C0:C1 (tests)")
    c = sp.add_parser("compare"); c.add_argument("map"); c.add_argument("reference")
    c.add_argument("--max-abs", type=float, default=0.05); c.add_argument("--mean-abs", type=float, default=0.005); c.add_argument("--pearson", type=float, default=0.995)
    i = sp.add_parser("info"); i.add_argument("--checkpoint", required=True)
    a = ap.parse_args(argv)
    return {"read": cmd_read, "compare": cmd_compare, "info": cmd_info}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
