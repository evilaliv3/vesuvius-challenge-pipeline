// Companion to core/test/test_normalgridtools.cpp: the same four calls, with the same sections
// and seeds, printing the estimate, its distance from the known centre in millimetres and the
// tolerance the test asserts. The test itself only prints pass or fail; this prints the margin.
// The section builder is copied from the test verbatim so that the input is identical.
#include "vc/core/util/normalgridtools.hpp"
#include "vc/core/util/GridStore.hpp"
#include <opencv2/core.hpp>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <random>
#include <vector>
using namespace vc::core::util;
namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kUnitMm = 0.009362;
constexpr int kSide = 8000;
constexpr double kCentreX = 4000.0, kCentreY = 4000.0;
void addSyntheticSection(GridStore& gs, double frac, int thin_ratio, std::uint32_t thin_seed)
{
    std::mt19937 rng(thin_seed);
    std::uniform_int_distribution<int> keep(1, std::max(1, thin_ratio));
    for (double r = 300.0; r <= 3500.0; r += 80.0) {
        const int n = std::max(8, (int)(2.0 * kPi * r / 12.0));
        const int m = std::max(3, (int)(n * frac));
        std::vector<cv::Point> pts;
        pts.reserve(m);
        for (int i = 0; i < m; ++i) {
            const double th = frac >= 1.0 ? 2.0 * kPi * i / m : 2.0 * kPi * frac * i / (m - 1);
            pts.emplace_back(cvRound(kCentreX + r * std::cos(th)), cvRound(kCentreY + r * std::sin(th)));
        }
        for (int i = 0; i + 1 < m; ++i) {
            const double mid_x = 0.5 * (pts[i].x + pts[i + 1].x);
            if (thin_ratio > 1 && mid_x < kCentreX && keep(rng) != 1) continue;
            gs.add({pts[i], pts[i + 1]});
        }
    }
}
double errorMm(const cv::Vec2f& u) { return std::hypot(u[0] - kCentreX, u[1] - kCentreY) * kUnitMm; }
bool insideGrid(const cv::Vec2f& u) { return u[0] >= 0.0f && u[0] <= kSide && u[1] >= 0.0f && u[1] <= kSide; }
void report(const char* name, double frac, int thin, std::uint32_t thin_seed, std::uint32_t seed, double tol_mm)
{
    GridStore gs(cv::Rect(0, 0, kSide, kSide), 64);
    addSyntheticSection(gs, frac, thin, thin_seed);
    auto u = align_and_extract_umbilicus(gs, seed);
    std::printf("%-22s segments=%zu estimate=(%.2f, %.2f) inside=%s distance=%.3f mm tolerance=%.1f mm margin=%.3f mm %s\n",
        name, gs.get_all().size(), u[0], u[1], insideGrid(u) ? "yes" : "no", errorMm(u), tol_mm, tol_mm - errorMm(u),
        errorMm(u) < tol_mm && insideGrid(u) ? "PASS" : "FAIL");
}
}
int main()
{
    {
        GridStore gs(cv::Rect(0, 0, kSide, kSide), 64);
        addSyntheticSection(gs, 1.0, 1, 0);
        auto a = align_and_extract_umbilicus(gs, 7u);
        auto b = align_and_extract_umbilicus(gs, 7u);
        std::printf("%-22s a=(%.4f, %.4f) b=(%.4f, %.4f) identical=%s %s\n", "seed-repeatable",
            a[0], a[1], b[0], b[1], (a[0] == b[0] && a[1] == b[1]) ? "yes" : "no",
            (a[0] == b[0] && a[1] == b[1]) ? "PASS" : "FAIL");
    }
    report("concentric-circles", 1.0, 1, 0, 1u, 1.0);
    report("half-circle", 0.5, 1, 0, 1u, 5.0);
    report("thinned-1:10", 1.0, 10, 3u, 1u, 4.5);
    return 0;
}
