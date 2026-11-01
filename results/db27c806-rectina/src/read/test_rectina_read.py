"""Unit test of rectina_read with a stub model (numpy only, CPU, seconds). Run: python3 test_rectina_read.py
Proves the lattice, the views, the shifted ensemble, the Hann stitching, the mean over starts and the output files. It does not load
a checkpoint: the real weights are covered by the parity check in README.md."""
import json, os, sys, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rectina_read as R


class Stub:
    """pixelwise and equivariant: p = sigmoid(mean over planes of x); so any correct stitching returns exactly that function of the stack"""
    depth, patch = 17, 32
    calls = 0
    def normalize(self, raw):
        return raw
    def predict(self, x, bf16):
        Stub.calls += 1
        return (1.0 / (1.0 + np.exp(-x.mean(1)))).astype(np.float32)


def expected(window):
    idx = R.centre_layers(window.shape[0])
    return (1.0 / (1.0 + np.exp(-window[idx].astype(np.float32).mean(0)))).astype(np.float32)


def main():
    rng = np.random.default_rng(0)
    # lattice
    for L in (10, 32, 33, 100, 129):
        p = R.positions(L, 32)
        assert p[0] == 0 and p[-1] == max(0, L - 32) and p == sorted(set(p)), (L, p)
        covered = np.zeros(L, bool)
        for s in p:
            covered[s:s + 32] = True
        assert covered.all(), L
    assert R.stride(128) == 64 and R.stride(384) == 192
    # views are inverse of each other
    a = rng.random((3, 7, 9)).astype(np.float32)
    for v in [(0, 0), (1, 0), (2, 0), (3, 0), (1, 1)]:
        assert np.array_equal(R.unview(R.view(a, v), v), a)
    # stitching returns the pixelwise function, on a size that is not a multiple of the patch, with no blank area
    H, W = 75, 90
    stack = rng.random((23, H, W)).astype(np.float32)
    m = Stub()
    for views in (R.VIEWS["1v"], R.VIEWS["2v"], R.VIEWS["4v"]):
        out, n = R.read_window(m, stack[3:20], views, True, False, 8)
        want = expected(stack[3:20])
        assert out.shape == (H, W) and n > 0
        assert np.abs(out - want).max() < 1e-5, np.abs(out - want).max()
    # an all blank window is skipped patch by patch: zero patches, zero map (a blank is not read)
    out, n = R.read_window(m, np.zeros((17, 40, 40), np.float32), R.VIEWS["2v"], True, False, 8)
    assert n == 0 and not out.any()
    # mean over starts equals the mean of the per start functions
    fin, rows = R.read_stack(m, stack, [0, 1, 2], R.VIEWS["2v"], None, True, False, 8, log=lambda *a: None)
    ref = np.mean([expected(stack[s:s + 17]) for s in (0, 1, 2)], 0)
    assert np.abs(fin - ref).max() < 1e-5 and [r[0] for r in rows] == [0, 1, 2]
    # a start past the end is refused
    try:
        R.read_stack(m, stack, [7], R.VIEWS["1v"], None, True, False, 8, log=lambda *a: None); raise AssertionError("not refused")
    except SystemExit:
        pass
    # divisor
    assert R.default_divisor(np.uint16) == 65280.0 and R.default_divisor(np.uint8) is None
    # outputs and compare
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR", "/data/tmp")) as d:
        R.write_outputs(d + "/o", fin, rows, dict(patch=32), "cpu")
        done = json.load(open(d + "/o/DONE"))
        assert set(done["files"]) == {"map.npy", "reads.csv"} and done["files"]["map.npy"] == R.sha256(d + "/o/map.npy")
        assert np.load(d + "/o/map.npy").dtype == np.float32
        assert open(d + "/o/reads.csv").readline().strip() == "start,seconds,patches,device"
        try:
            R.write_outputs(d + "/o", fin, rows, {}, "cpu"); raise AssertionError("overwrote")
        except SystemExit:
            pass
        np.save(d + "/a.npy", fin); np.save(d + "/b.npy", fin + np.float32(0.001)); np.save(d + "/c.npy", fin + np.float32(0.2))
        assert R.main(["compare", d + "/a.npy", d + "/b.npy"]) == 0
        assert R.main(["compare", d + "/a.npy", d + "/c.npy"]) == 14
        np.save(d + "/s.npy", (stack * 65280).astype(np.uint16))
        assert R.open_stack(d + "/s.npy").shape == (23, H, W)
    print("PASS: all checks")


if __name__ == "__main__":
    main()
