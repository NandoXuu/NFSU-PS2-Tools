#include "mesh.h"

#include <cmath>
#include <cstring>

#include "../core/binary_reader.h"
#include "../core/file_io.h"

namespace nfsu2 {

namespace {
constexpr uint32_t kMagic = 0x48534D4E;  // "NMSH" little-endian
constexpr uint32_t kVersion = 1;
constexpr size_t kNameBytes = 32;
}  // namespace

bool LoadMeshFromMemory(const uint8_t* data, size_t size, Mesh& out, std::string& err) {
    BinaryReader r(data, size);
    if (r.read<uint32_t>() != kMagic) { err = "NMSH: magic invalido"; return false; }
    if (r.read<uint32_t>() != kVersion) { err = "NMSH: versao nao suportada"; return false; }
    const uint32_t nv = r.read<uint32_t>();
    const uint32_t ni = r.read<uint32_t>();
    const uint32_t ns = r.read<uint32_t>();
    const uint32_t flags = r.read<uint32_t>();
    (void)flags;  // bit0 reservado para UV (ainda nao decodificado nos dados originais)
    float bb[6];
    for (float& f : bb) f = r.read<float>();
    if (!r.ok()) { err = "NMSH: cabecalho truncado"; return false; }

    // Valida tamanhos antes de alocar (evita alocacao gigante por arquivo corrompido).
    const uint64_t need = uint64_t(ns) * (kNameBytes + 8) + uint64_t(nv) * sizeof(MeshVertex) +
                          uint64_t(ni) * 4;
    if (need > r.remaining()) { err = "NMSH: dados truncados"; return false; }
    if (ni % 3 != 0) { err = "NMSH: contagem de indices nao multipla de 3"; return false; }

    Mesh m;
    m.submeshes.resize(ns);
    for (SubMesh& s : m.submeshes) {
        char name[kNameBytes + 1] = {};
        r.readBytes(name, kNameBytes);
        s.name = name;
        s.indexOffset = r.read<uint32_t>();
        s.indexCount = r.read<uint32_t>();
        if (uint64_t(s.indexOffset) + s.indexCount > ni) { err = "NMSH: submalha fora do limite"; return false; }
    }
    m.vertices.resize(nv);
    if (nv) r.readBytes(m.vertices.data(), size_t(nv) * sizeof(MeshVertex));
    m.indices.resize(ni);
    if (ni) r.readBytes(m.indices.data(), size_t(ni) * 4);
    if (!r.ok()) { err = "NMSH: leitura falhou"; return false; }

    for (uint32_t idx : m.indices)
        if (idx >= nv) { err = "NMSH: indice fora do intervalo"; return false; }
    for (const MeshVertex& v : m.vertices)
        if (!std::isfinite(v.px) || !std::isfinite(v.py) || !std::isfinite(v.pz)) {
            err = "NMSH: vertice nao finito";
            return false;
        }

    std::memcpy(m.aabbMin, bb, sizeof(float) * 3);
    std::memcpy(m.aabbMax, bb + 3, sizeof(float) * 3);
    out = std::move(m);
    return true;
}

bool LoadMeshFromFile(const std::string& path, Mesh& out, std::string& err) {
    std::vector<uint8_t> buf;
    if (!ReadWholeFile(path, buf)) { err = "nao foi possivel abrir " + path; return false; }
    return LoadMeshFromMemory(buf.data(), buf.size(), out, err);
}

std::vector<uint8_t> SerializeMesh(const Mesh& mesh) {
    std::vector<uint8_t> b;
    auto put = [&b](const void* p, size_t n) {
        const uint8_t* c = static_cast<const uint8_t*>(p);
        b.insert(b.end(), c, c + n);
    };
    auto put32 = [&put](uint32_t v) { put(&v, 4); };
    put32(kMagic); put32(kVersion);
    put32(uint32_t(mesh.vertices.size()));
    put32(uint32_t(mesh.indices.size()));
    put32(uint32_t(mesh.submeshes.size()));
    put32(0);
    put(mesh.aabbMin, 12); put(mesh.aabbMax, 12);
    for (const SubMesh& s : mesh.submeshes) {
        char name[kNameBytes] = {};
        std::strncpy(name, s.name.c_str(), kNameBytes - 1);
        put(name, kNameBytes);
        put32(s.indexOffset); put32(s.indexCount);
    }
    if (!mesh.vertices.empty()) put(mesh.vertices.data(), mesh.vertices.size() * sizeof(MeshVertex));
    if (!mesh.indices.empty()) put(mesh.indices.data(), mesh.indices.size() * 4);
    return b;
}

}  // namespace nfsu2
