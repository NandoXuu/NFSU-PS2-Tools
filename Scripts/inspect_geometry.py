import struct
from pathlib import Path

p = Path("EXTRAIDO/ZZDATA0/CARS/350Z/GEOMETRY.BIN")
data = p.read_bytes()

IDS = {
    0x80134010: "MESH",
    0x00134011: "MESH_META",
    0x80134100: "MESH_GEOM",
    0x00134900: "GEOM_META",
    0x00134B01: "VERTEX_BUFFER",
    0x00134B03: "FACE_BUFFER",
}

print("Arquivo:", p.name)
print("Tamanho:", len(data))

for ident, name in IDS.items():
    sig = struct.pack("<I", ident)
    positions = []
    start = 0

    while True:
        pos = data.find(sig, start)
        if pos < 0:
            break
        positions.append(pos)
        start = pos + 4

    print(f"\n{name} ({ident:08X}): {len(positions)} ocorrência(s)")

    for pos in positions[:40]:
        size = struct.unpack_from("<I", data, pos + 4)[0] if pos + 8 <= len(data) else 0
        end = pos + 8 + size

        print(
            f"  offset=0x{pos:08X} "
            f"size=0x{size:X} ({size}) "
            f"end=0x{end:X} "
            f"válido={end <= len(data)}"
        )

        if name == "GEOM_META" and size >= 56:
            payload = pos + 8
            faces = struct.unpack_from("<I", data, payload + 36)[0]
            vertices = struct.unpack_from("<I", data, payload + 52)[0]
            print(f"    faces={faces} vertices={vertices}")
