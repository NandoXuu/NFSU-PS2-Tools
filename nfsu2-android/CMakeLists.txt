cmake_minimum_required(VERSION 3.22)
project(nfsu2 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

option(NFSU2_BUILD_TESTS "Compila os testes unitarios (host)" ON)
# O CMake do Termux tambem define ANDROID; por isso o app usa uma opcao explicita (ligada pelo Gradle).
option(NFSU2_ANDROID_APP "Compila a biblioteca nativa do app Android (GLES/JNI)" OFF)

# Nucleo portavel: sem dependencia de Android/GL, testavel no host.
add_library(nfsu2_core STATIC
    engine/assets/mesh.cpp
    engine/assets/texture.cpp
    engine/audio/wav.cpp)
target_include_directories(nfsu2_core PUBLIC engine)
target_compile_options(nfsu2_core PRIVATE -Wall -Wextra)

if(NFSU2_ANDROID_APP)
    add_library(nfsu2_native SHARED
        engine/graphics/gl_renderer.cpp
        android/app/src/main/cpp/jni_bridge.cpp)
    target_link_libraries(nfsu2_native PRIVATE nfsu2_core GLESv3 EGL android log)
    target_compile_options(nfsu2_native PRIVATE -Wall -Wextra)
endif()

if(NFSU2_BUILD_TESTS AND NOT NFSU2_ANDROID_APP)
    enable_testing()
    add_subdirectory(tests/unit)
endif()
