// TpkExtractor.cs — .NET 8, sem dependências externas.
// Uso a partir do programa existente:
// TpkExtractor.Extract(args[1], args[2]);

using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Runtime.InteropServices;

public static class TpkExtractor
{
    private const uint InfoBlock = 0xB3310000;
    private const uint DataBlock = 0xB3320000;
    private const uint InfoPart1 = 0x33310001;
    private const uint InfoPart2 = 0x33310002;
    private const uint InfoPart3 = 0x33310003;
    private const uint InfoPart4 = 0x33310004;
    private const uint InfoPart5 = 0x33310005;
    private const uint DataPart2 = 0x33320002;

    private sealed record TextureInfo(
        int Index, string Name, uint BinKey, int Width, int Height,
        int Offset, int PaletteOffset, int Size, int PaletteSize,
        byte Compression, byte Mipmaps, byte PaletteCompression);

    private sealed record CompressionBlock(
        uint Key, int Offset, int Encoded, int Decoded,
        int HeaderEnd, int Unknown);

    private const string NativeLibraryName = "ea_compression";

    [DllImport(NativeLibraryName, EntryPoint = "ea_get_decompressed_size",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern int EaGetDecompressedSize(byte[] data, int size);

    [DllImport(NativeLibraryName, EntryPoint = "ea_decompress",
        CallingConvention = CallingConvention.Cdecl)]
    private static extern int EaDecompress(
        byte[] compressed, int compressedSize,
        [Out] byte[] decompressed, int decompressedSize);

    public static void Extract(string inputPath, string outputDirectory)
    {
        if (!File.Exists(inputPath))
            throw new FileNotFoundException("Arquivo TPK não encontrado.", inputPath);

        byte[] file = File.ReadAllBytes(inputPath);
        Directory.CreateDirectory(outputDirectory);

        var infoBlocks = FindBlocks(file, InfoBlock);
        if (infoBlocks.Count == 0)
            throw new InvalidDataException("Nenhum INFO_BLOCK TPK válido foi encontrado.");

        int extracted = 0;
        int failed = 0;
        var report = new List<object>();

        for (int blockIndex = 0; blockIndex < infoBlocks.Count; blockIndex++)
        {
            int infoAt = infoBlocks[blockIndex];
            int infoEnd = CheckedBlockEnd(file, infoAt);
            int nextInfo = blockIndex + 1 < infoBlocks.Count ? infoBlocks[blockIndex + 1] : file.Length;

            int dataAt = FindBlockInRange(file, DataBlock, infoEnd, nextInfo);
            if (dataAt < 0)
            {
                // Alguns arquivos encapsulam INFO e DATA em um contêiner maior.
                dataAt = FindBlockInRange(file, DataBlock, infoEnd, file.Length);
            }
            if (dataAt < 0)
            {
                report.Add(new { block = blockIndex, status = "DATA_BLOCK ausente" });
                failed++;
                continue;
            }

            int dataEnd = CheckedBlockEnd(file, dataAt);
            int dataPart = FindSubBlock(file, dataAt + 8, dataEnd, DataPart2);
            if (dataPart < 0)
            {
                report.Add(new { block = blockIndex, status = "DATA_PART2 ausente" });
                failed++;
                continue;
            }

            int dataPartEnd = CheckedBlockEnd(file, dataPart);

            int p1 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart1);
            int p2 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart2);
            int p3 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart3);
            int p4 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart4);
            int p5 = FindSubBlock(file, infoAt + 8, infoEnd, InfoPart5);

            string collection = p1 >= 0
                ? ReadCString(file, p1 + 12, 0x1C)
                : $"TPK_{blockIndex:D3}";

            if (p2 < 0 || p3 < 0 || p4 < 0)
            {
                report.Add(new { block = blockIndex, collection, status = "INFO_PART2, INFO_PART3 ou INFO_PART4 ausente" });
                failed++;
                continue;
            }

            int p2Size = ReadSize(file, p2);
            int p3Size = ReadSize(file, p3);
            int p4Size = ReadSize(file, p4);
            if (p2Size % 8 != 0 || p3Size % 24 != 0 || p4Size % 0x7C != 0)
            {
                report.Add(new { block = blockIndex, collection, status = "Tamanhos de tabela inválidos", p2Size, p4Size });
                failed++;
                continue;
            }

            int keyCount = p2Size / 8;
            int compressionCount = p3Size / 24;
            int headerCount = p4Size / 0x7C;
            int count = Math.Min(keyCount, headerCount);
            byte[] decodedData = DecompressTextureBlocks(
                file, p3, p4, dataPart + 8, dataPartEnd);
            string safeCollection = SafeName(collection);
            string blockDir = Path.Combine(outputDirectory, $"{blockIndex:D3}_{safeCollection}");
            Directory.CreateDirectory(blockDir);

