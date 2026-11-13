// Formato NTEX: textura RGBA8 convertida dos PNGs recuperados (TPK -> PNG -> NTEX).
// Especificação em docs/formats/NTEX.md
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace nfsu2 {

struct Texture {
    uint32_t width = 0;
    uint32_t height = 0;
    std::vector<uint8_t> rgba;  // width*height*4
};

bool LoadTextureFromMemory(const uint8_t* data, size_t size, Texture& out, std::string& err);
bool LoadTextureFromFile(const std::string& path, Texture& out, std::string& err);
std::vector<uint8_t> SerializeTexture(const Texture& tex);

}  // namespace nfsu2
