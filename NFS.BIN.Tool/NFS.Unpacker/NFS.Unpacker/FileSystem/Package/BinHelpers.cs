using System;
using System.IO;

namespace NFS.Unpacker
{
    class BinHelpers
    {
        public static void ReadWriteFile(
            String m_ArchiveFile,
            String m_FullPath,
            UInt32 dwOffset,
            Int32 dwSize)
        {
            const Int32 MAX_BUFFER = 524288;

            if (!File.Exists(m_ArchiveFile))
            {
                Utils.iSetError(
                    "[ERROR]: Input archive -> " +
                    m_ArchiveFile +
                    " <- does not exist"
                );
                return;
            }

            if (dwSize < 0)
            {
                Utils.iSetError("[ERROR]: Invalid file size");
                return;
            }

            String directory = Path.GetDirectoryName(m_FullPath);

            if (!String.IsNullOrEmpty(directory))
                Directory.CreateDirectory(directory);

            using (FileStream source = File.OpenRead(m_ArchiveFile))
            {
                UInt64 endOffset = (UInt64)dwOffset + (UInt64)dwSize;

                if (endOffset > (UInt64)source.Length)
                {
                    Utils.iSetError(
                        "[ERROR]: Archive range exceeds file size: " +
                        m_ArchiveFile
                    );
                    return;
                }

                source.Seek(dwOffset, SeekOrigin.Begin);

                using (FileStream destination = new FileStream(
                    m_FullPath,
                    FileMode.Create,
                    FileAccess.Write,
                    FileShare.None))
                {
                    byte[] buffer = new byte[MAX_BUFFER];
                    Int32 remaining = dwSize;

                    while (remaining > 0)
                    {
                        Int32 requested = Math.Min(
                            buffer.Length,
                            remaining
                        );

                        Int32 read = source.Read(
                            buffer,
                            0,
                            requested
                        );

                        if (read <= 0)
                        {
                            throw new EndOfStreamException(
                                "Unexpected end of archive: " +
                                m_ArchiveFile
                            );
                        }

                        destination.Write(buffer, 0, read);
                        remaining -= read;
                    }
                }
            }
        }
    }
}
