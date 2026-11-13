using System;
using System.IO;
using System.Buffers.Binary;

namespace NFS.Unpacker
{
    public static class Jdlz
    {
        private const int HeaderSize = 16;
        private const int MaxOutputSize = 512 * 1024 * 1024;

        public static byte[] Decompress(byte[] input)
        {
            if (input == null)
                throw new ArgumentNullException(nameof(input));

            if (input.Length < HeaderSize)
                throw new InvalidDataException("Arquivo menor que o cabeçalho JDLZ.");

            if (input[0] != 0x4A || input[1] != 0x44 ||
                input[2] != 0x4C || input[3] != 0x5A)
                throw new InvalidDataException("Assinatura JDLZ não encontrada.");

            if (input[4] != 0x02 || input[5] != 0x10)
                throw new InvalidDataException("Versão ou tamanho de cabeçalho JDLZ incompatível.");

            if (input[6] != 0 || input[7] != 0)
                throw new InvalidDataException("Campos reservados do cabeçalho inválidos.");

            uint outputSize = BinaryPrimitives.ReadUInt32LittleEndian(
                input.AsSpan(8, 4));

            uint compressedSize = BinaryPrimitives.ReadUInt32LittleEndian(
                input.AsSpan(12, 4));

            if (compressedSize != input.Length)
                throw new InvalidDataException(
                    $"Tamanho comprimido inválido: cabeçalho={compressedSize}, arquivo={input.Length}.");

            if (outputSize > MaxOutputSize)
                throw new InvalidDataException(
                    $"Saída excede o limite de segurança de {MaxOutputSize} bytes.");

            byte[] output = new byte[(int)outputSize];

            int inPos = HeaderSize;
            int outPos = 0;

            int flags1 = 1;
            int flags2 = 1;

            while (outPos < output.Length)
            {
                if (flags1 == 1)
                {
                    if (inPos >= input.Length)
                        throw new InvalidDataException("Fim inesperado ao ler flags1.");

                    flags1 = input[inPos++] | 0x100;
                }

                if (flags2 == 1)
                {
                    if (inPos >= input.Length)
                        throw new InvalidDataException("Fim inesperado ao ler flags2.");

                    flags2 = input[inPos++] | 0x100;
                }

                if ((flags1 & 1) != 0)
                {
                    if (inPos + 1 >= input.Length)
                        throw new InvalidDataException("Referência JDLZ incompleta.");

                    int distance;
                    int length;

                    if ((flags2 & 1) != 0)
                    {
                        length =
                            (input[inPos + 1] |
                            ((input[inPos] & 0xF0) << 4)) + 3;

                        distance = (input[inPos] & 0x0F) + 1;
                    }
                    else
                    {
                        distance =
                            (input[inPos + 1] |
                            ((input[inPos] & 0xE0) << 3)) + 17;

                        length = (input[inPos] & 0x1F) + 3;
                    }

                    inPos += 2;

                    if (distance <= 0 || distance > outPos)
                        throw new InvalidDataException(
                            $"Distância retroativa inválida: {distance}, posição: {outPos}.");

                    if (length > output.Length - outPos)
                        throw new InvalidDataException(
                            "Referência ultrapassa o tamanho esperado da saída.");

                    for (int i = 0; i < length; i++)
                    {
                        output[outPos + i] = output[outPos + i - distance];
                    }

                    outPos += length;
                    flags2 >>= 1;
                }
                else
                {
                    if (inPos >= input.Length)
                        throw new InvalidDataException("Fim inesperado ao ler byte literal.");

                    output[outPos++] = input[inPos++];
                }

                flags1 >>= 1;
            }

            return output;
        }

        public static void DecompressFile(string source, string destination)
        {
            byte[] compressed = File.ReadAllBytes(source);
            byte[] decompressed = Decompress(compressed);

            string directory = Path.GetDirectoryName(destination);

            if (!string.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            File.WriteAllBytes(destination, decompressed);
        }
    }
}
