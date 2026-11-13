import ctypes
import struct
from pathlib import Path

BASE = Path.home()
LIB = BASE / "EAC-NFS/EAC/HUFF/EA Compression Tool/libea_compression.so"
TPK = BASE / "storage/downloads/ps2/EXTRAIDO/ZZDATA0/CARS/3000GT/TEXTURES.BIN"

# INFO_PART3: início dos registros, depois do cabeçalho de 8 bytes.
INFO_PART3 = 0x15C
RECORD_SIZE = 24
RECORD_COUNT = 22

print("Carregando biblioteca...")
lib = ctypes.CDLL(str(LIB))

lib.ea_detect_format.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.ea_detect_format.restype = ctypes.c_int

lib.ea_get_decompressed_size.argtypes = [
    ctypes.c_void_p, ctypes.c_int
]
lib.ea_get_decompressed_size.restype = ctypes.c_int

lib.ea_decompress.argtypes = [
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_int
]
lib.ea_decompress.restype = ctypes.c_int

data = TPK.read_bytes()

print(f"TPK: {TPK}")
print(f"Tamanho: {len(data):,} bytes")
print("\nLendo INFO_PART3...")

records = []

for i in range(RECORD_COUNT):
    pos = INFO_PART3 + i * RECORD_SIZE

    key, offset, encoded, decoded, header_end, unknown = (
        struct.unpack_from("<6I", data, pos)
    )

    if offset + encoded > len(data):
        print(f"Registro {i}: bloco ultrapassa o arquivo!")
        continue

    blob = data[offset:offset + encoded]
    signature = blob[:4].decode("ascii", errors="replace")

    records.append({
        "index": i,
        "key": key,
        "offset": offset,
        "encoded": encoded,
        "decoded": decoded,
        "signature": signature,
        "blob": blob
    })

    print(
        f"[{i:02}] {signature} | "
        f"offset=0x{offset:X} | "
        f"comprimido={encoded:#x} | "
        f"descomprimido={decoded:#x}"
    )

print("\nTestando um bloco de cada formato...")

for fmt in ("HUFF", "JDLZ"):
    item = next(
        (r for r in records if r["signature"] == fmt),
        None
    )

    if item is None:
        print(f"\n{fmt}: nenhum bloco encontrado.")
        continue

    blob = item["blob"]
    expected = item["decoded"]

    print(f"\n========== {fmt} ==========")
    print(f"Registro: {item['index']}")
    print(f"Key: {item['key']:08X}")
    print(f"Tamanho esperado: {expected} bytes")

    src = ctypes.create_string_buffer(blob, len(blob))

    detected = lib.ea_detect_format(src, len(blob))
    reported_size = lib.ea_get_decompressed_size(src, len(blob))

    print(f"Formato detectado (enum): {detected}")
    print(f"Tamanho informado pela biblioteca: {reported_size}")

    if reported_size <= 0:
        print("ERRO: tamanho de saída inválido.")
        continue

    if reported_size != expected:
        print("AVISO: tamanho da biblioteca difere do INFO_PART3.")

    output = ctypes.create_string_buffer(reported_size)

    result = lib.ea_decompress(
        src,
        len(blob),
        output,
        reported_size
    )

    print(f"Retorno de ea_decompress: {result}")

    if result < 0:
        print("FALHA: biblioteca retornou erro.")
        continue

    output_bytes = output.raw[:reported_size]

    out_path = BASE / f"EAC_TEST_{fmt}_{item['index']:02}.bin"
    out_path.write_bytes(output_bytes)

    print(f"Arquivo salvo: {out_path}")
    print(f"Primeiros 16 bytes: {output_bytes[:16].hex(' ')}")
    print(f"Bytes não nulos: {sum(b != 0 for b in output_bytes)}")

print("\nTeste finalizado.")
