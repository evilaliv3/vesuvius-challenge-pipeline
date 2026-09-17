#!/usr/bin/env python3
"""The two figures in the README.

    python figures.py

`methods-compared.png` is the table as a picture, with the fake axis in grey so that the scroll
where the bench does not discriminate is visible at a glance. `plateau-on-papyrus.png` is the
mechanism on real sections: the plateau of the distance transform, and where each rule lands on it.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi

import bench
import data
import estimators as est

HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
ORDER = ["fake axis (control)", "argmax", "argmax + hampel", "centroid",
         "plateau_centroid", "plateau_nearest_centroid"]


def methods_compared(heights=46, level=3):
    fig, axes = plt.subplots(1, len(data.GROUND_TRUTH), figsize=(4.6 * len(data.GROUND_TRUTH), 4.8), sharex=True)
    for ax, scroll in zip(axes, data.GROUND_TRUTH):
        truth = data.published_umbilicus(scroll)
        lines = bench.polylines(scroll, est.ESTIMATORS, level, heights)
        lines["argmax + hampel"] = est.hampel_reject(lines["argmax"])[0]
        lines["fake axis (control)"] = bench.fake_axis(scroll, level, heights)
        grid = np.array([z * data.scale_to_reference(scroll, level)
                         for z in data.slice_heights(scroll, level, heights)], float)
        common = truth[(truth[:, 2] >= grid.min()) & (truth[:, 2] <= grid.max())]
        names = [n for n in ORDER if n in lines]
        mm = data.mm_per_voxel(scroll)
        med = [np.median(bench.errors(common, lines[n], mm)[0]) for n in names]
        p90 = [np.percentile(bench.errors(common, lines[n], mm)[0], 90) for n in names]
        colours = ["#b0b0b0" if n.startswith("fake") else
                   "#c05a3c" if n.startswith("argmax") else "#3c6ec0" for n in names]
        y = np.arange(len(names))
        ax.barh(y, med, color=colours, height=0.62)
        ax.plot(p90, y, "k|", ms=9, mew=1.4)
        ax.set_yticks(y)
        ax.set_yticklabels([est.display(n) for n in names] if scroll == data.GROUND_TRUTH[0]
                           else [""] * len(names), fontsize=9)
        ax.set_title(f"{scroll} ({len(common)} published points)", fontsize=10)
        ax.set_xlabel("median distance from the published umbilicus, mm")
        ax.grid(axis="x", lw=0.4, alpha=0.5)
        ax.invert_yaxis()
    fig.suptitle("Distance from the published umbilicus. Bar: median. Tick: p90. "
                 "Grey: a constant axis that knows nothing about the scroll", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "methods-compared.png", dpi=150)
    print("written", OUT / "methods-compared.png")


def plateau_on_papyrus(scroll="PHerc0826", level=3, heights=46):
    f = data.scale_to_reference(scroll, level)
    truth = data.published_umbilicus(scroll)
    rows = []
    for z in data.slice_heights(scroll, level, heights):
        z0 = z * f
        if not (truth[:, 2].min() <= z0 <= truth[:, 2].max()):
            continue
        sl = data.cached_slice(scroll, level, z)
        mask, dist = est.section(sl)
        if mask is None:
            raise data.MissingData(f"{scroll}: the slice at height {z} holds no section; "
                                   "the surface prediction behind it is missing or empty")
        a, c = est.argmax(mask, dist), est.centroid(mask, dist)
        p = est.plateau_nearest_centroid(mask, dist)
        vx = np.interp(z0, truth[:, 2], truth[:, 0]) / f
        vy = np.interp(z0, truth[:, 2], truth[:, 1]) / f
        ea = np.hypot(a[0] - vx, a[1] - vy) * f * data.mm_per_voxel(scroll)
        ep = np.hypot(p[0] - vx, p[1] - vy) * f * data.mm_per_voxel(scroll)
        rows.append((ea - ep, z0, sl, mask, dist, a, c, p, (vx, vy), ea, ep))
    rows.sort(key=lambda r: -r[0])
    picked = [rows[0], rows[len(rows) // 2], rows[-1]]
    titles = ["the maximum jumps into the wrong lobe", "a typical slice", "the worst slice for the proposal"]

    fig, axes = plt.subplots(3, 2, figsize=(12.6, 9.6))
    for (ax1, ax2), (_, z0, sl, mask, dist, a, c, p, v, ea, ep), title in zip(axes, picked, titles):
        ys, xs = np.where(mask)
        y0, y1, x0, x1 = max(0, ys.min() - 10), ys.max() + 10, max(0, xs.min() - 10), xs.max() + 10
        ax1.imshow(sl[y0:y1, x0:x1], cmap="bone", vmin=0, vmax=255, interpolation="nearest")
        ax1.contour(mask[y0:y1, x0:x1], levels=[0.5], colors="#e8b64c", linewidths=0.9)
        ax2.imshow(np.where(mask, dist, np.nan)[y0:y1, x0:x1], cmap="magma", interpolation="nearest")
        ax2.contour(dist[y0:y1, x0:x1], levels=[0.9 * dist.max()], colors="#7fd0ff", linewidths=1.4)
        for ax in (ax1, ax2):
            ax.plot(a[0] - x0, a[1] - y0, "x", color="#e0533d", ms=12, mew=2.6)
            ax.plot(c[0] - x0, c[1] - y0, "o", color="#8a8a8a", ms=7)
            ax.plot(p[0] - x0, p[1] - y0, "D", color="#3c9ee0", ms=8)
            ax.plot(v[0] - x0, v[1] - y0, "*", color="#49b06a", ms=15)
            ax.set_xticks([]); ax.set_yticks([])
        ax1.set_ylabel(f"z = {z0}", fontsize=9)
        ax1.set_title(f"{title}: argmax {ea:.1f} mm, plateau nearest centroid {ep:.1f} mm",
                      fontsize=9, loc="left")
        ax2.set_title("distance transform, plateau within 0.9 of the maximum outlined", fontsize=8, loc="left")
    handles = [plt.Line2D([], [], marker="x", ls="", color="#e0533d", mew=2.4, ms=10, label="argmax (as published)"),
               plt.Line2D([], [], marker="o", ls="", color="#8a8a8a", ms=7, label="centroid of the section"),
               plt.Line2D([], [], marker="D", ls="", color="#3c9ee0", ms=8, label="plateau point nearest the centroid"),
               plt.Line2D([], [], marker="*", ls="", color="#49b06a", ms=13, label="published umbilicus")]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=9, frameon=False)
    fig.suptitle(f"{scroll}: the maximum of the distance transform lives on a wide plateau", fontsize=11)
    fig.tight_layout(rect=[0, 0.035, 1, 0.98])
    fig.savefig(OUT / "plateau-on-papyrus.png", dpi=155)
    print("written", OUT / "plateau-on-papyrus.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    methods_compared()
    plateau_on_papyrus()
