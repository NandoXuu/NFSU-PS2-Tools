using System;
using System.IO;
using System.Collections.Generic;

namespace NFS.Unpacker
{
    class BinHashList
    {
        static readonly String m_Path = Path.Combine(
            Utils.iGetApplicationPath(),
            "Projects"
        );

        static readonly String m_ProjectFile = "FileNames.list";

        static readonly String m_ProjectFilePath = Path.Combine(
            m_Path,
            m_ProjectFile
        );

        static Dictionary<UInt32, String> m_HashList =
            new Dictionary<UInt32, String>();

        public static void iLoadProject()
        {
            if (!File.Exists(m_ProjectFilePath))
            {
                Utils.iSetError(
                    "[ERROR]: Unable to load project file " +
                    m_ProjectFilePath
                );

                throw new FileNotFoundException(
                    "Project file not found",
                    m_ProjectFilePath
                );
            }

            Int32 i = 0;
            m_HashList.Clear();

            using (StreamReader TProjectFile =
                new StreamReader(m_ProjectFilePath))
            {
                String m_Line;

                while ((m_Line = TProjectFile.ReadLine()) != null)
                {
                    UInt32 dwHash = BinHash.iGetHash(
                        m_Line.ToUpperInvariant()
                    );

                    if (m_HashList.ContainsKey(dwHash))
                    {
                        String m_Collision = null;
                        m_HashList.TryGetValue(
                            dwHash,
                            out m_Collision
                        );

                        Console.WriteLine(
                            "[COLLISION]: {0} <-> {1}",
                            m_Collision,
                            m_Line
                        );

                        continue;
                    }

                    m_HashList.Add(dwHash, m_Line);
                    i++;
                }
            }

            Console.WriteLine(
                "[INFO]: Project File Loaded: {0}",
                i
            );

            Console.WriteLine();
        }

        public static String iGetNameFromHashList(UInt32 dwHash)
        {
            String m_FileName;

            if (m_HashList.TryGetValue(dwHash, out m_FileName))
                return m_FileName.Replace('\\', Path.DirectorySeparatorChar).Replace('/', Path.DirectorySeparatorChar);

            return Path.Combine(
                "__Unknown",
                dwHash.ToString("X8")
            );
        }
    }
}
