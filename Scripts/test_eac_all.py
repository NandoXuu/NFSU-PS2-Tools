exec(open(str(__import__('pathlib').Path.home() / 'test_eac_tpk.py')).read().split('print("\\nTestando um bloco')[0])

outdir = BASE / "EAC_ALL_OUTPUT"
outdir.mkdir(exist_ok=True)

ok = 0
failed = 0

print("\n========== TESTE COMPLETO ==========")

for item in records:
    blob = item["blob"]
    expected = item["decoded"]

    src = ctypes.create_string_buffer(blob, len(blob))
    size = lib.ea_get_decompressed_size(src, len(blob))

    if size != expected or size <= 0:
        print(f"[ERRO] {item['index']:02} {item['signature']} tamanho inválido: {size}")
        failed += 1
        continue

    output = ctypes.create_string_buffer(size)

    result = lib.ea_decompress(src, len(blob), output, size)

    if result != expected:
        print(f"[ERRO] {item['index']:02} {item['signature']} retorno={result}")
        failed += 1
        continue

    path = outdir / f"{item['index']:02}_{item['key']:08X}.bin"
    path.write_bytes(output.raw[:size])

    print(f"[OK] {item['index']:02} {item['signature']} {size:,} bytes")
    ok += 1

print("\n========== RESUMO ==========")
print(f"Sucesso: {ok}/{len(records)}")
print(f"Falhas: {failed}")
print(f"Saída: {outdir}")
