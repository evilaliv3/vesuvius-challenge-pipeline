#!/usr/bin/env python3
"""c-f25-square-full.py: figure C25, the certified square of the headline surface on PHerc0826 at full resolution, one sample
per voxel, a full page. RAW SCAN, NO INK DETECTOR. Written 2026-09-30 on the owner's word (about 18:45Z, relayed by the director).

The square is the one of Figure C21 panel (a): route R2cnative, surface PHerc0826-seed6273-squarecentre, the square certified
with crossings between traced surfaces adjudicated (side, cells and corner from square-checks-adjudicated.csv, the row of that
surface), on the tracer's own grid as render-routes-0826's tools/routes.py surface() returns it (the native grid bilinearly
upsampled by 5, step about 4 voxels), turned by the same rule as c-f21-fig-r2c.py prep (a transpose and a flip only, so that
the scan's z points up). Only the nodes of the square are used, and every one of them is valid (checked).

prep (the scrollagent .venv): the node coordinates are interpolated bilinearly between the square's nodes to a grid whose
side has round(side_mm / voxel_mm) samples, from the first node to the last on each axis, so the step is about one voxel;
the raw scan (20250821151701 level 0, masked, 128 cubed uncompressed chunks) is sampled there by trilinear interpolation of
its 8 neighbouring voxels. The chunks needed are fetched with certified-piece-0826's dark.py fetch into render-routes-0826's
scratch/raw-chunks (its routes.py redirection), under a shared lock on its scratch/cache.lock, only if /data stays above
35 GB free after the fetch; their list is scratch/fetched-<TAG>.txt, and the study's tools/drop.py deletes them with a
ledger row. A sample is MISSING when any of its 8 voxels lies in a chunk that is absent from the store or outside the
volume: it is not measurable, never zero; missing samples are drawn white and counted in the table.
plot (any python with numpy and PIL): the PNG, grayscale, contrast stretched linearly from the 1st to the 99th percentile
of the non missing samples, one 5 mm scale bar (figstyle.scale_bar_pil) and the label «raw scan, no ink detector», sized to
the text width of an IEEE two column page (figstyle.PAGE_IN); and the plotted table. No coordinate, height, chunk index,
seed point or centre is drawn or written.

Usage: c-f25-square-full.py prep | plot [--png PNG] [--out CSV]
"""
import argparse, csv, hashlib, os, shutil, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
H = "/data/scrollagent/runs/rev1/render-routes-0826"
FIGURE = "c-f25-square-full"
ROUTE, NAME = "R2cnative", "PHerc0826-seed6273-squarecentre"
VOX_MM = 0.009362
TAG = "full-square-f25"
SCR = os.environ.get("F25_SCRATCH", "/data/scrollagent/outputs/artifacts/full-square-2026-09-30/scratch")
FN = SCR + "/%s-%s-%s.npz" % (FIGURE, ROUTE, NAME)
MINFREE = 35e9
LO_PCT, HI_PCT = 1.0, 99.0
BAR_MM = 5
LABEL = "raw scan, no ink detector"
for p in (HERE, "/data/tmp/v5-0826/f49f6c7d-pherc0826-chain/src/tools"):   # figstyle: this work's copy, read only
    if os.path.isfile(os.path.join(p, "figstyle.py")):
        sys.path.insert(0, p); break
import figstyle as F  # noqa: E402


def rows(p):
    return list(csv.DictReader(l for l in open(p) if not l.lstrip('"').startswith("#")))


def adjudicated():
    for p in (os.path.join(SRC, "inputs/render-routes-0826/square-checks-adjudicated.csv"),
              H + "/evidence/square-checks-adjudicated.csv"):
        if os.path.isfile(p):
            r = [x for x in rows(p) if x["route"] == ROUTE and x["surface"] == NAME]
            if len(r) != 1:
                raise SystemExit("%s: %d rows of %s %s" % (p, len(r), ROUTE, NAME))
            return r[0], p
    raise SystemExit("square-checks-adjudicated.csv not found")


