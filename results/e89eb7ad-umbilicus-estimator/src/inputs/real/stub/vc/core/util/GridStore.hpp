#pragma once
// Minimal stand-in for villa's GridStore, enough to compile and run normalgridtools.cpp.
//
// normalgridtools.cpp uses exactly four things from it: get_all(), add(), size() and meta.
// The real class adds a spatial index, an mmap loader and a codec, none of which
// align_and_extract_umbilicus touches: it calls get_all() once and works on the paths.
#include <memory>
#include <opencv2/core/types.hpp>
#include <vector>

#include "utils/Json.hpp"

namespace vc::core::util {

class GridStore {
public:
    using Path = std::vector<cv::Point>;

    GridStore(const cv::Rect& bounds, int cell_size)
        : bounds_(bounds), cell_size_(cell_size) {}

    void add(const std::vector<cv::Point>& points)
    {
        paths_.push_back(std::make_shared<Path>(points));
    }

    std::vector<std::shared_ptr<Path>> get_all() const { return paths_; }

    cv::Size size() const { return bounds_.size(); }

    utils::Json meta;

private:
    cv::Rect bounds_;
    int cell_size_ = 1;
    std::vector<std::shared_ptr<Path>> paths_;
};

}  // namespace vc::core::util
