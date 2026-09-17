"""The estimators under test, and the post-filter that was tried and rejected.

Every estimator takes the same input, the filled mask of the largest connected component of the
sheet mask and its distance transform, and returns one point (x, y) in slice coordinates. Keeping
the mask outside the estimators is what makes the comparison like for like: they all see the same
section, and only the reading of it changes.
"""
import numpy as np
from scipy import ndimage as ndi

MASK_THRESHOLD = 40         # the published estimator's threshold on the surface probability
CLOSING_ITERS = 4


def section(slice_):
    """The filled largest connected component of the sheet mask, and its distance transform."""
    m = ndi.binary_closing(slice_ > MASK_THRESHOLD, iterations=CLOSING_ITERS)
    labels, n = ndi.label(m)
    if n == 0:
        return None, None
    sizes = ndi.sum(m, labels, range(1, n + 1))
    mask = ndi.binary_fill_holes(labels == (1 + int(np.argmax(sizes))))
    return mask, ndi.distance_transform_edt(mask)


def argmax(mask, dist):
    """The published rule: the point of maximum distance to the boundary."""
    y, x = np.unravel_index(int(np.argmax(dist)), dist.shape)
    return float(x), float(y)


def centroid(mask, dist):
    """The centroid of the filled section."""
    y, x = ndi.center_of_mass(mask)
    return float(x), float(y)


def plateau_centroid(mask, dist, q=0.9):
    """The centroid of the plateau, meaning the pixels within q of the maximum distance."""
    y, x = ndi.center_of_mass(dist >= q * dist.max())
    return float(x), float(y)


def plateau_nearest_centroid(mask, dist, q=0.9):
    """The plateau point nearest the centroid of the section. This is the one that wins.

    The distance transform of a scroll section has a wide, nearly flat plateau. Its argmax picks one
    pixel out of many almost equal ones and jumps between lobes from slice to slice; the plateau
    says where the core is and the centroid says which end of it belongs to the body of the section.
    """
    cy, cx = ndi.center_of_mass(mask)
    ys, xs = np.where(dist >= q * dist.max())
    j = int(np.argmin((xs - cx) ** 2 + (ys - cy) ** 2))
    return float(xs[j]), float(ys[j])


def median_of(*points):
    """Coordinate-wise median of several estimates of the same slice."""
    a = np.array(points, float)
    return float(np.median(a[:, 0])), float(np.median(a[:, 1]))


# What each rule is called in a figure or a table, for readers who have never seen this code.
DISPLAY = {
    "argmax": "max distance-to-boundary (published rule)",
    "centroid": "centroid of the section",
    "plateau_centroid": "centroid of the plateau (within 0.9 of max)",
    "plateau_nearest_centroid": "plateau point nearest the centroid (proposed)",
    "argmax + hampel": "max distance, jumping points rejected",
    "fake axis (control)": "constant axis at the centre of the field (control)",
}


def display(name):
    return DISPLAY.get(name, name)


ESTIMATORS = {
    "argmax": argmax,                                   # as published
    "centroid": centroid,
    "plateau_centroid": plateau_centroid,
    "plateau_nearest_centroid": plateau_nearest_centroid,
}


def hampel_reject(points, half_window=3, threshold=2.0):
    """Drop control points that jump away from their neighbours.

    A Hampel-type identifier (Hampel 1974; Pearson et al., Generalized Hampel Filters, 2016) with
    two deliberate differences: the scale is the median deviation over the whole scroll rather than
    a per-window MAD, so a run of consecutive bad slices cannot mask itself, and the point is
    dropped rather than replaced.

    It is a large gain on top of `argmax` and close to nothing on top of a stable estimator, which
    is the honest reason it is here as a measurement and not as a default.
    """
    p = np.asarray(points, float)
    if len(p) < 5:
        return p, np.zeros(len(p))
    dev = np.empty(len(p))
    for i in range(len(p)):
        lo, hi = max(0, i - half_window), min(len(p), i + half_window + 1)
        neighbours = np.delete(p[lo:hi, :2], i - lo, axis=0)
        dev[i] = np.hypot(*(p[i, :2] - np.median(neighbours, axis=0)))
    return p[dev <= threshold * np.median(dev)], dev
