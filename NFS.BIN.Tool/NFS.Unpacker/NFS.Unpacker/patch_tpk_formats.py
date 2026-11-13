from pathlib import Path
import shutil

p = Path("TpkExtractor.cs")
s = p.read_text()

def replace(old, new, name):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"{name}: esperado 1 trecho, encontrado {n}.")
    s = s.replace(old, new, 1)
    print("[OK]", name)

# Passar INFO_PART4 para o construtor do buffer global.
replace(
    "DecompressTextureBlocks(file, p3, dataPart + 8, dataPartEnd)",
    "DecompressTextureBlocks(file, p3, p4, dataPart + 8, dataPartEnd)",
    "Passar INFO_PART4"
)

replace(
'''    private static byte[] DecompressTextureBlocks(
        byte[] file, int p3, int dataStart, int dataEnd)
''',
'''    private static byte[] DecompressTextureBlocks(
        byte[] file, int p3, int p4, int dataStart, int dataEnd)
''',
    "Atualizar assinatura"
)

# Localizar o offset lógico da textura através da key.
replace(
'''        using var output = new MemoryStream();

        int count = size / 24;

        for (int i = 0; i < count; i++)
''',
'''        int headerSize = ReadSize(file, p4);
        if (headerSize % 0x7C != 0)
            throw new InvalidDataException("INFO_PART4 inválido.");

        using var output = new MemoryStream();

        int count = size / 24;

        for (int i = 0; i < count; i++)
''',
    "Validar INFO_PART4"
)

replace(
'''            var block = new CompressionBlock(
                key, offset, encoded, decoded, headerEnd, unknown);

            byte[] result = DecompressTextureBlock(file, block);

            if (result.Length != decoded)
                throw new InvalidDataException(
                    $"Tamanho divergente no bloco {i}.");

            output.Write(result, 0, result.Length);
''',
'''            int targetOffset = -1;

            for (int j = 0; j < headerSize / 0x7C; j++)
            {
                int h = p4 + 8 + j * 0x7C;

                if (U32(file, h + 0x24) == key)
                {
                    targetOffset = I32(file, h + 0x30);
                    break;
                }
            }

            if (targetOffset < 0)
                throw new InvalidDataException(
                    $"Cabeçalho não encontrado para key 0x{key:X8}.");

            if (targetOffset < output.Length)
                throw new InvalidDataException(
                    $"Offset sobreposto para key 0x{key:X8}.");

            int gap = checked(targetOffset - (int)output.Length);

            if (gap > 1024 * 1024)
                throw new InvalidDataException(
                    $"Padding excessivo antes da key 0x{key:X8}: {gap}.");

            if (gap > 0)
            {
                Console.WriteLine(
                    $"Padding lógico: 0x{gap:X} bytes antes da key 0x{key:X8}.");

                output.Write(new byte[gap], 0, gap);
            }

            var block = new CompressionBlock(
                key, offset, encoded, decoded, headerEnd, unknown);

            byte[] result = DecompressTextureBlock(file, block);

            if (result.Length != decoded)
                throw new InvalidDataException(
                    $"Tamanho divergente no bloco {i}.");

            output.Write(result, 0, result.Length);
''',
    "Inserir padding conforme os offsets reais"
)

# Reconhecer 0x80 como candidato a P8.
replace(
'''        byte compression = t.Compression == 0x81 ? (byte)0x08 : t.Compression;
''',
'''        byte compression = t.Compression == 0x80 || t.Compression == 0x81
            ? (byte)0x08 : t.Compression;
''',
    "Mapear 0x80 para P8"
)

# Adicionar conversão P4.
replace(
'''            case 0x08: // P8_08: palette (0x400 bytes) followed by 8-bit indices
''',
'''            case 0x04: // P4: 16 cores, 4 bits por pixel
                int pixelCount = checked(t.Width * t.Height);
                int packedSize = (pixelCount + 1) / 2;

                if (t.PaletteSize < 64 ||
                    raw.Length < t.PaletteSize + packedSize)
                    return false;

                byte[] palette4 = raw.AsSpan(0, t.PaletteSize).ToArray();
                byte[] indices4 = raw.AsSpan(t.PaletteSize, packedSize).ToArray();

                imageData = new byte[checked(pixelCount * 4)];

                for (int i = 0; i < pixelCount; i++)
                {
                    byte packed = indices4[i / 2];

                    // Hipótese inicial: nibble baixo primeiro.
                    int paletteIndex = (i & 1) == 0
                        ? packed & 0x0F
                        : packed >> 4;

                    int src = paletteIndex * 4;
                    int dst = i * 4;

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

            case 0x08: // P8_08: palette followed by 8-bit indices
''',
    "Adicionar conversão P4"
)

replace(
'''        0x08 or 0x81 => "P8",
''',
'''        0x08 or 0x80 or 0x81 => "P8",
        0x04 => "P4",
''',
    "Atualizar nomes dos formatos"
)

backup = Path("TpkExtractor.cs.before_formats")
shutil.copy2(p, backup)
p.write_text(s)

print("\\nPatch aplicado. Backup:", backup)
