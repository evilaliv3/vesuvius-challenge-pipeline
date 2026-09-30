#!/usr/bin/env python3
"""draw_near.py: the fourth wave's near draw of chain-0826 (DECLARATION.md addition of 2026-09-27T20:25:28Z).

New file, written 2026-09-27T20:2xZ by a coordinator agent. The candidate test is draw_seeds.py's candidates_of (255
with its six face neighbours 255), applied on the interior of a block read around each source; nothing else of
draw_seeds.py is used.

  sources   evidence/wave4-sources.csv rows with is_source yes, in ascending draw_order;
  shell     Euclidean distance to the source point, in voxels, R_MIN 48 <= d <= R_MAX 256; inside the volume;
  order     candidates in numpy.nonzero order of the block (z, y, x);
  draw      numpy.random.default_rng(RNG_SEED 20260927), K 8 per source, one index at a time with rng.integers(0, n);
            a repeat, a point of draws 1 to 6400, or a point drawn for an earlier source is redrawn; a source with
            fewer than K admissible candidates gives all of them.
Writes evidence/seeds-PHerc0826-draw<N>.csv (tool line, then header and rows 1 to 6400 copied byte for byte from the
draw6400 file, then the near rows in the same columns and line ends) and evidence/candidate-population-draw<N>.csv
(draw6400's population rows copied, then the near draw's own rows), N = 6400 plus the draws. Refuses to overwrite.
Also writes evidence/wave4-near-draw.csv (one row per source: candidates in the shell, drawn, redraws) and
evidence/wave4-near-attempts.csv (one row per near draw: source, distance).
"""
import csv, io, json, os, subprocess, sys

import numpy as np
import zarr

S = "/data/scrollagent/runs/rev1/chain-0826"
E = os.path.join(S, "evidence")
PRED = "/data/scrollagent/data/datasets/PHerc0826/0"
MANIFEST = "/data/scrollagent/pipeline/datasets/manifests/PHerc0826.json"
TOOL = "chain-0826/tools/draw_near.py"
PREV = 6400
RNG_SEED = 20260927
K = 8
R_MIN, R_MAX = 48, 256
CHUNK = 192


def candidates_of(block):
    """draw_seeds.py's test, verbatim."""
    sol = block == 255
    out = np.zeros(sol.shape, dtype=bool)
    out[1:-1, 1:-1, 1:-1] = (sol[1:-1, 1:-1, 1:-1] & sol[:-2, 1:-1, 1:-1] & sol[2:, 1:-1, 1:-1]
                             & sol[1:-1, :-2, 1:-1] & sol[1:-1, 2:, 1:-1]
                             & sol[1:-1, 1:-1, :-2] & sol[1:-1, 1:-1, 2:])
    return sol, out


def rows(p):
    L = [l for l in open(p, newline="") if not l.lstrip().startswith('"#')]
    return list(csv.DictReader(L))


