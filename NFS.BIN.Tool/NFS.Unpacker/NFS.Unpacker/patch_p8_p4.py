from pathlib import Path
import shutil

path = Path("TpkExtractor.cs")
s = path.read_text()

def replace_once(old, new, label):
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(
            f"{label}: esperado 1 trecho, encontrado {count}. "
            "Arquivo não foi alterado."
        )
    s = s.replace(old, new, 1)
    print("[OK]", label)

# 0x80 utiliza o mesmo caminho de conversão P8.
replace_once(
    "byte compression = t.Compression == 0x81 ? (byte)0x08 : t.Compression;",
    """byte compression = (t.Compression == 0x80 || t.Compression == 0x81)
            ? (byte)0x08 : t.Compression;""",
    "Reconhecimento P8"
)

# Conversor P4: paleta de 16 cores e índices de 4 bits.
replace_once(
    "            case 0x08: // P8_08: palette (0x400 bytes) followed by 8-bit indices",
    """            case 0x04: // P4: paleta de 16 cores e índices de 4 bits
                int pixelCount = checked(t.Width * t.Height);
                int packedSize = (pixelCount + 1) / 2;

                if (t.PaletteSize < 64 ||
                    raw.Length < t.PaletteSize + packedSize)
                    return false;

                byte[] palette4 = raw.AsSpan(0, t.PaletteSize).ToArray();
                imageData = new byte[checked(pixelCount * 4)];

                for (int i = 0; i < pixelCount; i++)
                {
                    byte packed = raw[t.PaletteSize + (i / 2)];

                    // Hipótese inicial: nibble menos significativo primeiro.
                    int paletteIndex = (i & 1) == 0
                        ? packed & 0x0F
                        : packed >> 4;

                    int src = paletteIndex * 4;
                    int dst = i * 4;

                    if (src + 4 > palette4.Length)
                        return false;

                    Buffer.BlockCopy(palette4, src, imageData, dst, 4);
                }

                pfFlags = 0x41;
                rgbBits = 32;
                rMask = 0x00FF0000;
                gMask = 0x0000FF00;
                bMask = 0x000000FF;
                aMask = 0xFF000000;
                pitchOrLinear = (uint)t.Width * 4;
                break;

            case 0x08: // P8: palette followed by 8-bit indices""",
    "Adicionar conversor P4"
)

# DDS de P4 também utiliza pitch em vez de linear size.
replace_once(
    "(compression == 0x20 || compression == 0x08) ? 0x8u : 0x80000u;",
    "(compression == 0x20 || compression == 0x08 || compression == 0x04) ? 0x8u : 0x80000u;",
    "Corrigir flags DDS"
)

replace_once(
    "        0x08 or 0x81 => \"P8\",",
    """        0x08 or 0x80 or 0x81 => "P8",
        0x04 => "P4",""",
    "Atualizar nomes dos formatos"
)

backup = path.with_name("TpkExtractor.cs.before_p8_p4")
shutil.copy2(path, backup)
path.write_text(s)

print("\\nPatch aplicado com sucesso.")
print("Backup:", backup)
