from pathlib import Path
import shutil

p = Path("TpkExtractor.cs")
s = p.read_text()

def replace_once(old, new, description):
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError(
            f"{description}: esperado 1 trecho, encontrado {count}. "
            "Nenhuma alteração final será salva."
        )
    s = s.replace(old, new, 1)
    print("[OK]", description)

# 1. Importar P/Invoke.
replace_once(
    "using System.Text.Json;\n",
    "using System.Text.Json;\nusing System.Runtime.InteropServices;\n",
    "Importar Runtime.InteropServices"
)

# 2. Identificador INFO_PART3.
replace_once(
    "    private const uint InfoPart2 = 0x33310002;\n",
    "    private const uint InfoPart2 = 0x33310002;\n"
    "    private const uint InfoPart3 = 0x33310003;\n",
    "Adicionar INFO_PART3"
)

# 3. Registro dos blocos comprimidos.
replace_once(
    "    private sealed record TextureInfo(\n"
    "        int Index, string Name, uint BinKey, int Width, int Height,\n"
    "        int Offset, int PaletteOffset, int Size, int PaletteSize,\n"
    "        byte Compression, byte Mipmaps, byte PaletteCompression);\n",
    "    private sealed record TextureInfo(\n"
    "        int Index, string Name, uint BinKey, int Width, int Height,\n"
    "        int Offset, int PaletteOffset, int Size, int PaletteSize,\n"
    "        byte Compression, byte Mipmaps, byte PaletteCompression);\n\n"
    "    private sealed record CompressionBlock(\n"
    "        uint Key, int Offset, int Encoded, int Decoded,\n"
    "        int HeaderEnd, int Unknown);\n\n"
    "    private const string NativeLibraryName = \"ea_compression\";\n\n"
    "    [DllImport(NativeLibraryName, EntryPoint = \"ea_get_decompressed_size\",\n"
    "        CallingConvention = CallingConvention.Cdecl)]\n"
    "    private static extern int EaGetDecompressedSize(byte[] data, int size);\n\n"
    "    [DllImport(NativeLibraryName, EntryPoint = \"ea_decompress\",\n"
    "        CallingConvention = CallingConvention.Cdecl)]\n"
    "    private static extern int EaDecompress(\n"
    "        byte[] compressed, int compressedSize,\n"
    "        [Out] byte[] decompressed, int decompressedSize);\n",
    "Adicionar estrutura e funções nativas"
)

# 4. DATA_PART2: manter seus limites reais.
replace_once(
    "            int dataBase = checked(dataPart + 0x80);\n"
    "            if (dataBase > dataEnd)\n"
    "            {\n"
    "                report.Add(new { block = blockIndex, status = \"DATA_PART2 menor que 0x80 bytes\" });\n"
    "                failed++;\n"
    "                continue;\n"
    "            }\n",
    "            int dataPartEnd = CheckedBlockEnd(file, dataPart);\n",
    "Corrigir limite de DATA_PART2"
)

# 5. Localizar INFO_PART3.
replace_once(
    "            int p2 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart2);\n"
    "            int p4 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart4);\n",
    "            int p2 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart2);\n"
    "            int p3 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart3);\n"
    "            int p4 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart4);\n",
    "Localizar INFO_PART3"
)

replace_once(
    "            if (p2 < 0 || p4 < 0)\n"
    "            {\n"
    "                report.Add(new { block = blockIndex, collection, status = \"INFO_PART2 ou INFO_PART4 ausente\" });\n",
    "            if (p2 < 0 || p3 < 0 || p4 < 0)\n"
    "            {\n"
    "                report.Add(new { block = blockIndex, collection, status = \"INFO_PART2, INFO_PART3 ou INFO_PART4 ausente\" });\n",
    "Validar INFO_PART3"
)

