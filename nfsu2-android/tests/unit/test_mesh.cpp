#include <string>

#include "assets/mesh.h"
#include "check.h"

static nfsu2::Mesh makeQuad() {
    nfsu2::Mesh m;
    m.vertices = {{0, 0, 0, 0, 0, 1}, {1, 0, 0, 0, 0, 1}, {1, 1, 0, 0, 0, 1}, {0, 1, 0, 0, 0, 1}};
    m.indices = {0, 1, 2, 0, 2, 3};
    m.submeshes = {{"quad", 0, 6}};
    m.aabbMax[0] = m.aabbMax[1] = 1;
    return m;
}

int main() {
    using namespace nfsu2;
    std::string err;

    // Ida e volta.
    Mesh src = makeQuad();
    std::vector<uint8_t> blob = SerializeMesh(src);
    Mesh dst;
    CHECK(LoadMeshFromMemory(blob.data(), blob.size(), dst, err));
    CHECK(dst.vertices.size() == 4);
    CHECK(dst.indices.size() == 6);
    CHECK(dst.submeshes.size() == 1 && dst.submeshes[0].name == "quad");
    CHECK(dst.vertices[2].px == 1.0f && dst.vertices[2].py == 1.0f);
    CHECK(dst.aabbMax[0] == 1.0f);

    // Magic invalido.
    std::vector<uint8_t> bad = blob;
    bad[0] ^= 0xFF;
    CHECK(!LoadMeshFromMemory(bad.data(), bad.size(), dst, err));

    // Truncado em varios pontos: nunca deve travar nem aceitar.
    for (size_t cut = 0; cut < blob.size(); cut += 7) {
        Mesh tmp;
        CHECK(!LoadMeshFromMemory(blob.data(), cut, tmp, err));
    }

    // Indice fora do intervalo.
    Mesh oob = makeQuad();
    oob.indices[5] = 99;
    std::vector<uint8_t> b2 = SerializeMesh(oob);
    CHECK(!LoadMeshFromMemory(b2.data(), b2.size(), dst, err));

    // Vertice NaN.
    Mesh nan = makeQuad();
    nan.vertices[0].px = std::numeric_limits<float>::quiet_NaN();
    std::vector<uint8_t> b3 = SerializeMesh(nan);
    CHECK(!LoadMeshFromMemory(b3.data(), b3.size(), dst, err));

    // Contagem enorme no cabecalho (alocacao maliciosa) deve ser rejeitada sem alocar.
    std::vector<uint8_t> huge = blob;
    huge[8] = huge[9] = huge[10] = huge[11] = 0xFF;  // vertexCount = 0xFFFFFFFF
    CHECK(!LoadMeshFromMemory(huge.data(), huge.size(), dst, err));

    TEST_MAIN_END();
}
