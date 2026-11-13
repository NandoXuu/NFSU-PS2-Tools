// Leitor binário com checagem de limites (little-endian).
#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <string>

namespace nfsu2 {

class BinaryReader {
public:
    BinaryReader(const uint8_t* data, size_t size) : data_(data), size_(size) {}

    bool ok() const { return ok_; }
    size_t pos() const { return pos_; }
    size_t remaining() const { return size_ - pos_; }

    template <typename T>
    T read() {
        T v{};
        if (!ok_ || sizeof(T) > size_ - pos_) { ok_ = false; return v; }
        std::memcpy(&v, data_ + pos_, sizeof(T));
        pos_ += sizeof(T);
        return v;
    }

    bool readBytes(void* dst, size_t n) {
        if (!ok_ || n > size_ - pos_) { ok_ = false; return false; }
        std::memcpy(dst, data_ + pos_, n);
        pos_ += n;
        return true;
    }

    bool skip(size_t n) {
        if (!ok_ || n > size_ - pos_) { ok_ = false; return false; }
        pos_ += n;
        return true;
    }

private:
    const uint8_t* data_;
    size_t size_;
    size_t pos_ = 0;
    bool ok_ = true;
};

}  // namespace nfsu2