            var textureReport = new List<object>();
            for (int i = 0; i < count; i++)
            {
                int h = p4 + 8 + i * 0x7C;
                var t = new TextureInfo(
                    i,
                    ReadCString(file, h + 0x0C, 0x18),
                    U32(file, h + 0x24),
                    I16(file, h + 0x44),
                    I16(file, h + 0x46),
                    I32(file, h + 0x30),
                    I32(file, h + 0x34),
                    I32(file, h + 0x38),
                    I32(file, h + 0x3C),
                    file[h + 0x4A],
                    file[h + 0x4E],
                    file[h + 0x4B]);

                string baseName = string.IsNullOrWhiteSpace(t.Name) ? $"texture_{i:D4}" : SafeName(t.Name);
                string uniqueName = $"{i:D4}_{baseName}";
                string status;

                try
                {
                    ValidateTexture(t, decodedData.Length);
                    byte[] payload = ReadTexturePayload(decodedData, t);
                    string format = CompressionName(t.Compression);

                    string rawPath = Path.Combine(blockDir, uniqueName + ".raw");
                    File.WriteAllBytes(rawPath, payload);

                    string ddsPath = Path.Combine(blockDir, uniqueName + ".dds");
                    if (TryBuildDds(t, payload, out byte[] dds))
                    {
                        File.WriteAllBytes(ddsPath, dds);
                        status = "DDS + RAW";
                    }
                    else
                    {
                        status = "RAW (formato não convertido)";
                    }

                    textureReport.Add(new
                    {
                        t.Index, t.Name, binKey = $"0x{t.BinKey:X8}",
                        t.Width, t.Height, compression = format,
                        t.Mipmaps, t.Offset, t.PaletteOffset, t.Size, t.PaletteSize,
                        status
                    });
                    extracted++;
                }
                catch (Exception ex)
                {
                    textureReport.Add(new
                    {
                        t.Index, t.Name, t.Width, t.Height,
                        compression = CompressionName(t.Compression),
                        status = "ERRO", error = ex.Message
                    });
                    failed++;
                }
            }

            string metadataPath = Path.Combine(blockDir, "textures.json");
            File.WriteAllText(metadataPath,
                JsonSerializer.Serialize(new { collection, textureCount = count, textures = textureReport },
                    new JsonSerializerOptions { WriteIndented = true }));