def prep():
    import fcntl
    from scipy import ndimage
    sys.path.insert(0, H + "/tools")
    import routes as RT  # noqa: E402  (PT.CACHE redirected to the study's scratch/raw-chunks)
    PT, DK = RT.PT, RT.DK
    ad, _ = adjudicated()
    ba = int(ad["certified_adjudicated_cells"]); ai0, aj0 = map(int, ad["certified_adjudicated_corner"].split())
    side_mm = float(ad["certified_adjudicated_mm"])
    P, V = RT.surface(ROUTE, NAME)[:2]
    Pc, Vc = P[ai0:ai0 + ba, aj0:aj0 + ba].astype(np.float64), V[ai0:ai0 + ba, aj0:aj0 + ba]
    if Pc.shape[:2] != (ba, ba) or not Vc.all() or not np.isfinite(Pc).all():
        raise SystemExit("the adjudicated square is not fully covered on the tracer grid")
    N = int(round(side_mm / VOX_MM))
    t = np.linspace(0.0, ba - 1.0, N)
    TI, TJ = np.meshgrid(t, t, indexing="ij")
    Q = np.stack([ndimage.map_coordinates(Pc[..., k], [TI, TJ], order=1, mode="nearest") for k in range(3)], -1)
    del TI, TJ
    # the turn of c-f21-fig-r2c.py prep, from the nodes' z
    dzi = np.nanmedian(np.diff(Pc[..., 2], axis=0)); dzj = np.nanmedian(np.diff(Pc[..., 2], axis=1))
    turn = "none"
    if abs(dzj) > abs(dzi):
        Q = Q.transpose(1, 0, 2); dzi = dzj; turn = "transposed"
    if dzi > 0:
        Q = Q[::-1]; turn += ", flipped"
    Q = np.ascontiguousarray(Q)
    x, y, z = Q[..., 0].ravel(), Q[..., 1].ravel(), Q[..., 2].ravel()
    x0, y0, z0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fy, fz = x - x0, y - y0, z - z0
    CH = PT.CH
    need = set()
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                k = np.unique(((z0 + dz) // CH) * 10 ** 8 + ((y0 + dy) // CH) * 10 ** 4 + (x0 + dx) // CH)
                need.update(k.tolist())
    need = sorted((k // 10 ** 8, (k // 10 ** 4) % 10 ** 4, k % 10 ** 4) for k in need)
    lk = open(H + "/scratch/cache.lock", "a"); fcntl.flock(lk, fcntl.LOCK_SH)
    todo = [c for c in need if not PT.have(c)]
    free = shutil.disk_usage("/data").free
    print("chunks needed %d, to fetch %d (%.3f GB), /data free %.1f GB" % (len(need), len(todo), len(todo) * PT.NBYTES / 1e9, free / 1e9), flush=True)
    if free - len(todo) * PT.NBYTES <= MINFREE:
        raise SystemExit("refused: /data would fall under 35 GB free")
    if todo:
        tally, got = DK.fetch(todo)
        with open(H + "/scratch/fetched-%s.txt" % TAG, "a") as f:
            f.writelines(g + "\n" for g in got)
        print("fetch", tally, flush=True)
        if tally["failed"]:
            raise SystemExit("fetch failed for %d chunks" % tally["failed"])
    raw = PT.Raw2()
    acc = np.zeros(x.shape, np.float64)
    for dz in (0, 1):
        for dy in (0, 1):
            for dx in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                acc += w * raw.sample((x0 + dx).astype(np.float64), (y0 + dy).astype(np.float64), (z0 + dz).astype(np.float64))
                raw.cache.clear()
    fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
    VAL = acc.reshape(N, N)
    miss = ~np.isfinite(VAL)
    sr = np.linalg.norm(np.diff(Q, axis=0), axis=-1); sc = np.linalg.norm(np.diff(Q, axis=1), axis=-1)
    os.makedirs(SCR, exist_ok=True)
    np.savez_compressed(FN, VAL=VAL.astype(np.float32), MISS=miss, turn=turn, side_mm=side_mm, cells=ba,
                        step_row_vox=float(np.median(sr)), step_col_vox=float(np.median(sc)),
                        chunks_needed=len(need), chunks_fetched=len(todo))
    print(FN, N, "missing", int(miss.sum()), "turn", turn, "steps", float(np.median(sr)), float(np.median(sc)))


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def plot(png, out):
    from PIL import Image, ImageDraw, ImageFont
    z = np.load(FN)
    VAL, MISS = z["VAL"].astype(np.float64), z["MISS"]
    N = VAL.shape[0]
    step_vox = 0.5 * (float(z["step_row_vox"]) + float(z["step_col_vox"]))
    mm_px = step_vox * VOX_MM
    g = VAL[~MISS]
    lo, hi = np.percentile(g, [LO_PCT, HI_PCT])
    im = np.clip((np.nan_to_num(VAL) - lo) / (hi - lo), 0, 1)
    im[MISS] = 1.0
    img = Image.fromarray(np.rint(im * 255).astype(np.uint8), "L")
    dpi = N / F.PAGE_IN
    fpx = int(round(8.0 / 72.0 * dpi))          # 8 pt at the printed size
    F.scale_bar_pil(img, mm_px, length_mm=BAR_MM, colour=0, halo=255, font_px=fpx)
    try:
        font = ImageFont.truetype("/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-regular.otf", fpx)
    except OSError:
        font = ImageFont.load_default()
    d = ImageDraw.Draw(img)
    m = max(12, fpx)
    x0, y1 = m, N - m
    bb = d.textbbox((x0, y1), LABEL, font=font, anchor="ls")
    d.rectangle((bb[0] - 6, bb[1] - 6, bb[2] + 6, bb[3] + 6), fill=255)
    d.text((x0, y1), LABEL, fill=0, font=font, anchor="ls")
    os.makedirs(os.path.dirname(png), exist_ok=True)
    img.save(png, optimize=True, dpi=(dpi, dpi))
    fields = ["key", "what", "value"]
    r = [("grid", "samples per side of the square (rows = columns)", N),
         ("step_vox", "median 3D distance between neighbouring samples; voxels (mean of rows and columns)", "%.4f" % step_vox),
         ("voxel_um", "the scan's voxel; micrometres (the volume 20250821151701-9.362um; routes.py VOX)", "%.3f" % (VOX_MM * 1e3)),
         ("mm_per_px", "step_vox x the voxel; mm", "%.6f" % mm_px),
         ("side_mm", "square side; square-checks-adjudicated.csv certified_adjudicated_mm", "%.4f" % float(z["side_mm"])),
         ("samples", "samples drawn", N * N),
         ("missing", "samples with a voxel in an absent chunk; drawn white", int(MISS.sum())),
         ("sampling", "raw scan level 0; trilinear between the 8 neighbouring voxels; surface bilinear between the tracer grid's nodes", "trilinear"),
         ("turn_to_z_up", "quarter turns and flips of the tracer grid (c-f21-fig-r2c.py rule)", str(z["turn"]).replace(",", ";")),
         ("stretch_lo_pct", "contrast stretch lower percentile of the non missing samples (black)", "%g" % LO_PCT),
         ("stretch_hi_pct", "contrast stretch upper percentile of the non missing samples (white)", "%g" % HI_PCT),
         ("bar_mm", "scale bar; mm", BAR_MM),
         ("print_in", "printed width; inches (IEEE two column text width)", "%g" % F.PAGE_IN),
         ("dpi", "pixels per inch at that width", "%.1f" % dpi),
         ("png_mb", "PNG size; MB", "%.2f" % (os.path.getsize(png) / 1e6)),
         ("png_sha256", "sha256 of the PNG", sha(png))]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as f:
        f.write("# figure C25, written by src/tools/%s.py at %s: the certified square (adjudicated) of %s %s at one sample per voxel; "
                "RAW SCAN; NO INK DETECTOR; no coordinate; height; chunk index; seed point or centre is written\n"
                % (FIGURE, subprocess.check_output(["date", "-u", "+%FT%TZ"], text=True).strip(), ROUTE, NAME))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(fields)
        for k, what, v in r:
            w.writerow([k, what.replace(",", ";"), v])
    print(png, img.size, "%.2f MB" % (os.path.getsize(png) / 1e6), out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["prep", "plot"])
    ap.add_argument("--png", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.mode == "prep":
        return prep()
    inwork = os.path.isdir(os.path.join(SRC, "paper/figures"))
    png = a.png or (os.path.join(SRC, "paper/figures/%s.png" % FIGURE) if inwork else os.path.join(HERE, FIGURE + ".png"))
    out = a.out or (os.path.join(SRC, "evidence/figures/%s.csv" % FIGURE) if inwork else os.path.join(HERE, FIGURE + ".csv"))
    plot(os.path.abspath(png), os.path.abspath(out))


if __name__ == "__main__":
    main()
