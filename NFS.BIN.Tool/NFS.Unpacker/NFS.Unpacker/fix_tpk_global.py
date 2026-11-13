from pathlib import Path
import shutil

p = Path("TpkExtractor.cs")
s = p.read_text()

old1 = '''            var compressionBlocks = ReadCompressionBlocks(
                file, p3, dataPart + 8, dataPartEnd);
'''

new1 = '''            byte[] decodedData = DecompressTextureBlocks(
                file, p3, dataPart + 8, dataPartEnd);
'''

old2 = '''                    if (!compressionBlocks.TryGetValue(t.BinKey, out var compressedBlock))
                        throw new InvalidDataException($"Bloco comprimido não encontrado para a key 0x{t.BinKey:X8}.");

                    byte[] decoded = DecompressTextureBlock(file, compressedBlock);
                    ValidateTexture(t, decoded.Length);
                    byte[] payload = ReadTexturePayload(decoded, t);
'''

new2 = '''                    ValidateTexture(t, decodedData.Length);
                    byte[] payload = ReadTexturePayload(decodedData, t);
'''

method = '''    private static byte[] DecompressTextureBlocks(
        byte[] file, int p3, int dataStart, int dataEnd)
    {
        int size = ReadSize(file, p3);

        if (size % 24 != 0)
            throw new InvalidDataException("INFO_PART3 possui tamanho inválido.");

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

'''

if s.count(old1) != 1:
    raise SystemExit("Não encontrei exatamente uma declaração compressionBlocks.")

if s.count(old2) != 1:
    raise SystemExit("Não encontrei exatamente um trecho de descompressão individual.")

if s.count("private static byte[] DecompressTextureBlocks(") != 0:
    raise SystemExit("O método DecompressTextureBlocks já existe.")

backup = Path("TpkExtractor.cs.before_global_buffer")
shutil.copy2(p, backup)

s = s.replace(old1, new1, 1)
s = s.replace(old2, new2, 1)

marker = "    private static byte[] ReadTexturePayload("
if s.count(marker) != 1:
    raise SystemExit("Não encontrei o ponto de inserção do novo método.")

s = s.replace(marker, method + marker, 1)

p.write_text(s)

print("Correção aplicada!")
print("Backup:", backup)
