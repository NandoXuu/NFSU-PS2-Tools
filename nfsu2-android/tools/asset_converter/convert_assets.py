#!/usr/bin/env python3
"""Conversor de assets recuperados -> formatos do motor (NMSH / NTEX / WAV).

Nao altera nenhum arquivo de origem: so le e escreve em --out.

Uso:
  convert_assets.py mesh    <entrada.obj> <saida.nmsh>
  convert_assets.py texture <entrada.png> <saida.ntex>
  convert_assets.py audio   <entrada.wav> <saida.wav>      (valida PCM16 e copia)
  convert_assets.py diag    --obj X.obj --png Y.png --wav Z.wav --out PASTA
"""
import argparse
import math
import shutil
import struct
import sys
import zlib
from pathlib import Path

NMSH_MAGIC = b"NMSH"
NTEX_MAGIC = b"NTEX"


# ----------------------------------------------------------------------------- malha
def parse_obj(path):
    """Le o OBJ gerado por tools_v2/extrair_geometria.py.

    Retorna (verts[(x,y,z)], normals[(x,y,z)], objects[(nome, [tri...])]).
    Indices de face sao globais (1-based), como no OBJ.
    """
    verts, normals, objects = [], [], []
    cur_name, cur_tris = None, None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line or line[0] == "#":
                continue
            parts = line.split()
            if not parts:
                continue
            tag = parts[0]
            if tag == "v":
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif tag == "vn":
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
            elif tag == "o":
                if cur_name is not None:
                    objects.append((cur_name, cur_tris))
                cur_name, cur_tris = parts[1] if len(parts) > 1 else "obj", []
            elif tag == "f":
                if cur_name is None:
                    cur_name, cur_tris = "default", []
                idx = [int(p.split("/")[0]) for p in parts[1:4]]
                cur_tris.append(tuple(i - 1 for i in idx))
    if cur_name is not None:
        objects.append((cur_name, cur_tris))
    return verts, normals, objects


