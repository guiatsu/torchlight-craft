"""Create the project's small original geometric Windows icon from stdlib only."""

from __future__ import annotations

import struct
from pathlib import Path


def inside_polygon(x: float, y: float, points: list[tuple[float, float]]) -> bool:
    inside = False
    previous = points[-1]
    for current in points:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y):
            crossing = (x2 - x1) * (y - y1) / (y2 - y1) + x1
            if x < crossing:
                inside = not inside
        previous = current
    return inside


def icon_pixels(size: int) -> list[tuple[int, int, int, int]]:
    canvas = [(0, 0, 0, 0)] * (size * size)
    scale = size / 64
    center = (size - 1) / 2
    outer = [(center, 2 * scale), (size - 2 * scale, center), (center, size - 2 * scale), (2 * scale, center)]
    inner = [(center, 8 * scale), (size - 8 * scale, center), (center, size - 8 * scale), (8 * scale, center)]
    bolt = [(34 * scale, 12 * scale), (22 * scale, 35 * scale), (31 * scale, 35 * scale),
            (27 * scale, 52 * scale), (43 * scale, 28 * scale), (34 * scale, 28 * scale)]
    ring = [(center, 4 * scale), (size - 4 * scale, center), (center, size - 4 * scale), (4 * scale, center)]

    def paint(poly: list[tuple[float, float]], color: tuple[int, int, int, int]) -> None:
        for y in range(size):
            for x in range(size):
                if inside_polygon(x + 0.5, y + 0.5, poly):
                    canvas[y * size + x] = color

    paint(outer, (18, 40, 54, 255))
    paint(ring, (205, 165, 86, 255))
    paint(inner, (25, 47, 61, 255))
    paint(bolt, (238, 198, 107, 255))
    return canvas


def dib_image(size: int) -> bytes:
    pixels = icon_pixels(size)
    xor = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            red, green, blue, alpha = pixels[y * size + x]
            xor.extend((blue, green, red, alpha))
    mask_row_bytes = ((size + 31) // 32) * 4
    and_mask = bytearray(mask_row_bytes * size)
    for y in range(size):
        for x in range(size):
            if pixels[y * size + x][3] == 0:
                row = (size - 1 - y) * mask_row_bytes
                and_mask[row + x // 8] |= 1 << (7 - (x % 8))
    header = struct.pack(
        "<IIIHHIIIIII",
        40,
        size,
        size * 2,
        1,
        32,
        0,
        len(xor),
        0,
        0,
        0,
        0,
    )
    return header + xor + and_mask


def main() -> None:
    sizes = (16, 32, 48, 64)
    images = [dib_image(size) for size in sizes]
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    entries = bytearray()
    for size, image in zip(sizes, images, strict=True):
        entries.extend(
            struct.pack(
                "<BBBBHHII",
                size if size < 256 else 0,
                size if size < 256 else 0,
                0,
                0,
                1,
                32,
                len(image),
                offset,
            )
        )
        offset += len(image)
    output = Path(__file__).resolve().parents[1] / "assets" / "icons" / "planner-mark.ico"
    output.write_bytes(header + entries + b"".join(images))


if __name__ == "__main__":
    main()
