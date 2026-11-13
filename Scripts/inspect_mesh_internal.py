import struct
from pathlib import Path

p = Path("EXTRAIDO/ZZDATA0/CARS/350Z/GEOMETRY.BIN")
data = p.read_bytes()

MESH = struct.pack("<I", 0x80134010)
META = struct.pack("<I", 0x00134011)
GEOM = struct.pack("<I", 0x80134100)

def read_chunk(pos):
    ident, size = struct.unpack_from("<II", data, pos)
    return ident, size, pos + 8

def dump(label, pos, length):
    print(f"\n--- {label} | offset 0x{pos:X} ---")
    chunk = data[pos:pos + length]

    for i in range(0, len(chunk), 16):
        part = chunk[i:i+16]
        hx = " ".join(f"{b:02X}" for b in part)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in part)
        print(f"{pos+i:08X}: {hx:<47} {asc}")

    print("\nValores uint32:")
    for i in range(0, min(len(chunk), 128), 4):
        value = struct.unpack_from("<I", chunk, i)[0]
        print(f"+0x{i:02X}: 0x{value:08X} ({value})")

    strings = []
    current = bytearray()
    for b in chunk:
        if 32 <= b < 127:
            current.append(b)
        else:
            if len(current) >= 4:
                strings.append(current.decode("ascii", errors="replace"))
            current.clear()
    if len(current) >= 4:
        strings.append(current.decode("ascii", errors="replace"))

    if strings:
        print("Strings:", strings)

mesh_positions = []
pos = 0

while True:
    pos = data.find(MESH, pos)
    if pos < 0:
        break
    mesh_positions.append(pos)
    pos += 4

print("Total MESH:", len(mesh_positions))

for index, mesh_pos in enumerate(mesh_positions[:3]):
    _, mesh_size, mesh_payload = read_chunk(mesh_pos)
    mesh_end = mesh_payload + mesh_size

    print("\n" + "="*65)
    print(f"MESH #{index} em 0x{mesh_pos:X}")
    print(f"Tamanho: 0x{mesh_size:X}")

    meta_pos = data.find(META, mesh_payload, mesh_end)
    geom_pos = data.find(GEOM, mesh_payload, mesh_end)

    if meta_pos >= 0:
        _, meta_size, meta_payload = read_chunk(meta_pos)
        print(f"META: 0x{meta_pos:X}, tamanho 0x{meta_size:X}")
        dump("META", meta_payload, min(meta_size, 192))

    if geom_pos >= 0:
        _, geom_size, geom_payload = read_chunk(geom_pos)
        print(f"\nGEOM: 0x{geom_pos:X}, tamanho 0x{geom_size:X}")
        dump("GEOM", geom_payload, min(geom_size, 192))
