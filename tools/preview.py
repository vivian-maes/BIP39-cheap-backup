"""
Render a PNG preview for every .scad the generator produces.

Written because a card must be proofread *before* it is printed, and because
OpenSCAD is not always installed. It reads the very contours that go into the
.scad and fills them with the same even-odd rule OpenSCAD applies to
polygon(paths=...), so a preview showing hollow counters is evidence that the
.scad has hollow counters.

Pure standard library: no OpenSCAD, no third-party module.

    python3 tools/preview.py <key_path> <title> <out_dir>
"""

import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libs.card_dessing import CardDessing
from libs.word_manager import WordManager

PX_PER_MM = 24
SUPERSAMPLE = 2

# Filament clair / filament sombre, plus une teinte de fond pour ce qui est
# traversant, et une ombre pour ce qui est en creux.
LIGHT = (0xF2, 0xE8, 0xD5)
DARK = (0x1B, 0x2B, 0x34)
VOID = (0x8A, 0x8A, 0x8A)
ENGRAVED = (0xB3, 0xA7, 0x93)


def fill(buf, width, height, contours, colour):
    """
    Even-odd scanline fill of a contour set into an RGB bytearray.

    Even-odd rather than nonzero because that is what OpenSCAD applies to a
    polygon() with several paths, which is how counters become holes.
    """
    if not contours:
        return
    ys = [p[1] for c in contours for p in c]
    y_start = max(0, int(min(ys)))
    y_end = min(height - 1, int(max(ys)) + 1)
    colour = bytes(colour)

    for y in range(y_start, y_end + 1):
        scan = y + 0.5
        crossings = []
        for contour in contours:
            count = len(contour)
            for i in range(count):
                x1, y1 = contour[i]
                x2, y2 = contour[(i + 1) % count]
                if (y1 > scan) != (y2 > scan):
                    crossings.append(x1 + (scan - y1) * (x2 - x1) / (y2 - y1))
        crossings.sort()
        row = y * width * 3
        for i in range(0, len(crossings) - 1, 2):
            xa = max(0, int(crossings[i] + 0.5))
            xb = min(width - 1, int(crossings[i + 1] - 0.5))
            if xb >= xa:
                buf[row + xa * 3:row + (xb + 1) * 3] = colour * (xb - xa + 1)


def downsample(buf, width, height, factor):
    """
    Box-filter the supersampled buffer down, which is what antialiases the edges.
    """
    out_w, out_h = width // factor, height // factor
    out = bytearray(out_w * out_h * 3)
    inv = 1.0 / (factor * factor)
    for oy in range(out_h):
        for ox in range(out_w):
            r = g = b = 0
            for dy in range(factor):
                base = ((oy * factor + dy) * width + ox * factor) * 3
                for dx in range(factor):
                    o = base + dx * 3
                    r += buf[o]
                    g += buf[o + 1]
                    b += buf[o + 2]
            o = (oy * out_w + ox) * 3
            out[o] = int(r * inv)
            out[o + 1] = int(g * inv)
            out[o + 2] = int(b * inv)
    return out, out_w, out_h


def write_png(path, buf, width, height):
    """
    Write a minimal 8-bit RGB PNG. No filtering: the images are small and the
    point is to depend on nothing.
    """
    raw = b''.join(b'\x00' + bytes(buf[y * width * 3:(y + 1) * width * 3])
                   for y in range(height))

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9))
                + chunk(b'IEND', b''))


class Renderer:
    def __init__(self, card):
        self.card = card
        self.width = int(card.card_length * PX_PER_MM) * SUPERSAMPLE
        self.height = int(card.card_width * PX_PER_MM) * SUPERSAMPLE
        self.scale = PX_PER_MM * SUPERSAMPLE

        title_width = card.outliner.text_width(card.title, card.title_font_size)
        self.placements = [(card.title, card.title_font_size,
                            (card.card_length / 2) - (title_width / 2),
                            card.card_width - card.margin - card.title_font_size)]
        self.placements += [(label, card.base_font_size, x, y)
                            for _, label, x, y in card.layout()]

    def _to_px(self, points, dx, dy):
        # y is flipped: millimetres go up, image rows go down.
        return [((x + dx) * self.scale, self.height - (y + dy) * self.scale)
                for x, y in points]

    def _blank(self, colour):
        return bytearray(bytes(colour) * (self.width * self.height))

    def _plate(self, buf, colour):
        fill(buf, self.width, self.height,
             [self._to_px([(0, 0), (self.card.card_length, 0),
                           (self.card.card_length, self.card.card_width),
                           (0, self.card.card_width)], 0, 0)], colour)

    def _text(self, buf, colour):
        for text, size, dx, dy in self.placements:
            fill(buf, self.width, self.height,
                 [self._to_px(c, dx, dy)
                  for c in self.card.outliner.contours(text, size)], colour)

    def _bridges(self, buf, colour):
        for text, size, dx, dy in self.placements:
            for x0, y0, x1, y1 in self.card.outliner.counter_bridges(
                    text, size, self.card.bridge_width):
                fill(buf, self.width, self.height,
                     [self._to_px([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dx, dy)],
                     colour)

    def engraved(self):
        """Une seule pièce, texte en creux : l'ombre du sillon tient lieu de contraste."""
        buf = self._blank(VOID)
        self._plate(buf, LIGHT)
        self._text(buf, ENGRAVED)
        return buf

    def single(self):
        """Monobloc : changement de filament, lettres en relief et intactes."""
        buf = self._blank(VOID)
        self._plate(buf, DARK)
        self._text(buf, LIGHT)
        return buf

    def base(self):
        """Socle de l'assemblage : mêmes lettres, mais encochées par les ponts."""
        buf = self._blank(VOID)
        self._plate(buf, DARK)
        self._text(buf, LIGHT)
        self._bridges(buf, DARK)
        return buf

    def counter(self):
        """Contre-plaque seule : les perçages laissent voir à travers."""
        buf = self._blank(VOID)
        self._plate(buf, DARK)
        self._text(buf, VOID)
        self._bridges(buf, DARK)
        return buf

    def save(self, buf, path):
        small, w, h = downsample(buf, self.width, self.height, SUPERSAMPLE)
        write_png(path, small, w, h)
        print(f"Save preview to {path}")


def main(key_path, title, out_dir):
    renderer = Renderer(CardDessing(WordManager(key_path), title))
    # Un PNG par .scad produit par make_sample.sh, même racine de nom.
    for name, build in (('card', renderer.engraved),
                        ('card_contrast.single', renderer.single),
                        ('card_contrast.base', renderer.base),
                        ('card_contrast.counter', renderer.counter)):
        renderer.save(build(), os.path.join(out_dir, f"{name}.png"))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
