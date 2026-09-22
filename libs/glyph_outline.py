"""
Turn text into polygon contours, in millimetres.

This module exists to remove a reproducibility hazard. OpenSCAD's text() names a
font and lets the *renderer* resolve it through fontconfig, so the same .scad
produces different geometry on a machine with different fonts installed. For a
seed backup, regenerated years later on another machine, that means a silently
illegible card. Resolving the glyphs here, at generation time, makes the .scad
self-contained.

The module knows nothing about cards or OpenSCAD: it maps text to contours.
"""

import math
from collections import namedtuple

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

# 0.1 µm, far below anything an FDM printer resolves. Rounding matters because
# solid2 renders floats with repr(), so unrounded values reach the .scad as
# 17-digit noise: bigger files, unreadable diffs, no added precision.
COORD_DECIMALS = 4

Contour = namedtuple('Contour', 'points is_hole')
Glyph = namedtuple('Glyph', 'char origin_x advance contours bbox')


class MissingGlyphError(LookupError):
    """Raised when the font has no glyph for a character that must be engraved."""


class _FlattenPen(BasePen):
    """
    A pen that flattens every curve into line segments.

    Subdivision counts are derived from the control points and the tolerance, so
    the same text and tolerance always yield the same points. That determinism is
    what lets `git diff` stay empty when nothing has changed.
    """

    def __init__(self, glyph_set, tolerance_units):
        super().__init__(glyph_set)
        # Guard against a zero or negative tolerance, which would make the
        # segment counts below explode or go imaginary.
        self.tolerance = max(tolerance_units, 1e-9)
        self.contours = []
        self._current = []

    # -- BasePen interface --------------------------------------------------

    def _moveTo(self, pt):
        self._flush()
        self._current = [pt]

    def _lineTo(self, pt):
        self._current.append(pt)

    def _qCurveToOne(self, bcp, pt):
        p0 = self._current[-1]
        for t in self._steps(self._quad_segments(p0, bcp, pt)):
            self._current.append(self._quad_at(p0, bcp, pt, t))

    def _curveToOne(self, bcp1, bcp2, pt):
        p0 = self._current[-1]
        for t in self._steps(self._cubic_segments(p0, bcp1, bcp2, pt)):
            self._current.append(self._cubic_at(p0, bcp1, bcp2, pt, t))

    def _closePath(self):
        self._flush()

    def _endPath(self):
        self._flush()

    # -- flattening ---------------------------------------------------------

    @staticmethod
    def _steps(n):
        return [i / n for i in range(1, n + 1)]

    def _quad_segments(self, p0, p1, p2):
        # For a quadratic, the greatest deviation from the chord is
        # |p0 - 2*p1 + p2| / 8, and it falls as 1/n^2 under subdivision.
        d = math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1])
        return max(1, math.ceil(math.sqrt(d / (8 * self.tolerance))))

    def _cubic_segments(self, p0, p1, p2, p3):
        d = max(
            math.hypot(p0[0] - 2 * p1[0] + p2[0], p0[1] - 2 * p1[1] + p2[1]),
            math.hypot(p1[0] - 2 * p2[0] + p3[0], p1[1] - 2 * p2[1] + p3[1]),
        )
        return max(1, math.ceil(math.sqrt(3 * d / (4 * self.tolerance))))

    @staticmethod
    def _quad_at(p0, p1, p2, t):
        u = 1 - t
        return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])

    @staticmethod
    def _cubic_at(p0, p1, p2, p3, t):
        u = 1 - t
        a, b, c, d = u * u * u, 3 * u * u * t, 3 * u * t * t, t * t * t
        return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])

    def _flush(self):
        # A contour needs three distinct points to enclose an area. Anything
        # shorter is a degenerate artefact and would only confuse OpenSCAD.
        if len(self._current) >= 3:
            self.contours.append(self._current)
        self._current = []


def _point_in_polygon(point, polygon):
    """
    Even-odd ray casting. Used to decide which contours are counters.
    """
    x, y = point
    inside = False
    n = len(polygon)
    for i in range(n):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


