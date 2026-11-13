using System;
using System.IO;
using System.Reflection;

namespace NFS.Unpacker
{
    class Utils
    {
        public static String iGetApplicationPath()
        {
            return Path.GetDirectoryName(
                Assembly.GetExecutingAssembly().Location
            );
        }

        public static String iGetApplicationVersion()
        {
            return Assembly.GetExecutingAssembly()
                .GetName().Version.ToString();
        }

        public static void iSetInfo(String m_String)
        {
            Console.ForegroundColor = ConsoleColor.White;
            Console.WriteLine(m_String);
            Console.ResetColor();
        }

        public static void iSetError(String m_String)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine(m_String + "!");
            Console.ResetColor();
        }

        public static void iSetWarning(String m_String)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine(m_String + "!");
            Console.ResetColor();
        }

        public static String iCheckArgumentsPath(String m_Arg)
        {
            if (String.IsNullOrWhiteSpace(m_Arg))
                return m_Arg;

            return Path.EndsInDirectorySeparator(m_Arg)
                ? m_Arg
                : m_Arg + Path.DirectorySeparatorChar;
        }

        // Recebe um caminho de arquivo e cria a pasta que o contém.
        public static void iCreateDirectory(String m_FilePath)
        {
            if (String.IsNullOrWhiteSpace(m_FilePath))
                return;

            String directory = Path.GetDirectoryName(m_FilePath);

            if (!String.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);
        }
    }
}
