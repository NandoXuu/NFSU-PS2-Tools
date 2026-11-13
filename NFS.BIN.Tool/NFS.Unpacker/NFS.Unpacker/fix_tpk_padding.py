from pathlib import Path
import shutil

path = Path("TpkExtractor.cs")
source = path.read_text()

start_marker = "    private static byte[] DecompressTextureBlocks("
end_marker = "    private static byte[] ReadTexturePayload("

start = source.find(start_marker)
end = source.find(end_marker, start + len(start_marker))

if start < 0 or end < 0:
    raise SystemExit("Não foi possível localizar o método completo.")

new_method = r'''    private static byte[] DecompressTextureBlocks(
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

'''

updated = source[:start] + new_method + source[end:]

old_call = '''            byte[] decodedData = DecompressTextureBlocks(
                file, p3, dataPart + 8, dataPartEnd);'''

new_call = '''            byte[] decodedData = DecompressTextureBlocks(
                file, p3, p4, dataPart + 8, dataPartEnd);'''

if updated.count(old_call) != 1:
    raise SystemExit("Não encontrei a chamada original de DecompressTextureBlocks.")

updated = updated.replace(old_call, new_call, 1)

backup = path.with_name("TpkExtractor.cs.before_padding_fix")
shutil.copy2(path, backup)
path.write_text(updated)

print("Correção aplicada.")
print("Backup:", backup)