class FontOutliner:
    """
    Resolve text into polygon contours using a specific font file.

    `font_size` is interpreted as the em size, the usual typographic meaning.
    Note that OpenSCAD's text() instead sizes by ascent, so the same numeric size
    renders smaller here than it did through text().
    """

    def __init__(self, font_path, font_number=0, flatten_tolerance=0.02):
        """
        Parameters:
            font_path (str): path to a .ttf/.otf file. A .ttc collection holds
                several faces, so font_number selects one. Beware that faces in
                one collection may differ in unitsPerEm, so a wrong index
                silently rescales everything.
            font_number (int): face index inside a .ttc collection.
            flatten_tolerance (float): maximum deviation, in millimetres, between
                a curve and the polyline replacing it.
        """
        self.font_path = font_path
        self.flatten_tolerance = flatten_tolerance
        self._font = TTFont(font_path, fontNumber=font_number, lazy=True)
        self._glyph_set = self._font.getGlyphSet()
        self._cmap = self._font.getBestCmap()
        self._hmtx = self._font['hmtx']
        self._units_per_em = self._font['head'].unitsPerEm

    def _glyph_name(self, char):
        name = self._cmap.get(ord(char))
        if name is None:
            # Engraving a .notdef box into a seed backup would be the worst
            # possible silent failure, so this is fatal rather than a warning.
            raise MissingGlyphError(
                f"La police {self.font_path} ne contient pas le caractère {char!r} "
                f"(U+{ord(char):04X}).")
        return name

    def advance(self, char, font_size):
        """
        Horizontal advance of a single character, in millimetres.
        """
        width, _ = self._hmtx[self._glyph_name(char)]
        return width * font_size / self._units_per_em

    def text_width(self, text, font_size):
        """
        Exact rendered width of a string, in millimetres.

        This replaces the previous per-character estimate, so the column overflow
        check is now measured rather than guessed.
        """
        return sum(self.advance(c, font_size) for c in text)

    def glyphs(self, text, font_size):
        """
        Lay out a string and return one Glyph per character that has outlines.

        Each Glyph carries its contours already translated along x, each flagged
        as outline or counter, plus the glyph's bounding box. Counters are what
        make the counter-plate of a two-colour card fall apart into loose
        islands, so callers need them identified, not merely present.

        Returns:
            list[Glyph]
        """
        scale = font_size / self._units_per_em
        # Flattening happens in font units, so convert the tolerance too.
        tolerance_units = self.flatten_tolerance / scale

        out = []
        pen_x = 0.0
        for char in text:
            name = self._glyph_name(char)
            advance = self._hmtx[name][0]

            pen = _FlattenPen(self._glyph_set, tolerance_units)
            self._glyph_set[name].draw(pen)

            raw = []
            for contour in pen.contours:
                points = self._clean([((x + pen_x) * scale, y * scale)
                                      for x, y in contour])
                if len(points) >= 3:
                    raw.append(points)

            if raw:
                contours = [Contour(points, self._is_hole(points, raw))
                            for points in raw]
                bbox = _bbox([p for points in raw for p in points])
                out.append(Glyph(char, pen_x * scale, advance * scale,
                                 contours, bbox))

            pen_x += advance
        return out

    @staticmethod
    def _clean(points):
        """
        Round to COORD_DECIMALS, then drop duplicates *created by* the rounding.

        Order matters: deduplicating first would leave zero-length edges behind,
        which OpenSCAD's CGAL backend complains about.
        """
        rounded = [(round(x, COORD_DECIMALS), round(y, COORD_DECIMALS))
                   for x, y in points]
        cleaned = [rounded[0]]
        for point in rounded[1:]:
            if point != cleaned[-1]:
                cleaned.append(point)
        while len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
            cleaned.pop()
        return cleaned

    @staticmethod
    def _is_hole(points, all_contours):
        """
        A contour is a counter when it sits inside an odd number of the others.
        """
        probe = points[0]
        depth = 0
        for other in all_contours:
            if other is points:
                continue
            if _point_in_polygon(probe, other):
                depth += 1
        return depth % 2 == 1

    def contours(self, text, font_size):
        """
        Flattened outlines of a string, in millimetres.

        The origin is the baseline at the start of the first glyph, matching the
        halign='left' valign='baseline' convention the cards already use.

        Returns:
            list[list[tuple[float, float]]]: one point list per closed contour.
            A glyph with a counter (o, a, e, 8) contributes several contours;
            OpenSCAD's even-odd rule turns the inner ones into holes.
        """
        return [contour.points
                for glyph in self.glyphs(text, font_size)
                for contour in glyph.contours]

    def counter_bridges(self, text, font_size, bridge_width, margin):
        """
        Rectangles tying every counter to the outside of its glyph.

        Without these, the counter-plate of a two-colour card is riddled with
        free-floating islands: the middle of every o, a, e, 8 is enclosed by its
        letter and connected to nothing, so it prints as a loose speck. A bar is
        run from each counter out through the shorter of the glyph's top or
        bottom edge, which is exactly how stencil typefaces solve the problem.

        Two properties the bar must have, both learnt the hard way from counting
        connected components in the exported mesh:

        - it spans the counter from edge to edge, not merely from its centre, so
          it cannot miss an island that the clearance has shrunk;
        - `margin` must comfortably exceed the counter-plate's clearance. The bar
          is unioned back after the letters have been cut *grown by clearance*,
          so an overlap of `margin - clearance` is all that actually holds the
          island. At 0.2 against a 0.15 clearance that left 0.05 mm and most
          islands came away. Overshooting into the field costs nothing: out
          there the bar unions with plate that is already solid.

        Parameters:
            margin (float): how far past the glyph's bounding box the bar runs.

        Returns:
            list[tuple[float, float, float, float]]: (x0, y0, x1, y1) per bar.
        """
        bars = []
        for glyph in self.glyphs(text, font_size):
            gx0, gy0, gx1, gy1 = glyph.bbox
            for contour in glyph.contours:
                if not contour.is_hole:
                    continue
                hx0, hy0, hx1, hy1 = _bbox(contour.points)
                cx = (hx0 + hx1) / 2
                half = bridge_width / 2
                # Break out through whichever edge is nearer, so the notch cut
                # into the letter stays as short as possible.
                if (gy1 - hy1) <= (hy0 - gy0):
                    bars.append((cx - half, hy0, cx + half, gy1 + margin))
                else:
                    bars.append((cx - half, gy0 - margin, cx + half, hy1))
        return bars

    def is_monospaced(self, sample="abcdefghijklmnopqrstuvwxyz0123456789 "):
        """
        Whether every sampled character shares one advance width.
        """
        widths = set()
        for char in sample:
            name = self._cmap.get(ord(char))
            if name is not None:
                widths.add(self._hmtx[name][0])
        return len(widths) == 1
