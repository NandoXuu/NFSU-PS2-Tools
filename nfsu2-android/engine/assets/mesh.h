// Formato NMSH (malha convertida a partir dos dados recuperados do GEOMETRY.BIN).
// Especificação completa em docs/formats/NMSH.md
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace nfsu2 {

struct MeshVertex {
    float px, py, pz;
    float nx, ny, nz;
};

struct SubMesh {
    std::string name;
    uint32_t indexOffset = 0;  // em índices
    uint32_t indexCount = 0;
};

struct Mesh {
    std::vector<MeshVertex> vertices;
    std::vector<uint32_t> indices;
    std::vector<SubMesh> submeshes;
    float aabbMin[3] = {0, 0, 0};
    float aabbMax[3] = {0, 0, 0};
};

// Carrega NMSH v1 da memória. Em caso de erro devolve false e preenche `err`.
bool LoadMeshFromMemory(const uint8_t* data, size_t size, Mesh& out, std::string& err);
bool LoadMeshFromFile(const std::string& path, Mesh& out, std::string& err);

// Serializa NMSH v1 (usado pelos testes e ferramentas C++).
std::vector<uint8_t> SerializeMesh(const Mesh& mesh);

}  // namespace nfsu2
