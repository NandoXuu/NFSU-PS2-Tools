#pragma once
#include <cstdint>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

namespace nfsu2 {

inline bool ReadWholeFile(const std::string& path, std::vector<uint8_t>& out) {
    std::ifstream f(path, std::ios::binary);
    if (!f) return false;
    out.assign(std::istreambuf_iterator<char>(f), std::istreambuf_iterator<char>());
    return true;
}

}  // namespace nfsu2
