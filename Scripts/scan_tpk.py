import os
import struct

ROOT = os.path.expanduser(
    "~/storage/downloads/ps2/EXTRAIDO"
)

IDS = {
    0xB3310000: "INFO_BLOCK",
    0xB3320000: "DATA_BLOCK",
    0x33310001: "INFO_PART1",
    0x33310002: "INFO_PART2",
    0x33310003: "INFO_PART3",
    0x33310004: "INFO_PART4",
    0x33310005: "INFO_PART5",
    0xB3312000: "BINDATA",
    0x33320001: "DATA_PART1",
    0x33320002: "DATA_PART2",
    0x33320003: "DATA_PART3",
}

PATTERNS = {
    struct.pack("<I", value): name
    for value, name in IDS.items()
}

print("===== SCAN TPK =====")
print("Diretório:", ROOT)

total = 0
hits = 0

for base, _, files in os.walk(ROOT):
    for filename in files:
        path = os.path.join(base, filename)

        try:
            size = os.path.getsize(path)
            if size == 0 or size > 512 * 1024 * 1024:
                continue

            with open(path, "rb") as f:
                data = f.read()

            found = []

            for pattern, name in PATTERNS.items():
                pos = 0
                while True:
                    pos = data.find(pattern, pos)
                    if pos < 0:
                        break

                    found.append((pos, name))
                    pos += 1

            if found:
                total += 1
                hits += len(found)

                print(f"\nARQUIVO: {path}")
                print(f"TAMANHO: {size:,} bytes")

                for offset, name in sorted(found):
                    print(f"  0x{offset:08X}  {name}")

        except (OSError, MemoryError) as e:
            print("ERRO:", path, e)

print("\n===== RESULTADO =====")
print("Arquivos com identificadores:", total)
print("Ocorrências encontradas:", hits)
