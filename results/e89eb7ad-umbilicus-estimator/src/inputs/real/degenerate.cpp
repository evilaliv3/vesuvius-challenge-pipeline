// The two assertions villa's own test makes about align_and_extract_umbilicus
// (core/test/test_normalgridtools.cpp:101-116), run against the real function.
#include <cmath>
#include <cstdio>
#include "vc/core/util/GridStore.hpp"
#include "vc/core/util/normalgridtools.hpp"
using vc::core::util::GridStore;
using vc::core::util::align_and_extract_umbilicus;
int main()
{
    GridStore empty(cv::Rect(0, 0, 100, 100), 10);
    cv::Vec2f a = align_and_extract_umbilicus(empty);
    std::printf("empty GridStore -> (%f, %f)   NaN as the test expects: %s\n",
                a[0], a[1], (std::isnan(a[0]) && std::isnan(a[1])) ? "yes" : "NO");
    GridStore one(cv::Rect(0, 0, 100, 100), 10);
    one.add({cv::Point(5, 5)});
    cv::Vec2f b = align_and_extract_umbilicus(one);
    std::printf("single-point path -> (%f, %f)   NaN as the test expects: %s\n",
                b[0], b[1], std::isnan(b[0]) ? "yes" : "NO");
    return 0;
}
