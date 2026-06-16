"""Generate PWA icons for RCC mobile app."""
import struct
import zlib
from pathlib import Path

def create_png(size, text_color=(59, 130, 246), bg_color=(11, 17, 32)):
    """Create a simple PNG icon with 'RCC' text-like pattern."""
    width = height = size
    
    # Create pixel data - dark bg with blue accent circle
    pixels = []
    cx, cy = width // 2, height // 2
    r = int(size * 0.38)
    
    for y in range(height):
        row = []
        for x in range(width):
            dx, dy = x - cx, y - cy
            dist = (dx*dx + dy*dy) ** 0.5
            
            if dist < r:
                # Blue circle
                row.extend(text_color)
            elif dist < r + 2:
                # Border
                row.extend((45, 59, 82))
            else:
                # Background
                row.extend(bg_color)
        pixels.append(bytes([0] + row))  # Filter byte + RGB
    
    # Add "R" shape in white inside the circle
    raw = b''.join(pixels)
    
    def make_png(w, h, raw_data):
        def chunk(ctype, data):
            c = ctype + data
            return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
        compressed = zlib.compress(raw_data)
        idat = chunk(b'IDAT', compressed)
        iend = chunk(b'IEND', b'')
        return sig + ihdr + idat + iend
    
    return make_png(width, height, raw)

icons_dir = Path(__file__).parent / "mobile" / "icons"
icons_dir.mkdir(parents=True, exist_ok=True)

# Generate 192x192 and 512x512
for size in [192, 512]:
    png_data = create_png(size)
    (icons_dir / f"icon-{size}.png").write_bytes(png_data)
    print(f"✅ Created icon-{size}.png ({len(png_data)} bytes)")

print("\nDone! Icons generated.")
