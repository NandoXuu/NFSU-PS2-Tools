using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;

namespace NFS.Unpacker
{
    class BinUnpack
    {
        private static Boolean bZZData = true;
        private static List<BinEntry> m_EntryTable = new List<BinEntry>();
        private static List<String> m_BinList = new List<String>();

        public static void iDoIt(
            String m_IndexFile,
            String m_DstFolder,
            Boolean bOldZDirFormat = false)
        {
            if (!File.Exists(m_IndexFile))
                throw new FileNotFoundException("ZDIR index not found", m_IndexFile);

            BinHashList.iLoadProject();

            m_IndexFile = Path.GetFullPath(m_IndexFile);
            m_DstFolder = Path.GetFullPath(m_DstFolder);

            String indexDirectory = Path.GetDirectoryName(m_IndexFile);

            using (FileStream indexStream = File.OpenRead(m_IndexFile))
            using (BinaryReader reader = new BinaryReader(indexStream))
            {
                Int32 entrySize = bOldZDirFormat ? 12 : 24;

                if (indexStream.Length % entrySize != 0)
                    throw new InvalidDataException(
                        "ZDIR.BIN has an invalid size for this format."
                    );

                Int64 totalFiles = indexStream.Length / entrySize;

                if (totalFiles > Int32.MaxValue)
                    throw new InvalidDataException("Too many ZDIR entries.");

                m_EntryTable.Clear();

                for (Int32 i = 0; i < (Int32)totalFiles; i++)
                {
                    UInt32 nameHash = reader.ReadUInt32();
                    Int32 archiveID;
                    UInt32 localOffset;
                    UInt32 totalOffset;
                    Int32 size;
                    UInt32 checksum;

                    if (bOldZDirFormat)
                    {
                        archiveID = 0;
                        localOffset = reader.ReadUInt32();
                        size = reader.ReadInt32();
                        totalOffset = 0;
                        checksum = 0;
                    }
                    else
                    {
                        archiveID = reader.ReadInt32();
                        localOffset = reader.ReadUInt32();
                        totalOffset = reader.ReadUInt32();
                        size = reader.ReadInt32();
                        checksum = reader.ReadUInt32();
                    }

                    if (archiveID < 0)
                        throw new InvalidDataException(
                            "Invalid negative archive ID at entry " + i
                        );

                    if (size < 0)
                        throw new InvalidDataException(
                            "Invalid negative file size at entry " + i
                        );

                    m_EntryTable.Add(new BinEntry
                    {
                        dwNameHash = nameHash,
                        dwArchiveID = archiveID,
                        dwLocalOffset = unchecked(localOffset << 11),
                        dwTotalOffset = totalOffset,
                        dwSize = size,
                        dwChecksum = checksum
                    });
                }
            }

            // Need for Speed Undercover prototype: NAMES.HOO.
            String hooFile = Path.Combine(indexDirectory, "NAMES.HOO");

            bZZData = !File.Exists(hooFile);
            m_BinList.Clear();

            if (!bZZData)
            {
                m_BinList = File.ReadAllLines(hooFile)
                    .Select(line => line.Replace("Outfile: ", "").Trim())
                    .Where(line => line.Length > 0)
                    .ToList();
            }

            Directory.CreateDirectory(m_DstFolder);

            foreach (BinEntry entry in m_EntryTable)
            {
                String fileName = BinHashList.iGetNameFromHashList(
                    entry.dwNameHash
                );

                String archiveFile;
                String fullPath;

                if (bZZData)
                {
                    String archiveName = bOldZDirFormat
                        ? "ZZDATA"
                        : "ZZDATA" + entry.dwArchiveID.ToString();

                    archiveFile = Path.Combine(
                        indexDirectory,
                        archiveName + ".BIN"
                    );

                    fullPath = Path.Combine(
                        m_DstFolder,
                        archiveName,
                        fileName
                    );
                }
                else
                {
                    if (entry.dwArchiveID >= m_BinList.Count)
                    {
                        Utils.iSetWarning(
                            "[SKIPPED]: Invalid NAMES.HOO archive ID " +
                            entry.dwArchiveID
                        );
                        continue;
                    }

                    String archiveName = m_BinList[entry.dwArchiveID];

                    archiveFile = Path.Combine(
                        indexDirectory,
                        archiveName
                    );

                    fullPath = Path.Combine(
                        m_DstFolder,
                        Path.GetFileNameWithoutExtension(archiveName),
                        fileName
                    );
                }

                Utils.iSetInfo("[UNPACKING]: " + fileName);

                Utils.iCreateDirectory(fullPath);

                BinHelpers.ReadWriteFile(
                    archiveFile,
                    fullPath,
                    entry.dwLocalOffset,
                    entry.dwSize
                );
            }

            Utils.iSetInfo(
                "[DONE]: Processed " + m_EntryTable.Count + " ZDIR entries."
            );
        }
    }
}