            report.Add(new { block = blockIndex, collection, textureCount = count, directory = blockDir });
        }

        File.WriteAllText(Path.Combine(outputDirectory, "report.json"),
            JsonSerializer.Serialize(new { input = inputPath, extracted, failed, blocks = report },
                new JsonSerializerOptions { WriteIndented = true }));

        Console.WriteLine($"TPK concluído: {extracted} textura(s) extraída(s), {failed} ocorrência(s) com falha.");
        Console.WriteLine($"Relatório: {Path.Combine(outputDirectory, "report.json")}");
    }

    private static Dictionary<uint, CompressionBlock> ReadCompressionBlocks(
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

    private static byte[] DecompressTextureBlocks(
        byte[] file, int p3, int p4, int dataStart, int dataEnd)
    {
        int size = ReadSize(file, p3);
        int headerSize = ReadSize(file, p4);

        if (size % 24 != 0)
            throw new InvalidDataException("INFO_PART3 possui tamanho inválido.");

        if (headerSize % 0x7C != 0)
            throw new InvalidDataException("INFO_PART4 possui tamanho inválido.");

        // Associa cada key do INFO_PART4 ao offset lógico da textura.
        var textureOffsets = new Dictionary<uint, int>();

        int headerCount = headerSize / 0x7C;

        for (int i = 0; i < headerCount; i++)
        {
            int h = p4 + 8 + i * 0x7C;

            uint key = U32(file, h + 0x24);
            int targetOffset = I32(file, h + 0x30);

            if (targetOffset < 0)
                throw new InvalidDataException(
                    $"Offset negativo no INFO_PART4: key 0x{key:X8}.");

            if (!textureOffsets.TryAdd(key, targetOffset))
                throw new InvalidDataException(
                    $"Key duplicada no INFO_PART4: 0x{key:X8}.");
        }

        using var output = new MemoryStream();

        int count = size / 24;

        for (int i = 0; i < count; i++)
        {
            int p = p3 + 8 + i * 24;

            uint key = U32(file, p);
            int offset = I32(file, p + 4);
            int encoded = I32(file, p + 8);
            int decoded = I32(file, p + 12);
            int headerEnd = I32(file, p + 16);
            int unknown = I32(file, p + 20);

            if (offset < dataStart || encoded <= 0 ||
                decoded <= 0 || (long)offset + encoded > dataEnd)
            {
                throw new InvalidDataException(
                    $"Bloco inválido na posição {i}, key 0x{key:X8}.");
            }

            if (!textureOffsets.TryGetValue(key, out int targetOffset))
                throw new InvalidDataException(
                    $"Key 0x{key:X8} não encontrada no INFO_PART4.");

            if (targetOffset < output.Length)
                throw new InvalidDataException(
                    $"Offset sobreposto para key 0x{key:X8}: " +
                    $"cabeçalho=0x{targetOffset:X}, buffer=0x{output.Length:X}.");

            int gap = checked(targetOffset - (int)output.Length);

            if (gap > 1024 * 1024)
                throw new InvalidDataException(
                    $"Padding excessivo antes da key 0x{key:X8}: 0x{gap:X}.");

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
        }

        Console.WriteLine(
            $"Buffer global TPK: {output.Length} bytes, {count} blocos.");

        return output.ToArray();
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

    private static bool TryBuildDds(TextureInfo t, byte[] raw, out byte[] dds)
    {
        dds = Array.Empty<byte>();
        if (t.Width <= 0 || t.Height <= 0 || t.Width > 16384 || t.Height > 16384)
            return false;

        byte compression = (t.Compression == 0x80 || t.Compression == 0x81)
            ? (byte)0x08 : t.Compression;
        byte[] imageData;
        uint pfFlags, fourCC = 0, rgbBits = 0;
        uint rMask = 0, gMask = 0, bMask = 0, aMask = 0;
        uint pitchOrLinear;

        switch (compression)
        {
            case 0x22: // DXT1
                pfFlags = 0x4; fourCC = FourCc("DXT1");
                imageData = raw;
                pitchOrLinear = (uint)(Math.Max(1, (t.Width + 3) / 4) *
                                       Math.Max(1, (t.Height + 3) / 4) * 8);
                break;
            case 0x24: // DXT3
                pfFlags = 0x4; fourCC = FourCc("DXT3");
                imageData = raw;
                pitchOrLinear = (uint)(Math.Max(1, (t.Width + 3) / 4) *
                                       Math.Max(1, (t.Height + 3) / 4) * 16);
                break;
            case 0x26: // DXT5
                pfFlags = 0x4; fourCC = FourCc("DXT5");
                imageData = raw;
                pitchOrLinear = (uint)(Math.Max(1, (t.Width + 3) / 4) *
                                       Math.Max(1, (t.Height + 3) / 4) * 16);
                break;
            case 0x20: // RGBA_08
                pfFlags = 0x41; rgbBits = 32;
                rMask = 0x00FF0000; gMask = 0x0000FF00;
                bMask = 0x000000FF; aMask = 0xFF000000;
                imageData = raw;
                pitchOrLinear = (uint)t.Width * 4;
                break;
            case 0x04: // P4: paleta de 16 cores e índices de 4 bits
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

            case 0x08: // P8: palette followed by 8-bit indices
                if (raw.Length < 0x400) return false;
                byte[] palette = raw.AsSpan(0, 0x400).ToArray();
                byte[] indices = raw.AsSpan(0x400).ToArray();
                imageData = new byte[checked(indices.Length * 4)];
                for (int i = 0; i < indices.Length; i++)
                {
                    int p = indices[i] * 4;
                    Buffer.BlockCopy(palette, p, imageData, i * 4, 4);
                }
                pfFlags = 0x41; rgbBits = 32;
                rMask = 0x00FF0000; gMask = 0x0000FF00;
                bMask = 0x000000FF; aMask = 0xFF000000;
                pitchOrLinear = (uint)t.Width * 4;
                break;
            default:
                return false;
        }

        dds = new byte[checked(0x80 + imageData.Length)];
        WriteU32(dds, 0x00, FourCc("DDS "));
        WriteU32(dds, 0x04, 0x7C);
        uint ddsFlags = 0x00001007 | 0x00020000; // CAPS | HEIGHT | WIDTH | PIXELFORMAT | MIPMAPCOUNT
        ddsFlags |= (compression == 0x20 || compression == 0x08 || compression == 0x04) ? 0x8u : 0x80000u;
        WriteU32(dds, 0x08, ddsFlags);
        WriteU32(dds, 0x0C, (uint)t.Height);
        WriteU32(dds, 0x10, (uint)t.Width);
        WriteU32(dds, 0x14, pitchOrLinear);
        WriteU32(dds, 0x1C, Math.Max(1u, t.Mipmaps));
        WriteU32(dds, 0x4C, 0x20); // DDS_PIXELFORMAT size
        WriteU32(dds, 0x50, pfFlags);
        WriteU32(dds, 0x54, fourCC);
        WriteU32(dds, 0x58, rgbBits);
        WriteU32(dds, 0x5C, rMask);
        WriteU32(dds, 0x60, gMask);
        WriteU32(dds, 0x64, bMask);
        WriteU32(dds, 0x68, aMask);
        WriteU32(dds, 0x6C, 0x00401008); // TEXTURE | COMPLEX | MIPMAP
        Buffer.BlockCopy(imageData, 0, dds, 0x80, imageData.Length);
        return true;
    }

    private static void ValidateTexture(TextureInfo t, int decodedLength)
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

    private static List<int> FindBlocks(byte[] b, uint id)
    {
        var result = new List<int>();
        for (int i = 0; i <= b.Length - 8; i += 4)
        {
            if (U32(b, i) != id) continue;
            int size = I32(b, i + 4);
            if (size < 0 || (long)i + 8 + size > b.Length) continue;
            result.Add(i);
        }
        return result;
    }

    private static int FindBlockInRange(byte[] b, uint id, int start, int end)
    {
        start = Math.Max(0, start);
        end = Math.Min(b.Length, end);
        for (int i = (start + 3) & ~3; i <= end - 8; i += 4)
            if (U32(b, i) == id && I32(b, i + 4) >= 0 &&
                (long)i + 8 + I32(b, i + 4) <= end)
                return i;
        return -1;
    }

    private static int FindSubBlock(byte[] b, int start, int end, uint id)
    {
        for (int p = start; p <= end - 8;)
        {
            uint found = U32(b, p);
            int size = I32(b, p + 4);
            if (size < 0 || (long)p + 8 + size > end) break;
            if (found == id) return p;
            p += 8 + size;
        }
        return -1;
    }

    private static int CheckedBlockEnd(byte[] b, int at)
    {
        int size = ReadSize(b, at);
        long end = (long)at + 8 + size;
        if (size < 0 || end > b.Length) throw new InvalidDataException("Bloco com tamanho inválido.");
        return (int)end;
    }

    private static int ReadSize(byte[] b, int at)
    {
        if (at < 0 || at > b.Length - 8) throw new InvalidDataException("Cabeçalho de bloco truncado.");
        return I32(b, at + 4);
    }

    private static byte[] Slice(byte[] b, int at, int size, int limit)
    {
        CheckRange(at, size, Math.Min(limit, b.Length));
        return b.AsSpan(at, size).ToArray();
    }

    private static void CheckRange(long at, int size, int limit)
    {
        if (at < 0 || size < 0 || at + size > limit)
            throw new InvalidDataException($"Dados fora do bloco: offset=0x{at:X}, size=0x{size:X}, limite=0x{limit:X}.");
    }

    private static string ReadCString(byte[] b, int at, int max)
    {
        if (at < 0 || at >= b.Length) return "";
        int len = 0;
        while (len < max && at + len < b.Length && b[at + len] != 0) len++;
        return Encoding.ASCII.GetString(b, at, len).Trim();
    }

    private static string SafeName(string value)
    {
        if (string.IsNullOrWhiteSpace(value)) return "unnamed";
        foreach (char c in Path.GetInvalidFileNameChars())
            value = value.Replace(c, '_');
        value = value.Replace('/', '_').Replace('\\', '_').Trim();
        return value.Length > 100 ? value[..100] : value;
    }

    private static string CompressionName(byte c) => c switch
    {
        0x08 or 0x80 or 0x81 => "P8",
        0x04 => "P4",
        0x20 => "RGBA",
        0x22 => "DXT1",
        0x24 => "DXT3",
        0x26 => "DXT5",
        _ => $"UNKNOWN_0x{c:X2}"
    };

    private static uint FourCc(string s) =>
        (uint)s[0] | ((uint)s[1] << 8) | ((uint)s[2] << 16) | ((uint)s[3] << 24);

    private static ushort U16(byte[] b, int p) => BinaryPrimitives.ReadUInt16LittleEndian(b.AsSpan(p, 2));
    private static short I16(byte[] b, int p) => BinaryPrimitives.ReadInt16LittleEndian(b.AsSpan(p, 2));
    private static uint U32(byte[] b, int p) => BinaryPrimitives.ReadUInt32LittleEndian(b.AsSpan(p, 4));
    private static int I32(byte[] b, int p) => BinaryPrimitives.ReadInt32LittleEndian(b.AsSpan(p, 4));
    private static void WriteU32(byte[] b, int p, uint v) => BinaryPrimitives.WriteUInt32LittleEndian(b.AsSpan(p, 4), v);
}
