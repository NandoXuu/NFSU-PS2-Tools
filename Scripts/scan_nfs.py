import os
import collections
import hashlib

ROOT = os.path.expanduser("~/storage/downloads/ps2/EXTRAIDO")
REPORT = os.path.expanduser("~/storage/downloads/ps2/RELATORIO_FORMATOS.txt")

if not os.path.isdir(ROOT):
    raise SystemExit(f"Pasta não encontrada: {ROOT}")

files = []
extensions = collections.Counter()
signatures = collections.Counter()
total_size = 0

def identify(data):
    if data.startswith(b"JDLZ"):
        return "JDLZ - compressao EA"
    if data.startswith(b"MOIR"):
        return "MOIR - recurso EA"
    if data.startswith(b"PK\x03\x04"):
        return "ZIP"
    if data.startswith(b"\x1f\x8b"):
        return "GZIP"
    if data.startswith(b"\x7fELF"):
        return "ELF executavel"
    if data.startswith(b"MZ"):
        return "Executavel DOS/Windows"
    if data.startswith(b"RIFF"):
        return "RIFF (audio/video)"
    if data.startswith(b"OggS"):
        return "OGG"
    if data.startswith(b"PNG\r\n\x1a\n"):
        return "PNG"
    if data.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if data.startswith(b"FSB"):
        return "FMOD Sound Bank"
    if data.startswith(b"BIFF"):
        return "BIFF"
    if data.startswith(b"FORM"):
        return "FORM/EA ou IFF"
    return "Assinatura desconhecida"

for base, dirs, names in os.walk(ROOT):
    dirs.sort()
    names.sort()
    for name in names:
        path = os.path.join(base, name)
        try:
            size = os.path.getsize(path)
            with open(path, "rb") as f:
                header = f.read(32)
            ext = os.path.splitext(name)[1].upper() or "[SEM EXTENSAO]"
            kind = identify(header)
            files.append((path, size, ext, header, kind))
            extensions[ext] += 1
            signatures[kind] += 1
            total_size += size
        except (OSError, PermissionError) as e:
            print("Erro:", path, e)

with open(REPORT, "w", encoding="utf-8") as out:
    out.write("RELATORIO DE FORMATOS - NFS UNDERGROUND\n")
    out.write("=" * 65 + "\n")
    out.write(f"Pasta: {ROOT}\n")
    out.write(f"Arquivos: {len(files)}\n")
    out.write(f"Tamanho total: {total_size:,} bytes\n\n")

    out.write("CONTAGEM POR EXTENSAO\n")
    out.write("-" * 65 + "\n")
    for ext, count in extensions.most_common():
        out.write(f"{count:7}  {ext}\n")

    out.write("\nCONTAGEM POR ASSINATURA\n")
    out.write("-" * 65 + "\n")
    for kind, count in signatures.most_common():
        out.write(f"{count:7}  {kind}\n")

    out.write("\nARQUIVOS E CABECALHOS\n")
    out.write("-" * 65 + "\n")
    for path, size, ext, header, kind in files:
        relative = os.path.relpath(path, ROOT)
        out.write(f"\nARQUIVO: {relative}\n")
        out.write(f"TAMANHO: {size} bytes\n")
        out.write(f"EXTENSAO: {ext}\n")
        out.write(f"FORMATO: {kind}\n")
        out.write(f"HEX: {header.hex(' ').upper()}\n")
        out.write(f"ASCII: {''.join(chr(b) if 32 <= b < 127 else '.' for b in header)}\n")

print("\nVARREDURA CONCLUIDA!")
print("Arquivos encontrados:", len(files))
print("Tamanho total:", f"{total_size:,}", "bytes")
print("\nExtensoes mais comuns:")
for ext, count in extensions.most_common(15):
    print(f"{count:6}  {ext}")
print("\nRelatorio salvo em:")
print(REPORT)