replace_once(
    "            int p2Size = ReadSize(file, p2);\n"
    "            int p4Size = ReadSize(file, p4);\n"
    "            if (p2Size % 8 != 0 || p4Size % 0x7C != 0)\n",
    "            int p2Size = ReadSize(file, p2);\n"
    "            int p3Size = ReadSize(file, p3);\n"
    "            int p4Size = ReadSize(file, p4);\n"
    "            if (p2Size % 8 != 0 || p3Size % 24 != 0 || p4Size % 0x7C != 0)\n",
    "Validar tamanhos das tabelas"
)

replace_once(
    "            int keyCount = p2Size / 8;\n"
    "            int headerCount = p4Size / 0x7C;\n"
    "            int count = Math.Min(keyCount, headerCount);\n",
    "            int keyCount = p2Size / 8;\n"
    "            int compressionCount = p3Size / 24;\n"
    "            int headerCount = p4Size / 0x7C;\n"
    "            int count = Math.Min(keyCount, headerCount);\n"
    "            var compressionBlocks = ReadCompressionBlocks(\n"
    "                file, p3, dataPart + 8, dataPartEnd);\n",
    "Ler os registros de compressão"
)

# 6. Trocar a leitura direta por descompressão.
replace_once(
    "                    ValidateTexture(t, dataBase, dataEnd);\n"
    "                    byte[] payload = ReadTexturePayload(file, t, dataBase, dataEnd);\n"
    "                    string format = CompressionName(t.Compression);\n",
    "                    if (!compressionBlocks.TryGetValue(t.BinKey, out var compressedBlock))\n"
    "                        throw new InvalidDataException($\"Bloco comprimido não encontrado para a key 0x{t.BinKey:X8}.\");\n\n"
    "                    byte[] decoded = DecompressTextureBlock(file, compressedBlock);\n"
    "                    ValidateTexture(t, decoded.Length);\n"
    "                    byte[] payload = ReadTexturePayload(decoded, t);\n"
    "                    string format = CompressionName(t.Compression);\n",
    "Integrar descompressão por chave"
)

# 7. Substituir leitura antiga do payload.
old_payload = '''    private static byte[] ReadTexturePayload(byte[] file, TextureInfo t, int dataBase, int dataEnd)
    {
        // No parser UG1 do GlobalLib, ReadData recebe DATA_PART2 + 0x80
        // como base. Os offsets do cabeçalho são relativos a essa base.
        byte[] pixels = Slice(file, checked(dataBase + t.Offset), t.Size, dataEnd);

        if (t.PaletteSize <= 0)
            return pixels;

        int paletteOffset = t.PaletteOffset;
        byte[] palette = Slice(file, checked(dataBase + paletteOffset), t.PaletteSize, dataEnd);
        byte[] combined = new byte[checked(palette.Length + pixels.Length)];
        Buffer.BlockCopy(palette, 0, combined, 0, palette.Length);
        Buffer.BlockCopy(pixels, 0, combined, palette.Length, pixels.Length);
        return combined;
    }
'''

