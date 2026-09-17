#pragma once
// Minimal stand-in for villa's utils::Json, enough to compile normalgridtools.cpp.
// The only use in that file is result.meta["umbilicus_x"] = float and meta["aligned"] = true.
#include <map>
#include <string>

namespace vc::core::util::utils {
struct Json {
    struct Value {
        double number = 0.0;
        bool boolean = false;
        Value& operator=(float v) { number = v; return *this; }
        Value& operator=(double v) { number = v; return *this; }
        Value& operator=(bool v) { boolean = v; return *this; }
    };
    std::map<std::string, Value> items;
    Value& operator[](const std::string& k) { return items[k]; }
};
}  // namespace vc::core::util::utils

namespace utils { using Json = vc::core::util::utils::Json; }