def main():
    shape = json.load(open(MANIFEST))["shape"]
    prev_draw = os.path.join(E, "seeds-PHerc0826-draw%d.csv" % PREV)
    prev_pop = os.path.join(E, "candidate-population-draw%d.csv" % PREV)
    raw = open(prev_draw, "rb").read().split(b"\n")
    assert len(raw) == PREV + 3 and raw[-1] == b"", "draw6400 layout"
    head = raw[1].rstrip(b"\r").decode()
    fields = head.split(",")
    taken = set()
    for r in rows(prev_draw):
        taken.add((int(r["seed_z"]), int(r["seed_y"]), int(r["seed_x"])))
    assert len(rows(prev_draw)) == PREV
    src = sorted((r for r in rows(os.path.join(E, "wave4-sources.csv")) if r["is_source"] == "yes"),
                 key=lambda r: int(r["draw_order"]))
    a = zarr.open(PRED, mode="r")
    assert list(a.shape) == list(shape), (a.shape, shape)
    rng = np.random.default_rng(RNG_SEED)
    new, per = [], []
    order = PREV
    for s in src:
        sx, sy, sz = int(s["seed_x"]), int(s["seed_y"]), int(s["seed_z"])
        z0, z1 = max(0, sz - R_MAX - 1), min(shape[0], sz + R_MAX + 2)
        y0, y1 = max(0, sy - R_MAX - 1), min(shape[1], sy + R_MAX + 2)
        x0, x1 = max(0, sx - R_MAX - 1), min(shape[2], sx + R_MAX + 2)
        block = np.asarray(a[z0:z1, y0:y1, x0:x1])
        _sol, cand = candidates_of(block)
        idx = np.nonzero(cand)
        zz, yy, xx = idx[0] + z0, idx[1] + y0, idx[2] + x0
        d2 = (zz - sz).astype(np.int64) ** 2 + (yy - sy).astype(np.int64) ** 2 + (xx - sx).astype(np.int64) ** 2
        keep = (d2 >= R_MIN * R_MIN) & (d2 <= R_MAX * R_MAX)
        zz, yy, xx = zz[keep], yy[keep], xx[keep]
        n = int(zz.size)
        t_in = 0   # points already taken that are candidates of this shell: the admissible count is n minus them
        for (tz, ty, tx) in taken:
            dd = (tz - sz) ** 2 + (ty - sy) ** 2 + (tx - sx) ** 2
            if R_MIN * R_MIN <= dd <= R_MAX * R_MAX and z0 <= tz < z1 and y0 <= ty < y1 and x0 <= tx < x1 \
                    and cand[tz - z0, ty - y0, tx - x0]:
                t_in += 1
        n_adm = n - t_in
        want = min(K, n_adm)
        got, seen, draws, redraws = [], set(), 0, 0
        while len(got) < want:
            g = int(rng.integers(0, n)); draws += 1
            p = (int(zz[g]), int(yy[g]), int(xx[g]))
            if g in seen or p in taken:
                redraws += 1; continue
            seen.add(g); got.append(g); taken.add(p)
        for g in got:
            z, y, x = int(zz[g]), int(yy[g]), int(xx[g])
            nb = np.asarray(a[z - 1:z + 2, y - 1:y + 2, x - 1:x + 2])
            six = [int(nb[0, 1, 1]), int(nb[2, 1, 1]), int(nb[1, 0, 1]), int(nb[1, 2, 1]), int(nb[1, 1, 0]), int(nb[1, 1, 2])]
            order += 1
            new.append({
                "scroll": "PHerc0826", "attempt": "PHerc0826-seed%02d" % order, "draw_order": order,
                "global_candidate_index": "near %s" % s["attempt"],
                "lattice_chunk": "%d/%d/%d" % (z // CHUNK, y // CHUNK, x // CHUNK),
                "seed_x": x, "seed_y": y, "seed_z": z, "seed_value": int(nb[1, 1, 1]),
                "six_face_neighbours_all_255": "yes" if all(v == 255 for v in six) else "no",
                "neighbourhood_3x3x3_of_255": int((nb == 255).sum()),
                "edge_margin_x": min(x, shape[2] - 1 - x), "edge_margin_y": min(y, shape[1] - 1 - y),
                "edge_margin_z": min(z, shape[0] - 1 - z),
                "_source": s["attempt"], "_d": round(float(np.sqrt((z - sz) ** 2 + (y - sy) ** 2 + (x - sx) ** 2)), 1)})
        per.append([s["attempt"], s["draw_order"], sx, sy, sz, s["best_square_mm_min_step"], n, len(got), draws, redraws,
                    "PHerc0826-seed%d..%d" % (order - len(got) + 1, order) if got else "none"])
        print("  %s: %d candidates in the shell, %d drawn (%d draws, %d redrawn)" % (s["attempt"], n, len(got), draws, redraws),
              flush=True)
    N = order
    out = os.path.join(E, "seeds-PHerc0826-draw%d.csv" % N)
    pop = os.path.join(E, "candidate-population-draw%d.csv" % N)
    for p in (out, pop):
        if os.path.exists(p):
            raise SystemExit("REFUSED: %s exists" % p)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")   # default line end \r\n, as draw_seeds.py
    w.writerows(new)
    with open(out + ".part", "wb") as f:
        f.write(('"# written by %s: rows 1 to %d copied byte for byte from seeds-PHerc0826-draw%d.csv (draw_seeds.py, rng '
                 '20260920); rows %d to %d the near draw of the fourth wave, rng %d, %d per source, %d to %d voxels from the '
                 'source seed point; global_candidate_index names the source"\r\n'
                 % (TOOL, PREV, PREV, PREV + 1, N, RNG_SEED, K, R_MIN, R_MAX)).encode())
        f.write(b"\n".join(raw[1:PREV + 2]) + b"\n")
        f.write(buf.getvalue().encode())
    os.replace(out + ".part", out)
    P = rows(prev_pop)
    with open(pop + ".part", "w", newline="") as f:
        f.write('"# written by %s: the rows of candidate-population-draw%d.csv copied (they describe draws 1 to %d), then '
                'the near draw of draws %d to %d"\r\n' % (TOOL, PREV, PREV, PREV + 1, N))
        w = csv.writer(f)
        w.writerow(["scroll", "quantity", "value", "what_it_is"])
        for r in P:
            w.writerow([r["scroll"], r["quantity"], r["value"], r["what_it_is"]])
        for q, v, t in [("near_sources", len(src), "evidence/wave4-sources.csv is_source yes"),
                        ("near_rng_seed", RNG_SEED, "numpy default_rng seed of the near draw, written into the tool"),
                        ("near_per_source", K, "draws per source"),
                        ("near_r_min_voxels", R_MIN, "shell inner radius"), ("near_r_max_voxels", R_MAX, "shell outer radius"),
                        ("near_seeds_drawn", N - PREV, "rows %d to %d" % (PREV + 1, N))]:
            w.writerow(["PHerc0826", q, v, t])
    os.replace(pop + ".part", pop)
    t = subprocess.check_output(["date", "-u", "+%FT%TZ"]).decode().strip()
    with open(os.path.join(E, "wave4-near-draw.csv"), "w", newline="") as f:
        f.write('"# written by %s at %s: one row per source of the near draw; candidates_in_shell counts voxels of 255 with six '
                '255 neighbours at %d to %d voxels from the source point"\n' % (TOOL, t, R_MIN, R_MAX))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["source", "source_draw_order", "seed_x", "seed_y", "seed_z", "source_best_square_mm", "candidates_in_shell",
                    "drawn", "draws_made", "redrawn", "attempts"])
        w.writerows(per)
    with open(os.path.join(E, "wave4-near-attempts.csv"), "w", newline="") as f:
        f.write('"# written by %s at %s: one row per near draw, its source and its distance to the source point in voxels"\n'
                % (TOOL, t))
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["attempt", "source", "distance_voxels", "seed_x", "seed_y", "seed_z", "six_face_neighbours_all_255"])
        for r in new:
            w.writerow([r["attempt"], r["_source"], r["_d"], r["seed_x"], r["seed_y"], r["seed_z"], r["six_face_neighbours_all_255"]])
    print("written %s (%d near rows, N %d), %s" % (out, N - PREV, N, pop))


if __name__ == "__main__":
    main()