new_payload = '''    private static Dictionary<uint, CompressionBlock> ReadCompressionBlocks(
        byte[] file, int p3, int dataStart, int dataEnd)
    {
        int size = ReadSize(file, p3);
        if (size % 24 != 0)
            throw new InvalidDataException("INFO_PART3 possui tamanho inválido.");

        var result = new Dictionary<uint, CompressionBlock>();

        for (int i = 0; i < size / 24; i++)
        {
            int p = p3 + 8 + i * 24;

            uint key = U32(file, p);
            int offset = I32(file, p + 4);
            int encoded = I32(file, p + 8);
            int decoded = I32(file, p + 12);
            int headerEnd = I32(file, p + 16);
            int unknown = I32(file, p + 20);

            if (offset < dataStart || encoded <= 0 || decoded <= 0 ||
                (long)offset + encoded > dataEnd)
                throw new InvalidDataException(
                    $"Bloco comprimido inválido para key 0x{key:X8}.");

            var item = new CompressionBlock(
                key, offset, encoded, decoded, headerEnd, unknown);

            if (!result.TryAdd(key, item))
                throw new InvalidDataException(
                    $"Key duplicada em INFO_PART3: 0x{key:X8}.");
        }

        return result;
    }

    private static byte[] DecompressTextureBlock(
        byte[] file, CompressionBlock block)
    {
        byte[] compressed = Slice(
            file, block.Offset, block.Encoded, file.Length);

        int reportedSize = EaGetDecompressedSize(
            compressed, compressed.Length);

        if (reportedSize != block.Decoded)
            throw new InvalidDataException(
                $"Tamanho nativo divergente para 0x{block.Key:X8}: " +
                $"INFO_PART3={block.Decoded}, biblioteca={reportedSize}.");

        byte[] output = new byte[block.Decoded];

        int written = EaDecompress(
            compressed, compressed.Length, output, output.Length);

        if (written != block.Decoded)
            throw new InvalidDataException(
                $"Falha na descompressão de 0x{block.Key:X8}: retorno {written}.");

        return output;
    }

    private static byte[] ReadTexturePayload(byte[] decoded, TextureInfo t)
    {
        byte[] pixels = Slice(decoded, t.Offset, t.Size, decoded.Length);

        if (t.PaletteSize <= 0)
            return pixels;

        byte[] palette = Slice(
            decoded, t.PaletteOffset, t.PaletteSize, decoded.Length);

        byte[] combined = new byte[checked(palette.Length + pixels.Length)];
        Buffer.BlockCopy(palette, 0, combined, 0, palette.Length);
        Buffer.BlockCopy(pixels, 0, combined, palette.Length, pixels.Length);
        return combined;
    }
'''

replace_once(old_payload, new_payload, "Adicionar parser e descompressor")

# 8. Validar offsets no buffer descomprimido, não no arquivo original.
old_validate = '''    private static void ValidateTexture(TextureInfo t, int dataBase, int dataEnd)
    {
        if (t.Width <= 0 || t.Height <= 0 || t.Width > 16384 || t.Height > 16384)
            throw new InvalidDataException("Dimensões inválidas.");
        if (t.Offset < 0 || t.Size < 0 || t.PaletteOffset < 0 || t.PaletteSize < 0)
            throw new InvalidDataException("Offset/tamanho negativo.");
        if (t.Size > 256 * 1024 * 1024 || t.PaletteSize > 16 * 1024 * 1024)
            throw new InvalidDataException("Tamanho excede o limite de segurança.");
        CheckRange((long)dataBase + t.Offset, t.Size, dataEnd);
        if (t.PaletteSize > 0)
            CheckRange((long)dataBase + t.PaletteOffset, t.PaletteSize, dataEnd);
    }
'''

new_validate = '''    private static void ValidateTexture(TextureInfo t, int decodedLength)
    {
        if (t.Width <= 0 || t.Height <= 0 || t.Width > 16384 || t.Height > 16384)
            throw new InvalidDataException("Dimensões inválidas.");
        if (t.Offset < 0 || t.Size < 0 || t.PaletteOffset < 0 || t.PaletteSize < 0)
            throw new InvalidDataException("Offset/tamanho negativo.");
        if (t.Size > 256 * 1024 * 1024 || t.PaletteSize > 16 * 1024 * 1024)
            throw new InvalidDataException("Tamanho excede o limite de segurança.");

        CheckRange(t.Offset, t.Size, decodedLength);
        if (t.PaletteSize > 0)
            CheckRange(t.PaletteOffset, t.PaletteSize, decodedLength);
    }
'''

replace_once(old_validate, new_validate, "Validar offsets no buffer descomprimido")

# Backup e gravação somente depois de todas as verificações.
backup = Path("TpkExtractor.cs.before_native")
shutil.copy2(p, backup)
p.write_text(s)

print("\nIntegração aplicada.")
print("Backup:", backup)
