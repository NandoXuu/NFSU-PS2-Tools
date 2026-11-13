// Carregador WAV PCM 16-bit (formato dos áudios recuperados dos ABK).
#pragma once
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace nfsu2 {

struct PcmClip {
    uint32_t sampleRate = 0;
    uint16_t channels = 0;
    std::vector<int16_t> samples;  // intercalado
    size_t frames() const { return channels ? samples.size() / channels : 0; }
    double durationSeconds() const { return sampleRate ? double(frames()) / sampleRate : 0.0; }
};

bool LoadWavFromMemory(const uint8_t* data, size_t size, PcmClip& out, std::string& err);
bool LoadWavFromFile(const std::string& path, PcmClip& out, std::string& err);

}  // namespace nfsu2
