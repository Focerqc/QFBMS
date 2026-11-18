"""Warp the reference pictures into rev A's board frame for the Board Boxes compare view.

Each picture is warped so the 130 x 32 mm board outline lands on a fixed rectangle
(PX_PER_MM pixels per mm, MARGIN_MM around it), the same frame the visual model's render
is drawn in. The corners below are where the board outline's corners sit in each source
picture, in source pixels, listed as the board's top-left, top-right, bottom-right and
bottom-left in KiCad coordinates (top-left = the CHG+ XT30 corner).

Writes rev-a/compare/*.png and rev-a/qfbms-rev-a-visual.compare.json.
Run from the repo root: python rev-a/tools/make_compare_images.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'rev-a' / 'compare'
MANIFEST = ROOT / 'rev-a' / 'qfbms-rev-a-visual.compare.json'
BOARD_MM = (130.0, 32.0)
PX_PER_MM = 20
MARGIN_MM = 4.0

SOURCES = [
    dict(name='v1_0_photo.png', label='Real board · V1.0 photo',
         source='_reference/vfbms32_v1_0_photo.webp', background=(0, 0, 0),
         corners=[(47, 250), (998, 244), (1002, 478), (47, 482)]),
    # The diagram shows the board upright (XT30s at the top), so its corners run down the right edge first.
    dict(name='v1_1_wiring.png', label='32s wiring diagram · V1.1 board',
         source='_reference/vfbms32_wiring_32s_best.jpg', background=(255, 255, 255),
         corners=[(814, 178), (814, 892), (638, 892), (638, 178)]),
]


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points dst onto input points src."""
    a, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        a += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        b += [u, v]
    return np.linalg.solve(np.array(a, float), np.array(b, float)).tolist()


def main():
    OUT.mkdir(exist_ok=True)
    m = MARGIN_MM * PX_PER_MM
    w, h = BOARD_MM[0] * PX_PER_MM, BOARD_MM[1] * PX_PER_MM
    size = (round(w + 2 * m), round(h + 2 * m))
    board = [m, m, m + w, m + h]
    dst = [(board[0], board[1]), (board[2], board[1]), (board[2], board[3]), (board[0], board[3])]
    images = []
    for s in SOURCES:
        src = Image.open(ROOT / s['source']).convert('RGB')
        out = src.transform(size, Image.PERSPECTIVE, perspective_coeffs(dst, s['corners']), Image.BICUBIC,
                            fillcolor=s['background'])
        out.save(OUT / s['name'], optimize=True)
        images.append(dict(label=s['label'], path=f"rev-a/compare/{s['name']}", source=s['source'], board=board))
        print('wrote', OUT / s['name'], size)
    MANIFEST.write_text(json.dumps(dict(
        note='Reference pictures warped into the board frame. Made by rev-a/tools/make_compare_images.py.',
        boardMm=list(BOARD_MM), images=images), indent=1) + '\n', encoding='utf-8')
    print('wrote', MANIFEST)


if __name__ == '__main__':
    main()
