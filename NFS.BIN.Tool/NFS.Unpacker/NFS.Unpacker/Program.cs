using System;
using System.IO;

namespace NFS.Unpacker
{
    class Program
    {
        public static String m_Title = "Need for Speed ZDIR Unpacker";

        static void Main(String[] args)
        {
            Console.Title = m_Title;
            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine(m_Title);
            Console.WriteLine("(c) 2024 Ekey (h4x0r) / v{0}\n",
                Utils.iGetApplicationVersion());
            Console.ResetColor();

            if (args.Length != 3)
            {
                ShowUsage();
                return;
            }

            string mode = args[0];
            string source = args[1];
            string destination = args[2];

            try
            {
                if (mode == "-tpk")
                {
                    if (!File.Exists(source))
                        throw new FileNotFoundException(
                            "Arquivo TPK não encontrado.", source);

                    TpkExtractor.Extract(source, destination);

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("[OK] Extração TPK concluída: " + destination);
                    Console.ResetColor();
                    return;
                }

                if (mode == "-jdlz")
                {
                    if (!File.Exists(source))
                        throw new FileNotFoundException("Arquivo de entrada não encontrado.", source);

                    Jdlz.DecompressFile(source, destination);

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("[OK] Descomprimido: " + destination);
                    Console.ResetColor();
                    return;
                }

                if (mode == "-jdlz-dir")
                {
                    DecompressDirectory(source, destination);
                    return;
                }

                RunOriginalExtractor(mode, source, destination);
            }
            catch (Exception ex)
            {
                Utils.iSetError("[ERROR]: " + ex.Message);
            }
        }

        static void DecompressDirectory(string source, string destination)
        {
            if (!Directory.Exists(source))
                throw new DirectoryNotFoundException(
                    "Diretório de entrada não encontrado: " + source);

            string inputRoot = Path.GetFullPath(source);
            string outputRoot = Path.GetFullPath(destination);

            if (outputRoot.StartsWith(
                inputRoot.TrimEnd(Path.DirectorySeparatorChar) +
                Path.DirectorySeparatorChar,
                StringComparison.Ordinal))
            {
                throw new InvalidOperationException(
                    "A pasta de saída não pode ficar dentro da pasta de entrada.");
            }

            Directory.CreateDirectory(outputRoot);

            string[] files = Directory.GetFiles(
                inputRoot, "*.LZC", SearchOption.AllDirectories);

            int success = 0;
            int errors = 0;

            Console.WriteLine("Arquivos JDLZ encontrados: " + files.Length);
            Console.WriteLine();

            foreach (string file in files)
            {
                string relative = Path.GetRelativePath(inputRoot, file);

                // Preserva o nome original e acrescenta .DEC.BIN.
                string outputRelative = relative + ".DEC.BIN";
                string outputFile = Path.Combine(outputRoot, outputRelative);

                try
                {
                    Jdlz.DecompressFile(file, outputFile);

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("[OK] " + relative);
                    Console.ResetColor();

                    success++;
                }
                catch (Exception ex)
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("[ERRO] " + relative);
                    Console.WriteLine("       " + ex.Message);
                    Console.ResetColor();

                    errors++;
                }
            }

            Console.WriteLine();
            Console.WriteLine("===== RESULTADO =====");
            Console.WriteLine("Encontrados: " + files.Length);
            Console.WriteLine("Sucesso:     " + success);
            Console.WriteLine("Erros:       " + errors);
            Console.WriteLine("Destino:     " + outputRoot);
        }

        static void RunOriginalExtractor(
            string format, string source, string destination)
        {
            Boolean oldFormat;

            switch (format)
            {
                case "-false":
                    oldFormat = false;
                    break;

                case "-true":
                    oldFormat = true;
                    break;

                default:
                    Utils.iSetError(
                        "[ERROR]: Modo desconhecido. Use -false, -true, -jdlz ou -jdlz-dir.");
                    return;
            }

            if (Path.GetFileName(source) != "ZDIR.BIN")
            {
                Utils.iSetError(
                    "[ERROR]: Você precisa especificar o arquivo ZDIR.BIN.");
                return;
            }

            if (!File.Exists(source))
            {
                Utils.iSetError(
                    "[ERROR]: Arquivo de entrada não encontrado: " + source);
                return;
            }

            string output = Utils.iCheckArgumentsPath(destination);
            BinUnpack.iDoIt(source, output, oldFormat);
        }

        static void ShowUsage()
        {
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine("[Usage]");
            Console.WriteLine("  NFS.Unpacker -false ZDIR.BIN pasta_saida");
            Console.WriteLine("  NFS.Unpacker -true ZDIR.BIN pasta_saida");
            Console.WriteLine("  NFS.Unpacker -jdlz arquivo.LZC arquivo_saida");
            Console.WriteLine("  NFS.Unpacker -jdlz-dir pasta_entrada pasta_saida");
            Console.WriteLine("  NFS.Unpacker -tpk arquivo.BIN pasta_saida");
            Console.ResetColor();
        }
    }
}
