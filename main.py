#!/usr/bin/env python3
"""news-image-20261126 - one-day world news front page, Thursday 26 November 2026.

Pure Python 3 standard library. Draws a 1024x1024 PNG newspaper front page
with a hand-built 5x7 bitmap font and a minimal PNG encoder (zlib + struct).
No network, no external assets, no timestamps, no randomness: two runs write
identical bytes.

Stories (verified against Reuters / BBC / CNA reporting of 26 Nov 2026):
 1. US proposes new tariffs on 14 trading partners (China highest; India up
    to 25%, Taiwan up to 15%).
 2. Houthis claim a strike on Saudi Arabia's Ras Tanura refinery; Brent
    crude settles at $94.61, up 3.5%.
 3. Kim Jong Un orders wider deployment of tactical nuclear weapons; calls
    the North's nuclear status irreversible (KCNA, reported Thu 26 Nov).
 4. Ukraine says it struck Russia's Savasleyka air base, damaging five planes.
 5. Israeli judges recommend dropping the most serious charges against
    Benjamin Netanyahu.
 6. Thanksgiving in America: New York postpones its parade over a major
    storm; wholesale turkey prices at a record $2/lb.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
PAPER = (246, 241, 227)   # newsprint off-white
INK = (22, 22, 22)        # near-black
RED = (163, 22, 33)       # headline accent
NAVY = (31, 58, 95)       # section accent
GRAY = (110, 104, 90)     # muted rules / captions
LIGHT = (232, 226, 208)   # panel fill
ORANGE = (214, 106, 24)   # flame
GOLD = (198, 148, 44)     # chart accent
WHITE = (255, 255, 255)

# ------------------------------------------------------------- 5x7 font -----
# Each glyph: 7 rows of 5 bits, '1' = ink. Covers printable ASCII 32..126.
FONT = {
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '*': ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    ',': ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "00100", "00100"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ':': ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    ';': ("00000", "00100", "00000", "00000", "00100", "00100", "01000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    '\\': ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '^': ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '`': ("00100", "00100", "00010", "00000", "00000", "00000", "00000"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    'q': ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '{': ("00010", "00100", "00100", "01100", "00100", "00100", "00010"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    '}': ("01000", "00100", "00100", "00110", "00100", "00100", "01000"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
}

# ------------------------------------------------------------ PNG encoder ---
def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(w, h, rgb):
    """Deterministic RGB PNG: fixed header, single zlib stream, no ancillary."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter: none
        raw += rgb[y * w * 3:(y + 1) * w * 3]
    comp = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", comp)
    png += _chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------- canvas ---
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, rw, rh, color):
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + rw, self.w), min(y + rh, self.h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(i + (x1 - x0) * 3)] = bytes(color) * (x1 - x0)

    def hline(self, x, y, length, color, thick=1):
        self.rect(x, y, length, thick, color)

    def vline(self, x, y, length, color, thick=1):
        self.rect(x, y, thick, length, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for ox in range(thick):
                for oy in range(thick):
                    self.put(x0 + ox - thick // 2, y0 + oy - thick // 2, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick <= d <= r:
                    self.put(xx, yy, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)

        def sign(ax, ay, bx, by, cx, cy):
            return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

        d = sign(x0, y0, x1, y1, x2, y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                d0 = sign(xx, yy, x0, y0, x1, y1)
                d1 = sign(xx, yy, x1, y1, x2, y2)
                d2 = sign(xx, yy, x2, y2, x0, y0)
                if (d > 0 and d0 >= 0 and d1 >= 0 and d2 >= 0) or \
                   (d < 0 and d0 <= 0 and d1 <= 0 and d2 <= 0):
                    self.put(xx, yy, color)

    # ---------------------------------------------------------------- text --
    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, s, scale, color):
        self.text(cx - self.text_width(s, scale) // 2, y, s, scale, color)

    def wrap(self, s, scale, max_w):
        """Greedy word wrap; returns list of lines that fit max_w."""
        words = s.split(" ")
        lines, cur = [], ""
        for wd in words:
            trial = wd if not cur else cur + " " + wd
            if self.text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def paragraph(self, x, y, s, scale, color, max_w, leading=None):
        lh = leading if leading is not None else 9 * scale
        for ln in self.wrap(s, scale, max_w):
            self.text(x, y, ln, scale, color)
            y += lh
        return y

# ------------------------------------------------------------- illustrations -
def draw_globe(c, cx, cy, r):
    c.ring(cx, cy, r, INK, 3)
    c.vline(cx, cy - r, 2 * r, INK, 2)
    c.hline(cx - r, cy, 2 * r, INK, 2)
    # latitude arcs (approximated with short horizontal chords)
    for dy, half in ((-r // 2, 26), (r // 2, 26)):
        c.hline(cx - half * r // 30, cy + dy, 2 * half * r // 30, INK, 2)


def draw_tariff_chart(c, x, y, w, h):
    """Bar chart: China highest (no number published), India 25%, Taiwan 15%."""
    c.rect(x, y, w, h, WHITE)
    c.rect(x, y, w, 2, INK)
    c.rect(x, y + h - 2, w, 2, INK)
    c.rect(x, y, 2, h, INK)
    c.rect(x + w - 2, y, 2, h, INK)
    c.text_center(x + w // 2, y + 10, "WHO PAYS THE MOST?", 2, INK)
    base = y + h - 62
    c.hline(x + 24, base, w - 48, INK, 2)
    bars = [("CHINA", "HIGHEST", 110, RED),
            ("INDIA", "25%", 76, NAVY),
            ("TAIWAN", "15%", 46, GOLD)]
    bw = 62
    gap = (w - 48 - 3 * bw) // 4
    bx = x + 24 + gap
    for name, val, bh, col in bars:
        c.rect(bx, base - bh, bw, bh, col)
        c.text_center(bx + bw // 2, base - bh - 18, val, 2, INK)
        c.text_center(bx + bw // 2, base + 8, name, 2, INK)
        bx += bw + gap
    c.text_center(x + w // 2, y + h - 26,
                  "Proposed 25 Nov; China highest", 2, GRAY)


def draw_refinery(c, x, y, w, h):
    c.rect(x, y, w, h, LIGHT)
    gy = y + h - 8
    c.hline(x + 8, gy, w - 16, INK, 2)
    # towers
    c.rect(x + 30, gy - 20, 14, 20, INK)
    c.rect(x + 56, gy - 26, 12, 26, NAVY)
    c.rect(x + 80, gy - 16, 20, 16, INK)
    # flame over middle tower
    c.triangle(x + 56, gy - 38, x + 50, gy - 26, x + 68, gy - 26, ORANGE)
    c.triangle(x + 60, gy - 32, x + 56, gy - 26, x + 64, gy - 26, RED)
    # storage tank
    c.rect(x + 112, gy - 16, 34, 16, INK)
    c.text(x + 170, y + 8, "RAS TANURA", 2, INK)
    c.text(x + 170, y + 26, "BRENT $94.61", 2, RED)


def draw_missile(c, x, y, w, h):
    c.rect(x, y, w, h, LIGHT)
    mx = x + 60
    # body
    c.rect(mx - 7, y + 12, 14, 26, NAVY)
    c.triangle(mx, y + 2, mx - 7, y + 12, mx + 7, y + 12, NAVY)
    c.triangle(mx - 7, y + 38, mx - 14, y + 46, mx - 7, y + 38, NAVY)
    c.triangle(mx + 7, y + 38, mx + 14, y + 46, mx + 7, y + 38, NAVY)
    # exhaust
    c.triangle(mx, y + h - 4, mx - 5, y + 38, mx + 5, y + 38, ORANGE)
    # motion lines
    for yy in (y + 10, y + 20, y + 30):
        c.hline(x + 90, yy, 26, GRAY, 2)
    c.text(x + 130, y + 8, "TACTICAL", 2, INK)
    c.text(x + 130, y + 26, "NUCLEAR", 2, RED)


def draw_jets(c, x, y, w, h):
    c.rect(x, y, w, h, LIGHT)
    # two jets: delta wings + fuselage
    for jx, jy in ((x + 40, y + 14), (x + 110, y + 26)):
        c.triangle(jx, jy, jx + 26, jy + 6, jx, jy + 12, NAVY)
        c.rect(jx + 24, jy + 4, 14, 4, NAVY)
        c.hline(jx - 26, jy + 6, 24, GRAY, 2)
    # starburst (impact)
    sx, sy = x + 200, y + 22
    for dx, dy in ((0, -12), (9, -9), (12, 0), (9, 9), (0, 12),
                   (-9, 9), (-12, 0), (-9, -9)):
        c.line(sx, sy, sx + dx, sy + dy, RED, 2)
    c.text(x + 230, y + 8, "5 PLANES", 2, INK)
    c.text(x + 230, y + 26, "DAMAGED", 2, RED)


def draw_court(c, x, y, w, h):
    c.rect(x, y, w, h, LIGHT)
    cx = x + 70
    gy = y + h - 8
    # pediment + columns + base
    c.triangle(cx - 44, y + 12, cx + 44, y + 12, cx, y + 2, INK)
    for ox in (-30, -10, 10, 30):
        c.rect(cx + ox - 3, y + 14, 6, 22, INK)
    c.hline(cx - 44, y + 36, 88, INK, 2)
    c.hline(cx - 44, gy - 2, 88, INK, 2)
    # scales of justice
    sx = x + 190
    c.vline(sx, y + 8, 28, INK, 2)
    c.hline(sx - 14, y + 8, 28, INK, 2)
    c.line(sx - 14, y + 8, sx - 18, y + 20, INK, 2)
    c.line(sx + 14, y + 8, sx + 18, y + 20, INK, 2)
    c.triangle(sx - 22, y + 20, sx - 14, y + 20, sx - 18, y + 26, INK)
    c.triangle(sx + 14, y + 20, sx + 22, y + 20, sx + 18, y + 26, INK)
    c.text(x + 240, y + 8, "COURT", 2, INK)
    c.text(x + 240, y + 26, "JERUSALEM", 2, GRAY)


def draw_storm(c, x, y, w, h):
    # storm cloud + rain, right side of the Thanksgiving strip
    cx, cy = x + w // 2, y + h // 2 - 4
    c.circle(cx - 22, cy, 16, NAVY)
    c.circle(cx, cy - 8, 19, NAVY)
    c.circle(cx + 22, cy, 16, NAVY)
    c.rect(cx - 38, cy, 76, 12, NAVY)
    for i, ox in enumerate((-28, -10, 8, 26)):
        c.line(cx + ox, cy + 16, cx + ox - 4, cy + 28, ORANGE, 2)


# ------------------------------------------------------------------- page ----
def build():
    c = Canvas(W, H, PAPER)
    MX = 40                      # side margin
    CW = W - 2 * MX              # content width = 944

    # --- masthead ------------------------------------------------------
    c.hline(MX, 20, CW, INK, 3)
    draw_globe(c, 98, 62, 28)
    c.text_center(W // 2, 34, "THE WORLD TODAY", 8, INK)
    c.text_center(W // 2, 96, "ONE DAY  |  ONE PAGE  |  THE NEWS THAT MATTERED",
                  2, GRAY)
    c.hline(MX, 118, CW, INK, 2)

    # --- date bar ------------------------------------------------------
    c.rect(MX, 128, CW, 32, INK)
    c.text(MX + 16, 137, "THURSDAY, 26 NOVEMBER 2026", 2, WHITE)
    right = "SIX STORIES THAT SHAPED THE DAY"
    c.text(MX + CW - 16 - c.text_width(right, 2), 137, right, 2, WHITE)

    # --- lead story: US tariffs ---------------------------------------
    c.text(MX, 176, "TRADE  -  WASHINGTON", 2, RED)
    c.text(MX, 198, "US PROPOSES NEW TARIFFS", 4, INK)
    c.text(MX, 230, "ON 14 TRADING PARTNERS", 4, INK)
    lead = ("Washington proposed tariffs on 14 major trading partners to "
            "fight what it calls excess factory capacity. China faces the "
            "highest rates. India would pay up to 25%, Taiwan up to 15%.")
    c.paragraph(MX, 272, lead, 2, INK, 520, leading=19)
    c.text(MX, 372, "S&P 500 FUTURES -2.1% | NASDAQ FUTURES -3.1%",
           2, GRAY)
    draw_tariff_chart(c, 600, 176, 384, 220)

    c.hline(MX, 412, CW, INK, 3)

    # --- grid of four stories -----------------------------------------
    col_w = 450
    cols = [MX, MX + col_w + 44]
    rows = [428, 650]
    stories = [
        ("ENERGY  -  MIDDLE EAST",
         ["HOUTHIS CLAIM STRIKE", "ON SAUDI REFINERY"],
         "Yemen's Houthis said they hit Ras Tanura, Saudi Arabia's biggest "
         "refinery. Riyadh said it downed four drones. Brent: $94.61, "
         "up 3.5%.",
         draw_refinery),
        ("ASIA  -  NORTH KOREA",
         ["KIM ORDERS WIDER", "NUCLEAR DEPLOYMENT"],
         "Kim Jong Un ordered tactical nuclear weapons deployed more widely, "
         "calling the North's nuclear status irreversible, KCNA reported "
         "Thursday.",
         draw_missile),
        ("WAR IN UKRAINE",
         ["UKRAINE SAYS IT HIT", "RUSSIAN AIR BASE"],
         "Kyiv said its forces struck the Savasleyka air base in Russia, "
         "damaging five planes used to launch missiles and glide bombs at "
         "Ukraine.",
         draw_jets),
        ("ISRAEL",
         ["JUDGES URGE DROPPING", "TOP NETANYAHU CHARGES"],
         "Israeli judges recommended dropping the most serious charges "
         "against Prime Minister Benjamin Netanyahu in his long-running "
         "corruption trial.",
         draw_court),
    ]
    for i, (kicker, head, body, art) in enumerate(stories):
        x = cols[i % 2]
        y = rows[i // 2]
        c.text(x, y, kicker, 2, RED)
        hy = y + 20
        for ln in head:
            c.text(x, hy, ln, 3, INK)
            hy += 25
        c.paragraph(x, hy + 6, body, 2, INK, col_w, leading=17)
        art(c, x, y + 158, col_w, 46)

    # vertical divider between grid columns
    c.vline(MX + col_w + 22, 428, 424, GRAY, 1)
    # horizontal divider between grid rows
    c.hline(MX, 642, CW, GRAY, 1)

    # --- Thanksgiving strip -------------------------------------------
    c.hline(MX, 862, CW, INK, 2)
    c.text(MX, 874, "AMERICA  -  THANKSGIVING", 2, RED)
    c.text(MX, 896, "PARADE POSTPONED AS STORM HITS NEW YORK", 3, INK)
    thanks = ("New York postponed its Thanksgiving parade over a major "
              "storm. Grocers held deals as turkey hit a record $2 a pound.")
    c.paragraph(MX, 926, thanks, 2, INK, 780, leading=17)
    draw_storm(c, 800, 878, 160, 66)

    # --- markets ticker ------------------------------------------------
    c.rect(MX, 968, CW, 56, INK)
    t1 = "BRENT $94.61 +3.5%  |  WTI $83.68 +2%  |  NASDAQ -4%  |  NVIDIA -3.9% $149.30"
    t2 = "ANTHROPIC BELOW $83 IPO  |  BANK OF KOREA 3.25%  |  F-15EX IN OKINAWA"
    c.text_center(W // 2, 978, t1, 2, WHITE)
    c.text_center(W // 2, 998, t2, 2, WHITE)

    return encode_png(W, H, bytes(c.px))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
