// Run villa's own align_and_extract_umbilicus, compiled from its own source file, on a real
// published grid.
//
// Nothing in core/src/normalgridtools.cpp is modified: it is compiled as it stands, against real
// OpenCV 4.10 headers and a minimal GridStore that provides the four members it uses. The paths
// come from a dump of a published .grid file.
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>

#include "vc/core/util/GridStore.hpp"
#include "vc/core/util/normalgridtools.hpp"

using vc::core::util::GridStore;
using vc::core::util::align_and_extract_umbilicus;

int main(int argc, char** argv)
{
    if (argc < 2) { std::fprintf(stderr, "usage: driver <dump> [repeats]\n"); return 2; }
    const int repeats = argc > 2 ? std::atoi(argv[2]) : 1;

    std::ifstream in(argv[1], std::ios::binary);
    int w = 0, h = 0, npaths = 0;
    in.read(reinterpret_cast<char*>(&w), 4);
    in.read(reinterpret_cast<char*>(&h), 4);
    in.read(reinterpret_cast<char*>(&npaths), 4);

    GridStore gs(cv::Rect(0, 0, w, h), 64);
    long points = 0, segments = 0;
    for (int i = 0; i < npaths; ++i) {
        int n = 0;
        in.read(reinterpret_cast<char*>(&n), 4);
        std::vector<cv::Point> path(n);
        for (int j = 0; j < n; ++j) {
            int x = 0, y = 0;
            in.read(reinterpret_cast<char*>(&x), 4);
            in.read(reinterpret_cast<char*>(&y), 4);
            path[j] = cv::Point(x, y);
        }
        points += n;
        if (n >= 2) segments += n - 1;
        gs.add(path);
    }
    std::printf("grid %dx%d, %d paths, %ld points, %ld segments\n", w, h, npaths, points, segments);

    for (int r = 0; r < repeats; ++r) {
        cv::Vec2f u = align_and_extract_umbilicus(gs);
        const bool outside = !(u[0] >= 0 && u[0] <= w && u[1] >= 0 && u[1] <= h);
        std::printf("run %d: umbilicus (%.1f, %.1f)%s\n", r, u[0], u[1],
                    outside ? "   OUTSIDE THE GRID" : "");
        std::fflush(stdout);
    }
    return 0;
}
