import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "asset_converter"))
import convert_assets as ca  # noqa: E402


def make_png(w, h, ctype, pixels, palette=None):
    """Gera PNG 8-bit sem filtro (filtro 0) para os testes."""
    raw = b"".join(b"\0" + bytes(pixels[y * w * _ch(ctype):(y + 1) * w * _ch(ctype)]) for y in range(h))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0))
    if palette:
        out += chunk(b"PLTE", bytes(palette))
    return out + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _ch(ctype):
    return {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]


class PngTests(unittest.TestCase):
    def test_rgba(self):
        px = [10, 20, 30, 255, 40, 50, 60, 128]
        w, h, rgba = ca.decode_png(make_png(2, 1, 6, px))
        self.assertEqual((w, h), (2, 1))
        self.assertEqual(list(rgba), px)

    def test_rgb_gets_opaque_alpha(self):
        w, h, rgba = ca.decode_png(make_png(1, 1, 2, [1, 2, 3]))
        self.assertEqual(list(rgba), [1, 2, 3, 255])

    def test_palette(self):
        png = make_png(2, 1, 3, [1, 0], palette=[255, 0, 0, 0, 255, 0])
        _, _, rgba = ca.decode_png(png)
        self.assertEqual(list(rgba), [0, 255, 0, 255, 255, 0, 0, 255])

    def test_palette_index_out_of_range(self):
        png = make_png(1, 1, 3, [5], palette=[255, 0, 0])
        with self.assertRaises(ValueError):
            ca.decode_png(png)

    def test_not_png(self):
        with self.assertRaises(ValueError):
            ca.decode_png(b"nope")


class MeshTests(unittest.TestCase):
    OBJ = (
        "o a\nv 0 0 0\nv 1 0 0\nv 1 1 0\nvn 0 0 1\nvn 0 0 1\nvn 0 0 1\nf 1//1 2//2 3//3\n"
        "o b\nv 0 1 0\nvn 0 0 1\nf 1//1 3//3 4//4\n"
    )

    def test_obj_to_nmsh(self):
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "x.obj", Path(d) / "x.nmsh"
            src.write_text(self.OBJ)
            info = ca.convert_mesh(src, dst)
            self.assertEqual(info["vertices"], 4)
            self.assertEqual(info["triangles"], 2)
            self.assertEqual(info["submeshes"], 2)
            b = dst.read_bytes()
            self.assertEqual(b[:4], b"NMSH")
            ver, nv, ni, ns, _ = struct.unpack_from("<IIIII", b, 4)
            self.assertEqual((ver, nv, ni, ns), (1, 4, 6, 2))
            self.assertEqual(len(b), 4 + 20 + 24 + ns * 40 + nv * 24 + ni * 4)

    def test_bad_index(self):
        with self.assertRaises(ValueError):
            ca.build_nmsh([(0, 0, 0)], [(0, 0, 1)], [("a", [(0, 1, 2)])])

    def test_normal_count_mismatch(self):
        with self.assertRaises(ValueError):
            ca.build_nmsh([(0, 0, 0), (1, 0, 0)], [(0, 0, 1)], [("a", [])])


class WavTests(unittest.TestCase):
    @staticmethod
    def wav(tag=1, ch=1, bits=16, n=4):
        data = b"\0\0" * n
        return (b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " +
                struct.pack("<IHHIIHH", 16, tag, ch, 20000, 20000 * 2, 2, bits) +
                b"data" + struct.pack("<I", len(data)) + data)

    def test_valid(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.wav"
            p.write_bytes(self.wav())
            self.assertEqual(ca.validate_wav(p)["frames"], 4)

    def test_rejects_float(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.wav"
            p.write_bytes(self.wav(tag=3))
            with self.assertRaises(ValueError):
                ca.validate_wav(p)


if __name__ == "__main__":
    unittest.main()
