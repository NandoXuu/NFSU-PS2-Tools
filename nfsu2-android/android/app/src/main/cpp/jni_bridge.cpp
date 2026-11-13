// Ponte JNI: Kotlin <-> motor C++. Cena de diagnóstico (carrega um veículo e renderiza).
#include <android/log.h>
#include <jni.h>

#include <chrono>
#include <memory>
#include <string>

#include "assets/mesh.h"
#include "core/fixed_timestep.h"
#include "graphics/gl_renderer.h"

#define LOG_TAG "nfsu2"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

namespace {

struct DiagState {
    nfsu2::GlRenderer renderer;
    nfsu2::Mesh mesh;
    nfsu2::FixedTimestep sim{1.0 / 120.0};
    std::string assetDir;
    std::string status = "nao iniciado";
    bool meshOk = false;
    float yaw = 0.6f, pitch = 0.25f, distance = 2.2f;
    float yawVel = 0.0f;
    std::chrono::steady_clock::time_point last;
    bool haveLast = false;
};

std::unique_ptr<DiagState> g;

}  // namespace

extern "C" {

JNIEXPORT void JNICALL Java_dev_nfsu2_NativeBridge_nativeSetAssetDir(JNIEnv* env, jclass, jstring dir) {
    const char* c = env->GetStringUTFChars(dir, nullptr);
    if (!g) g = std::make_unique<DiagState>();
    g->assetDir = c ? c : "";
    env->ReleaseStringUTFChars(dir, c);
}

JNIEXPORT void JNICALL Java_dev_nfsu2_NativeBridge_nativeOnSurfaceCreated(JNIEnv*, jclass) {
    if (!g) g = std::make_unique<DiagState>();
    const char* err = nullptr;
    if (!g->renderer.init(&err)) {
        g->status = std::string("renderer: ") + (err ? err : "erro");
        LOGE("%s", g->status.c_str());
        return;
    }
    const std::string path = g->assetDir + "/diag/car.nmsh";
    std::string merr;
    if (nfsu2::LoadMeshFromFile(path, g->mesh, merr) && g->renderer.uploadMesh(g->mesh)) {
        g->meshOk = true;
        g->status = "ok: " + std::to_string(g->mesh.vertices.size()) + " vertices, " +
                    std::to_string(g->mesh.indices.size() / 3) + " triangulos";
        LOGI("%s", g->status.c_str());
    } else {
        g->meshOk = false;
        g->status = "falha ao carregar " + path + ": " + merr;
        LOGE("%s", g->status.c_str());
    }
}

JNIEXPORT void JNICALL Java_dev_nfsu2_NativeBridge_nativeOnSurfaceChanged(JNIEnv*, jclass, jint w, jint h) {
    if (g) g->renderer.resize(w, h);
}

JNIEXPORT void JNICALL Java_dev_nfsu2_NativeBridge_nativeOnDrawFrame(JNIEnv*, jclass) {
    if (!g) return;
    const auto now = std::chrono::steady_clock::now();
    double dt = 0.0;
    if (g->haveLast) dt = std::chrono::duration<double>(now - g->last).count();
    g->last = now;
    g->haveLast = true;
    const int steps = g->sim.advance(dt);
    for (int i = 0; i < steps; ++i) {
        g->yaw += g->yawVel * float(g->sim.step());
        g->yawVel *= 0.99f;
    }
    g->renderer.draw(g->yaw, g->pitch, g->distance, !g->meshOk);
}

JNIEXPORT void JNICALL Java_dev_nfsu2_NativeBridge_nativeOnDrag(JNIEnv*, jclass, jfloat dx, jfloat dy) {
    if (!g) return;
    g->yaw += dx * 0.01f;
    g->pitch += dy * 0.01f;
    if (g->pitch > 1.4f) g->pitch = 1.4f;
    if (g->pitch < -1.4f) g->pitch = -1.4f;
}

JNIEXPORT jstring JNICALL Java_dev_nfsu2_NativeBridge_nativeStatus(JNIEnv* env, jclass) {
    return env->NewStringUTF(g ? g->status.c_str() : "nao iniciado");
}

}  // extern "C"
