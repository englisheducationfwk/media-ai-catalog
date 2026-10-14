#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор apple-touch-icon.png (180x180) без внешних зависимостей.

Рисует скруглённый квадрат с фиолетово-маджентовым градиентом и белой
4-конечной «звёздочкой» — иконка для домашнего экрана iPhone.

Использование:
    python _tools/make_icon.py
"""
import math
import os
import struct
import sys
import zlib

SIZE = 180
SS = 3  # супер-сэмплинг для сглаживания
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'apple-touch-icon.png')

C1 = (124, 108, 255)   # #7c6cff
C2 = (180, 92, 255)    # #b45cff


def blend(c1, c2, t):
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def inside_round_rect(x, y, w, h, r):
    """Точка внутри скруглённого прямоугольника (x,y — координаты центра пикселя)."""
    cx = min(max(x, r), w - r)
    cy = min(max(y, r), h - r)
    if r <= x <= w - r or r <= y <= h - r:
        return 0 <= x <= w and 0 <= y <= h
    dx = x - cx
    dy = y - cy
    return dx * dx + dy * dy <= r * r


def star_val(x, y, cx, cy, r, power=0.55):
    """4-конечная звезда: |dx|^p + |dy|^p <= r^p. Возвращает 1 внутри, 0 снаружи."""
    dx = abs(x - cx) / r
    dy = abs(y - cy) / r
    return 1 if (dx ** power + dy ** power) <= 1.0 else 0


def render():
    big = SIZE * SS
    # аккумулятор RGB(A) вниз, усредняем
    rows = []
    for py in range(SIZE):
        row = []
        for px in range(SIZE):
            rs = gs = bs = as_ = 0
            for sy in range(SS):
                for sx in range(SS):
                    x = px * SS + sx + 0.5
                    y = py * SS + sy + 0.5
                    if not inside_round_rect(x, y, big, big, 40 * SS):
                        continue
                    t = (x + y) / (2.0 * big)
                    r, g, b = blend(C1, C2, t)
                    # центральный блик
                    dx = (x - big / 2) / big
                    dy = (y - big / 2) / big
                    glow = max(0.0, 1.0 - (dx * dx + dy * dy) * 2.4) * 26
                    r = min(255, int(r + glow))
                    g = min(255, int(g + glow))
                    b = min(255, int(b + glow))
                    # большая звезда по центру
                    if star_val(x, y, big / 2, big / 2 + 6 * SS, 62 * SS):
                        r = g = b = 255
                    # маленькая звёздочка справа сверху
                    elif star_val(x, y, big / 2 + 46 * SS, big / 2 - 46 * SS, 22 * SS, 0.62):
                        r, g, b = blend((r, g, b), (255, 255, 255), 0.92)
                    rs += r
                    gs += g
                    bs += b
                    as_ += 255
            n = SS * SS
            row.append((rs // n, gs // n, bs // n, as_ // n))
        rows.append(row)
    return rows


def write_png(path, rows):
    raw = b''
    for row in rows:
        raw += b'\x00' + bytes(v for p in row for v in p)

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data
                + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack('>IIBBBBB', SIZE, SIZE, 8, 6, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)


def main():
    rows = render()
    write_png(OUT, rows)
    print('OK: иконка %s (%.0f КБ)' % (OUT, os.path.getsize(OUT) / 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
