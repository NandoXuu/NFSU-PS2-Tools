# Estado do projeto (honesto)

Atualizado em 2026-11-13. Marcação: ✅ implementado e testado · 🟡 implementado, só compilado/sem teste em dispositivo · ❌ não feito · ⛔ bloqueado por engenharia reversa pendente.

## Pipeline de dados
| Item | Estado | Observação |
|---|---|---|
| Conversor OBJ→NMSH, PNG→NTEX, validação WAV | ✅ | 10 testes Python; rodado com dados reais do 3000GT (74.488 vértices, 44.964 triângulos) |
| Carregadores C++ NMSH / NTEX / WAV | ✅ | 4 testes unitários + teste com assets reais (`NFSU2_REAL_ASSETS`) |
| Passo fixo de simulação + alfa de interpolação | ✅ | independente de FPS (testado a 17/30/60/144) |

## Motor / app
| Item | Estado | Observação |
|---|---|---|
| Renderer GLES 3.0 (malha + luz direcional) | 🟡 | sintaxe checada com stubs; **nunca executado em aparelho** |
| Cena de diagnóstico (carrega `diag/car.nmsh`, gira com toque) | 🟡 | falha de carga → fundo vermelho + mensagem, sem modelo substituto |
| Ponte JNI Kotlin↔C++ | 🟡 | compila no CI (NDK 26); **nunca executada em aparelho** |
| GitHub Actions (host tests + APK arm64-v8a) | ✅ | executado em 2026-11-13: testes passam no runner e o APK debug (~1,1 MB) é publicado como artifact |
| Texturas na malha, sombras, reflexos, LOD, culling | ❌ | texturas dependem de UV (⛔) |
| Áudio (Oboe/AAudio) | ❌ | só o carregador WAV existe |
| UI, garagem, HUD, controles configuráveis, gamepad | ❌ | |
| Streaming de mundo / cenários | ⛔ | formato de setores/cenários ainda não analisado |
| Física veicular | ⛔ | tabelas de física do veículo ainda não localizadas/decodificadas |
| Eventos, progressão, salvamento | ⛔ | |

## Pendências de engenharia reversa (de `tools_v2/README_v2.md`)
- UV do VIF (nem intercalado nem planar suaves).
- Topologia (ADC) para lotes com N ≥ 25 vértices: decodificação parcial.
- Separar as 155 malhas em peças / LODs (via chunks 134011 / 134019).
- Tabelas de chaves 134018/134019.

## Assets
Os assets originais **não** vão para o repositório. O app lê de
`<armazenamento do app>/diag/` (ex.: `/sdcard/Android/data/dev.nfsu2/files/diag/`).
Gere com:

```
python3 tools/asset_converter/convert_assets.py diag \
  --obj <malha.obj> --png <textura.png> --wav <som.wav> --out <pasta>
```

e copie a pasta `diag/` para o aparelho.
