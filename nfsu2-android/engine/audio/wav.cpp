#include "wav.h"

#include <cstring>

#include "../core/binary_reader.h"
#include "../core/file_io.h"

namespace nfsu2 {

bool LoadWavFromMemory(const uint8_t* data, size_t size, PcmClip& out, std::string& err) {
    BinaryReader r(data, size);
    char tag[4];
    if (!r.readBytes(tag, 4) || std::memcmp(tag, "RIFF", 4) != 0) { err = "WAV: sem RIFF"; return false; }
    r.skip(4);  // tamanho do RIFF (alguns exportadores gravam errado; nao confiamos nele)
    if (!r.readBytes(tag, 4) || std::memcmp(tag, "WAVE", 4) != 0) { err = "WAV: sem WAVE"; return false; }

    bool haveFmt = false;
    uint16_t fmtTag = 0, channels = 0, bits = 0;
    uint32_t rate = 0;
    while (r.remaining() >= 8) {
        char id[4];
        r.readBytes(id, 4);
        uint32_t len = r.read<uint32_t>();
        if (std::memcmp(id, "fmt ", 4) == 0) {
            if (len < 16) { err = "WAV: chunk fmt curto"; return false; }
            fmtTag = r.read<uint16_t>();
            channels = r.read<uint16_t>();
            rate = r.read<uint32_t>();
            r.skip(6);  // byte rate + block align
            bits = r.read<uint16_t>();
            if (!r.skip(len - 16)) { err = "WAV: fmt truncado"; return false; }
            haveFmt = true;
        } else if (std::memcmp(id, "data", 4) == 0) {
            if (!haveFmt) { err = "WAV: data antes de fmt"; return false; }
            if (fmtTag != 1 || bits != 16) { err = "WAV: apenas PCM 16-bit"; return false; }
            if (channels == 0 || channels > 2 || rate == 0) { err = "WAV: parametros invalidos"; return false; }
            if (len > r.remaining()) len = uint32_t(r.remaining());  // tolera data truncado
            const size_t n = len / 2 / channels * channels;
            PcmClip c;
            c.sampleRate = rate;
            c.channels = channels;
            c.samples.resize(n);
            if (n) r.readBytes(c.samples.data(), n * 2);
            out = std::move(c);
            return true;
        } else {
            if (!r.skip(len + (len & 1))) break;
        }
    }
    err = "WAV: chunk data nao encontrado";
    return false;
}

bool LoadWavFromFile(const std::string& path, PcmClip& out, std::string& err) {
    std::vector<uint8_t> buf;
    if (!ReadWholeFile(path, buf)) { err = "nao foi possivel abrir " + path; return false; }
    return LoadWavFromMemory(buf.data(), buf.size(), out, err);
}

}  // namespace nfsu2
