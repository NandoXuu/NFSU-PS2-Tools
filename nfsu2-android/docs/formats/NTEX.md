# NTEX v1 — textura do motor

Gerado por `convert_assets.py texture` a partir dos PNGs recuperados (TPK → PNG).
Little-endian.

| Offset | Tipo | Campo |
|---|---|---|
| 0 | char[4] | `NTEX` |
| 4 | u32 | versão (=1) |
| 8 | u32 | largura (1..8192) |
| 12 | u32 | altura (1..8192) |
| 16 | u32 | formato de pixel (1 = RGBA8) |
| 20 | u8[w*h*4] | pixels RGBA8, linha de cima primeiro |

O tamanho do arquivo precisa bater exatamente com `20 + w*h*4`.
Compressão de textura (ETC2/ASTC) ainda não implementada.
