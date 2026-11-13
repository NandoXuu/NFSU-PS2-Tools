# NMSH v1 — malha do motor

Gerado por `tools/asset_converter/convert_assets.py mesh` a partir do OBJ de
`tools_v2/extrair_geometria.py` (GEOMETRY.BIN do PS2). Little-endian.

| Offset | Tipo | Campo |
|---|---|---|
| 0 | char[4] | `NMSH` |
| 4 | u32 | versão (=1) |
| 8 | u32 | nº de vértices |
| 12 | u32 | nº de índices (múltiplo de 3) |
| 16 | u32 | nº de submalhas |
| 20 | u32 | flags (reservado; bit0 = tem UV, **ainda 0**) |
| 24 | f32[6] | AABB: min xyz, max xyz |
| 48 | submalhas | `char name[32]`, `u32 indexOffset`, `u32 indexCount` (cada) |
| … | vértices | `f32 px,py,pz, nx,ny,nz` (24 bytes cada) |
| … | índices | `u32` por índice (lista de triângulos) |

O carregador (`engine/assets/mesh.cpp`) valida: magic, versão, tamanhos antes de
alocar, índices dentro do intervalo, submalhas dentro do buffer e vértices finitos.

## O que NÃO está no formato (e por quê)
- **UV**: a decodificação de UV do VIF ainda não foi resolvida (`tools_v2/README_v2.md`).
- **Cor por vértice** (RGBA8, confirmada): não exportada ainda.
- **Topologia**: os triângulos vêm da hipótese ADC/strip (validada só estatisticamente).
