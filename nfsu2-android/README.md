# NFSU2 Android (reconstrução nativa — em andamento)

Motor C++17 (NDK/CMake) + Kotlin/JNI, alimentado pelos dados recuperados em
`../recovery`, `../Sons_Recuperados` e `../tools_v2`. Estado real: veja `docs/STATUS.md`.

## Layout
- `engine/core, assets, audio, graphics` — núcleo portátil (testável no host) e renderer GLES
- `android/` — projeto Gradle (app de diagnóstico)
- `tools/asset_converter/` — OBJ/PNG/WAV → NMSH/NTEX/WAV
- `tests/unit` (C++), `tests/tools` (Python)
- `docs/formats` — especificação dos formatos

## Rodar os testes (host / Termux)
```
cmake -S . -B ~/nfsu2-build -G "Unix Makefiles" && cmake --build ~/nfsu2-build -j8
ctest --test-dir ~/nfsu2-build --output-on-failure
python3 -m unittest discover -s tests/tools -v
```
Para validar assets reais: `NFSU2_REAL_ASSETS=<pasta> ctest -R real_assets`.

## APK
Gerado pelo workflow `.github/workflows/nfsu2-android.yml` (artifact `nfsu2-diag-arm64-v8a-debug`).