def build_nmsh(verts, normals, objects):
    if normals and len(normals) != len(verts):
        raise ValueError(f"vn ({len(normals)}) != v ({len(verts)})")
    nv = len(verts)
    indices, subs = [], []
    for name, tris in objects:
        off = len(indices)
        for tri in tris:
            for i in tri:
                if not 0 <= i < nv:
                    raise ValueError(f"indice {i} fora de [0,{nv})")
            indices.extend(tri)
        subs.append((name, off, len(indices) - off))
    for v in verts:
        if not all(math.isfinite(c) for c in v):
            raise ValueError("vertice nao finito")
    if verts:
        mn = [min(v[k] for v in verts) for k in range(3)]
        mx = [max(v[k] for v in verts) for k in range(3)]
    else:
        mn = mx = [0.0, 0.0, 0.0]

    out = bytearray()
    out += NMSH_MAGIC + struct.pack("<IIIII", 1, nv, len(indices), len(subs), 0)
    out += struct.pack("<6f", *mn, *mx)
    for name, off, cnt in subs:
        out += name.encode("ascii", "replace")[:31].ljust(32, b"\0")
        out += struct.pack("<II", off, cnt)
    for i, v in enumerate(verts):
        n = normals[i] if normals else (0.0, 0.0, 1.0)
        out += struct.pack("<6f", *v, *n)
    out += struct.pack("<%dI" % len(indices), *indices)
    return bytes(out), dict(vertices=nv, triangles=len(indices) // 3, submeshes=len(subs), aabb=(mn, mx))


def convert_mesh(src, dst):
    verts, normals, objects = parse_obj(src)
    blob, info = build_nmsh(verts, normals, objects)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(blob)
    return info


# ----------------------------------------------------------------------------- textura
def decode_png(data):
    """Decodificador PNG minimo (8 bits, nao entrelacado). Retorna (w, h, rgba bytes)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("nao eh PNG")
    pos, idat, plte, trns, ihdr = 8, bytearray(), None, None, None
    while pos + 8 <= len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"PLTE":
            plte = body
        elif typ == b"tRNS":
            trns = body
        elif typ == b"IDAT":
            idat += body
        elif typ == b"IEND":
            break
    if ihdr is None:
        raise ValueError("sem IHDR")
    w, h, depth, ctype, _, _, interlace = ihdr
    if interlace:
        raise ValueError("PNG entrelacado nao suportado")
    chans = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if chans is None:
        raise ValueError(f"tipo de cor {ctype} nao suportado")
    if depth != 8:
        raise ValueError(f"profundidade {depth} nao suportada (apenas 8)")
    raw = zlib.decompress(bytes(idat))
    stride, bpp = w * chans, chans
    if len(raw) != (stride + 1) * h:
        raise ValueError("tamanho dos dados nao confere")
    rows, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        ft = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif ft != 0:
            raise ValueError(f"filtro {ft} invalido")
        rows.append(line)
        prev = line
    out = bytearray(w * h * 4)
    o = 0
    pal = None
    if ctype == 3:
        if plte is None:
            raise ValueError("paleta ausente")
        pal = [(plte[i], plte[i + 1], plte[i + 2], (trns[i // 3] if trns and i // 3 < len(trns) else 255))
               for i in range(0, len(plte), 3)]
    for line in rows:
        for x in range(w):
            if ctype == 6:
                r, g, b, a = line[x * 4:x * 4 + 4]
            elif ctype == 2:
                r, g, b = line[x * 3:x * 3 + 3]
                a = 255
            elif ctype == 0:
                r = g = b = line[x]
                a = 255
            elif ctype == 4:
                r = g = b = line[x * 2]
                a = line[x * 2 + 1]
            else:
                idx = line[x]
                if idx >= len(pal):
                    raise ValueError("indice de paleta invalido")
                r, g, b, a = pal[idx]
            out[o:o + 4] = bytes((r, g, b, a))
            o += 4
    return w, h, bytes(out)


def convert_texture(src, dst):
    w, h, rgba = decode_png(Path(src).read_bytes())
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(NTEX_MAGIC + struct.pack("<IIII", 1, w, h, 1) + rgba)
    return dict(width=w, height=h)


# ----------------------------------------------------------------------------- audio
def validate_wav(path):
    d = Path(path).read_bytes()
    if d[:4] != b"RIFF" or d[8:12] != b"WAVE":
        raise ValueError("nao eh WAV")
    pos, fmt = 12, None
    while pos + 8 <= len(d):
        cid, ln = struct.unpack("<4sI", d[pos:pos + 8])
        if cid == b"fmt ":
            fmt = struct.unpack("<HHIIHH", d[pos + 8:pos + 24])
        elif cid == b"data":
            if fmt is None:
                raise ValueError("data antes de fmt")
            tag, ch, rate, _, _, bits = fmt
            if tag != 1 or bits != 16 or ch not in (1, 2):
                raise ValueError(f"WAV nao suportado: tag={tag} canais={ch} bits={bits}")
            frames = min(ln, len(d) - pos - 8) // (2 * ch)
            return dict(rate=rate, channels=ch, frames=frames, seconds=frames / rate)
        pos += 8 + ln + (ln & 1)
    raise ValueError("chunk data ausente")


def convert_audio(src, dst):
    info = validate_wav(src)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return info


# ----------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("mesh", "texture", "audio"):
        p = sub.add_parser(name)
        p.add_argument("src")
        p.add_argument("dst")
    d = sub.add_parser("diag")
    d.add_argument("--obj", required=True)
    d.add_argument("--png", required=True)
    d.add_argument("--wav", required=True)
    d.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "mesh":
        print(convert_mesh(a.src, a.dst))
    elif a.cmd == "texture":
        print(convert_texture(a.src, a.dst))
    elif a.cmd == "audio":
        print(convert_audio(a.src, a.dst))
    else:
        out = Path(a.out) / "diag"
        print("mesh   :", convert_mesh(a.obj, out / "car.nmsh"))
        print("texture:", convert_texture(a.png, out / "tex.ntex"))
        print("audio  :", convert_audio(a.wav, out / "clip.wav"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
