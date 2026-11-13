#include <string>

#include "assets/texture.h"
#include "check.h"

int main() {
    using namespace nfsu2;
    std::string err;

    Texture t;
    t.width = 4;
    t.height = 2;
    t.rgba.resize(4 * 2 * 4);
    for (size_t i = 0; i < t.rgba.size(); ++i) t.rgba[i] = uint8_t(i * 7);

    std::vector<uint8_t> blob = SerializeTexture(t);
    Texture o;
    CHECK(LoadTextureFromMemory(blob.data(), blob.size(), o, err));
    CHECK(o.width == 4 && o.height == 2);
    CHECK(o.rgba == t.rgba);

    // Pixels faltando.
    CHECK(!LoadTextureFromMemory(blob.data(), blob.size() - 1, o, err));
    // Pixels sobrando.
    std::vector<uint8_t> extra = blob;
    extra.push_back(0);
    CHECK(!LoadTextureFromMemory(extra.data(), extra.size(), o, err));
    // Dimensao zero.
    std::vector<uint8_t> zero = blob;
    zero[8] = zero[9] = zero[10] = zero[11] = 0;
    CHECK(!LoadTextureFromMemory(zero.data(), zero.size(), o, err));
    // Dimensao absurda.
    std::vector<uint8_t> big = blob;
    big[11] = 0x7F;
    CHECK(!LoadTextureFromMemory(big.data(), big.size(), o, err));
    // Truncamentos.
    for (size_t cut = 0; cut < 20; ++cut) CHECK(!LoadTextureFromMemory(blob.data(), cut, o, err));

    TEST_MAIN_END();
}
