// Renderer OpenGL ES 3.0+ (somente Android). Interface mínima para a cena de diagnóstico.
#pragma once
#include <cstdint>

#include "../assets/mesh.h"
#include "../core/math.h"

namespace nfsu2 {

class GlRenderer {
public:
    GlRenderer() = default;
    ~GlRenderer();
    GlRenderer(const GlRenderer&) = delete;
    GlRenderer& operator=(const GlRenderer&) = delete;

    // Deve ser chamado com o contexto GL atual.
    bool init(const char** errorOut);
    void resize(int width, int height);
    bool uploadMesh(const Mesh& mesh);
    void clearError();  // fundo vermelho indica falha de carga (sem modelo substituto)
    void draw(float yaw, float pitch, float distance, bool showError);
    void shutdown();

    int drawCalls() const { return drawCalls_; }

private:
    unsigned program_ = 0, vao_ = 0, vbo_ = 0, ebo_ = 0;
    int locMvp_ = -1, locModel_ = -1;
    int width_ = 1, height_ = 1;
    int indexCount_ = 0;
    float center_[3] = {0, 0, 0};
    float radius_ = 1.0f;
    int drawCalls_ = 0;
    const char* lastError_ = nullptr;
};

}  // namespace nfsu2
