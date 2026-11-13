#include "texture.h"

#include "../core/binary_reader.h"
#include "../core/file_io.h"

namespace nfsu2 {

// "NTEX" little-endian = 'N' | 'T'<<8 | 'E'<<16 | 'X'<<24
static constexpr uint32_t kNtexMagic = 0x5845544E;
static constexpr uint32_t kNtexVersion = 1;
static constexpr uint32_t kFormatRGBA8 = 1;
static constexpr uint32_t kMaxDim = 8192;

bool LoadTextureFromMemory(const uint8_t* data, size_t size, Texture& out, std::string& err) {
    BinaryReader r(data, size);
    if (r.read<uint32_t>() != kNtexMagic) { err = "NTEX: magic invalido"; return false; }
    if (r.read<uint32_t>() != kNtexVersion) { err = "NTEX: versao nao suportada"; return false; }
    const uint32_t w = r.read<uint32_t>();
    const uint32_t h = r.read<uint32_t>();
    const uint32_t fmt = r.read<uint32_t>();
    if (!r.ok()) { err = "NTEX: cabecalho truncado"; return false; }
    if (fmt != kFormatRGBA8) { err = "NTEX: formato de pixel nao suportado"; return false; }
    if (w == 0 || h == 0 || w > kMaxDim || h > kMaxDim) { err = "NTEX: dimensoes invalidas"; return false; }
    const uint64_t bytes = uint64_t(w) * h * 4;
    if (bytes != r.remaining()) { err = "NTEX: tamanho dos pixels nao confere"; return false; }
    Texture t;
    t.width = w;
    t.height = h;
    t.rgba.resize(size_t(bytes));
    r.readBytes(t.rgba.data(), size_t(bytes));
    out = std::move(t);
    return true;
}

bool LoadTextureFromFile(const std::string& path, Texture& out, std::string& err) {
    std::vector<uint8_t> buf;
    if (!ReadWholeFile(path, buf)) { err = "nao foi possivel abrir " + path; return false; }
    return LoadTextureFromMemory(buf.data(), buf.size(), out, err);
}

std::vector<uint8_t> SerializeTexture(const Texture& tex) {
    std::vector<uint8_t> b;
    auto put32 = [&b](uint32_t v) {
        const uint8_t* c = reinterpret_cast<const uint8_t*>(&v);
        b.insert(b.end(), c, c + 4);
    };
    put32(kNtexMagic); put32(kNtexVersion); put32(tex.width); put32(tex.height); put32(kFormatRGBA8);
    b.insert(b.end(), tex.rgba.begin(), tex.rgba.end());
    return b;
}

}  // namespace nfsu2
