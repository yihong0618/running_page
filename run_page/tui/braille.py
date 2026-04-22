"""Braille canvas for rendering polylines as braille art."""

import polyline

# Braille dot bit patterns — (col, row) in a 2x4 grid
_DOT_BITS = {
    (0, 0): 0x01,
    (0, 1): 0x02,
    (0, 2): 0x04,
    (0, 3): 0x40,
    (1, 0): 0x08,
    (1, 1): 0x10,
    (1, 2): 0x20,
    (1, 3): 0x80,
}

_BRAILLE_BASE = 0x2800


class BrailleCanvas:
    """A 2-dot × 4-dot-per-character canvas for line rendering."""

    def __init__(self, width_chars: int, height_chars: int):
        self.w = width_chars * 2
        self.h = height_chars * 4
        self.dots = bytearray(self.w * self.h)

    def _set(self, x: int, y: int) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.dots[y * self.w + x] = 1

    def draw_line(self, x0: int, y0: int, x1: int, y1: int) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            self._set(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def to_lines(self) -> list[str]:
        lines: list[str] = []
        for cy in range(0, self.h, 4):
            chars: list[str] = []
            for cx in range(0, self.w, 2):
                pattern = 0
                for dy in range(4):
                    for dx in (0, 1):
                        px = cx + dx
                        py = cy + dy
                        if px < self.w and py < self.h and self.dots[py * self.w + px]:
                            pattern |= _DOT_BITS.get((dx, dy), 0)
                chars.append(chr(_BRAILLE_BASE + pattern))
            lines.append("".join(chars))
        return lines


def render_polyline(
    polyline_str: str, width_chars: int, height_chars: int
) -> list[str]:
    """Render an encoded polyline as braille-art lines.

    Returns a list of strings, one per character-row of the terminal.
    """
    coords = polyline.decode(polyline_str)
    if not coords or len(coords) < 2:
        return [f"  (route has {len(coords)} point(s))"]

    lats = [c[0] for c in coords]
    lngs = [c[1] for c in coords]
    min_lat, max_lat = min(lats), max(lats)
    min_lng, max_lng = min(lngs), max(lngs)

    lat_rng = max_lat - min_lat or 0.001
    lng_rng = max_lng - min_lng or 0.001
    pad_lat = lat_rng * 0.1
    pad_lng = lng_rng * 0.1
    min_lat -= pad_lat
    max_lat += pad_lat
    min_lng -= pad_lng
    max_lng += pad_lng
    lat_rng = max_lat - min_lat
    lng_rng = max_lng - min_lng

    canvas = BrailleCanvas(width_chars, height_chars)
    w_dots = canvas.w
    h_dots = canvas.h

    def sx(lng: float) -> int:
        return int((lng - min_lng) / lng_rng * (w_dots - 1))

    def sy(lat: float) -> int:
        return int((max_lat - lat) / lat_rng * (h_dots - 1))

    for i in range(len(coords) - 1):
        canvas.draw_line(
            sx(coords[i][1]),
            sy(coords[i][0]),
            sx(coords[i + 1][1]),
            sy(coords[i + 1][0]),
        )

    return canvas.to_lines()
