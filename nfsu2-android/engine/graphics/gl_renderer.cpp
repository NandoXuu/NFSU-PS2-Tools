#include "gl_renderer.h"

#include <GLES3/gl3.h>

#include <algorithm>
#include <cmath>

namespace nfsu2 {

namespace {

const char* kVertexSrc = R"(#version 300 es
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
uniform mat4 uMvp;
uniform mat4 uModel;
out vec3 vNrm;
void main() {
    vNrm = mat3(uModel) * aNrm;
    gl_Position = uMvp * vec4(aPos, 1.0);
}
)";

const char* kFragmentSrc = R"(#version 300 es
precision mediump float;
in vec3 vNrm;
out vec4 oColor;
void main() {
    vec3 n = normalize(vNrm);
    float d = max(dot(n, normalize(vec3(0.4, 0.8, 0.5))), 0.0);
    oColor = vec4(vec3(0.15) + vec3(0.85) * d, 1.0);
}
)";

GLuint compile(GLenum type, const char* src, const char** err) {
    GLuint s = glCreateShader(type);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    GLint ok = 0;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        *err = type == GL_VERTEX_SHADER ? "falha ao compilar vertex shader" : "falha ao compilar fragment shader";
        glDeleteShader(s);
        return 0;
    }
    return s;
}

}  // namespace

GlRenderer::~GlRenderer() { shutdown(); }

bool GlRenderer::init(const char** errorOut) {
    const char* err = nullptr;
    GLuint vs = compile(GL_VERTEX_SHADER, kVertexSrc, &err);
    GLuint fs = vs ? compile(GL_FRAGMENT_SHADER, kFragmentSrc, &err) : 0;
    if (!vs || !fs) {
        if (errorOut) *errorOut = err;
        if (vs) glDeleteShader(vs);
        return false;
    }
    program_ = glCreateProgram();
    glAttachShader(program_, vs);
    glAttachShader(program_, fs);
    glLinkProgram(program_);
    glDeleteShader(vs);
    glDeleteShader(fs);
    GLint ok = 0;
    glGetProgramiv(program_, GL_LINK_STATUS, &ok);
    if (!ok) {
        if (errorOut) *errorOut = "falha ao linkar programa";
        return false;
    }
    locMvp_ = glGetUniformLocation(program_, "uMvp");
    locModel_ = glGetUniformLocation(program_, "uModel");
    glEnable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);  // winding das strips ainda eh hipotese; nao descartar faces
    return true;
}

void GlRenderer::resize(int w, int h) {
    width_ = std::max(w, 1);
    height_ = std::max(h, 1);
    glViewport(0, 0, width_, height_);
}

bool GlRenderer::uploadMesh(const Mesh& mesh) {
    if (mesh.vertices.empty() || mesh.indices.empty()) return false;
    if (!vao_) glGenVertexArrays(1, &vao_);
    if (!vbo_) glGenBuffers(1, &vbo_);
    if (!ebo_) glGenBuffers(1, &ebo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, GLsizeiptr(mesh.vertices.size() * sizeof(MeshVertex)),
                 mesh.vertices.data(), GL_STATIC_DRAW);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo_);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, GLsizeiptr(mesh.indices.size() * 4), mesh.indices.data(),
                 GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(MeshVertex), (void*)0);
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(MeshVertex), (void*)(3 * sizeof(float)));
    glBindVertexArray(0);
    indexCount_ = int(mesh.indices.size());
    float r2 = 0;
    for (int i = 0; i < 3; ++i) center_[i] = 0.5f * (mesh.aabbMin[i] + mesh.aabbMax[i]);
    for (int i = 0; i < 3; ++i) {
        float e = 0.5f * (mesh.aabbMax[i] - mesh.aabbMin[i]);
        r2 += e * e;
    }
    radius_ = std::max(std::sqrt(r2), 0.001f);
    return true;
}

void GlRenderer::draw(float yaw, float pitch, float distance, bool showError) {
    drawCalls_ = 0;
    if (showError) glClearColor(0.5f, 0.0f, 0.0f, 1.0f);
    else glClearColor(0.05f, 0.06f, 0.09f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    if (showError || indexCount_ == 0) return;

    const float dist = radius_ * distance;
    Mat4 proj = perspective(0.9f, float(width_) / float(height_), radius_ * 0.05f, radius_ * 20.0f);
    Mat4 model = mul(rotateY(yaw), rotateX(pitch));
    Mat4 center = translate(-center_[0], -center_[1], -center_[2]);
    Mat4 view = translate(0, 0, -dist);
    Mat4 modelFull = mul(model, center);
    Mat4 mvp = mul(proj, mul(view, modelFull));

    glUseProgram(program_);
    glUniformMatrix4fv(locMvp_, 1, GL_FALSE, mvp.m);
    glUniformMatrix4fv(locModel_, 1, GL_FALSE, model.m);
    glBindVertexArray(vao_);
    glDrawElements(GL_TRIANGLES, indexCount_, GL_UNSIGNED_INT, nullptr);
    glBindVertexArray(0);
    drawCalls_ = 1;
}

void GlRenderer::shutdown() {
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (ebo_) glDeleteBuffers(1, &ebo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
    if (program_) glDeleteProgram(program_);
    vbo_ = ebo_ = vao_ = program_ = 0;
    indexCount_ = 0;
}

}  // namespace nfsu2
