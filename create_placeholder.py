#!/usr/bin/env python3
"""Generate a simple PNG placeholder image"""
import struct
import zlib


def create_simple_png(filename, width=200, height=150, color=(224, 224, 224)):
    """Create a simple solid-color PNG file"""

    # PNG signature
    png_signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk (image header)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB
    ihdr_chunk = b"IHDR" + ihdr_data
    ihdr_crc = zlib.crc32(ihdr_chunk) & 0xFFFFFFFF
    ihdr = struct.pack(">I", 13) + ihdr_chunk + struct.pack(">I", ihdr_crc)

    # IDAT chunk (image data) - simple uniform color
    r, g, b = color
    scanline = (
        bytes([0]) + bytes([r, g, b]) * width
    )  # 0 = filter type, RGB for each pixel
    raw_data = scanline * height
    compressed = zlib.compress(raw_data)

    idat_chunk = b"IDAT" + compressed
    idat_crc = zlib.crc32(idat_chunk) & 0xFFFFFFFF
    idat = struct.pack(">I", len(compressed)) + idat_chunk + struct.pack(">I", idat_crc)

    # IEND chunk (end of image)
    iend_chunk = b"IEND"
    iend_crc = zlib.crc32(iend_chunk) & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + iend_chunk + struct.pack(">I", iend_crc)

    # Write PNG file
    png_data = png_signature + ihdr + idat + iend
    with open(filename, "wb") as f:
        f.write(png_data)

    print(f"Created {filename} ({len(png_data)} bytes)")


# Create placeholder
create_simple_png("app/static/img/placeholder.png")
