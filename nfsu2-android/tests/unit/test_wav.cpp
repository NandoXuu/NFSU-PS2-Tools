#include <cstring>
#include <string>
#include <vector>

#include "audio/wav.h"
#include "check.h"

static std::vector<uint8_t> makeWav(uint32_t rate, uint16_t ch, const std::vector<int16_t>& s) {
    std::vector<uint8_t> b;
    auto p = [&b](const void* d, size_t n) {
        const uint8_t* c = static_cast<const uint8_t*>(d);
        b.insert(b.end(), c, c + n);
    };
    auto u32 = [&p](uint32_t v) { p(&v, 4); };
    auto u16 = [&p](uint16_t v) { p(&v, 2); };
    const uint32_t dataBytes = uint32_t(s.size() * 2);
    p("RIFF", 4); u32(36 + dataBytes); p("WAVE", 4);
    p("fmt ", 4); u32(16); u16(1); u16(ch); u32(rate); u32(rate * ch * 2); u16(uint16_t(ch * 2)); u16(16);
    p("data", 4); u32(dataBytes); p(s.data(), dataBytes);
    return b;
}

int main() {
    using namespace nfsu2;
    std::string err;

    std::vector<int16_t> samples = {0, 100, -100, 32767, -32768, 5};
    auto mono = makeWav(20000, 1, samples);
    PcmClip c;
    CHECK(LoadWavFromMemory(mono.data(), mono.size(), c, err));
    CHECK(c.sampleRate == 20000 && c.channels == 1);
    CHECK(c.samples == samples);
    CHECK(c.frames() == 6);
    CHECK(c.durationSeconds() > 0.0002 && c.durationSeconds() < 0.0004);

    auto stereo = makeWav(44100, 2, samples);
    CHECK(LoadWavFromMemory(stereo.data(), stereo.size(), c, err));
    CHECK(c.channels == 2 && c.frames() == 3);

    // Tamanho do RIFF errado (visto em exportadores) deve ser tolerado.
    auto wrongRiff = mono;
    wrongRiff[4] = wrongRiff[5] = wrongRiff[6] = wrongRiff[7] = 0;
    CHECK(LoadWavFromMemory(wrongRiff.data(), wrongRiff.size(), c, err));

    // Data truncado: carrega o que existe.
    auto trunc = mono;
    trunc.resize(trunc.size() - 3);
    CHECK(LoadWavFromMemory(trunc.data(), trunc.size(), c, err));

    // Entradas invalidas.
    auto bad = mono;
    bad[0] = 'X';
    CHECK(!LoadWavFromMemory(bad.data(), bad.size(), c, err));
    for (size_t cut = 0; cut < 40; ++cut) {
        PcmClip tmp;
        LoadWavFromMemory(mono.data(), cut, tmp, err);  // nao deve travar
    }
    auto notPcm = mono;
    notPcm[20] = 3;  // formato float
    CHECK(!LoadWavFromMemory(notPcm.data(), notPcm.size(), c, err));

    TEST_MAIN_END();
}
