// Valida os assets reais convertidos. Só roda se NFSU2_REAL_ASSETS apontar para uma pasta
// (estrutura: <pasta>/diag/car.nmsh, <pasta>/diag/tex.ntex, <pasta>/diag/clip.wav).
// Sem a variável, o teste é pulado (os assets originais não ficam no repositório).
#include <cstdio>
#include <cstdlib>
#include <string>

#include "assets/mesh.h"
#include "assets/texture.h"
#include "audio/wav.h"
#include "check.h"

int main() {
    using namespace nfsu2;
    const char* dir = std::getenv("NFSU2_REAL_ASSETS");
    if (!dir) {
        std::puts("PULADO (NFSU2_REAL_ASSETS nao definido)");
        return 0;
    }
    std::string err;
    const std::string base = std::string(dir) + "/diag/";

    Mesh m;
    CHECK(LoadMeshFromFile(base + "car.nmsh", m, err));
    if (!err.empty()) std::fprintf(stderr, "mesh: %s\n", err.c_str());
    CHECK(m.vertices.size() > 1000);
    CHECK(m.indices.size() > 3000);
    CHECK(!m.submeshes.empty());
    for (int i = 0; i < 3; ++i) CHECK(m.aabbMax[i] >= m.aabbMin[i]);
    std::printf("mesh: %zu vertices, %zu triangulos, %zu submalhas\n", m.vertices.size(),
                m.indices.size() / 3, m.submeshes.size());

    // Normais devem ser aproximadamente unitarias (valida a decodificacao s8/127).
    size_t unit = 0;
    for (const MeshVertex& v : m.vertices) {
        float l2 = v.nx * v.nx + v.ny * v.ny + v.nz * v.nz;
        if (l2 > 0.9f && l2 < 1.1f) ++unit;
    }
    CHECK(unit * 100 >= m.vertices.size() * 90);

    Texture t;
    if (LoadTextureFromFile(base + "tex.ntex", t, err))
        std::printf("textura: %ux%u\n", t.width, t.height);
    else
        CHECK(false);

    PcmClip c;
    CHECK(LoadWavFromFile(base + "clip.wav", c, err));
    CHECK(c.frames() > 0);
    std::printf("audio: %u Hz, %u canal(is), %.2f s\n", c.sampleRate, unsigned(c.channels), c.durationSeconds());

    TEST_MAIN_END();
}
