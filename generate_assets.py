import os
import math
from PIL import Image, ImageEnhance, ImageOps

def create_puzzle_sprites():
    puzzle_dir = os.path.join('sprite', 'puzzle')
    os.makedirs(puzzle_dir, exist_ok=True)
    
    trippy_path = os.path.join('sprite', 'Trippy.png')
    if not os.path.exists(trippy_path):
        print(f"Error: {trippy_path} not found.")
        return
        
    base_img = Image.open(trippy_path).convert('RGBA')
    # Resize to standard size (e.g. 256x256) for tile asset
    tile_size = (256, 256)
    base_resized = base_img.resize(tile_size, Image.LANCZOS)
    
    # We will produce 6 color variations for puzzle tiles
    # Hues / color tints: Red, Blue, Green, Yellow, Purple, Orange
    tint_colors = [
        (255, 80, 80),    # Red
        (80, 160, 255),   # Blue
        (80, 220, 100),   # Green
        (255, 220, 60),   # Yellow
        (200, 100, 255),  # Purple
        (255, 140, 40)    # Orange
    ]
    
    for i, color in enumerate(tint_colors):
        # Create a tinted version of Trippy
        # Convert base image to grayscale and colorize with target tint
        gray = ImageOps.grayscale(base_resized)
        tinted = ImageOps.colorize(gray, black=(10, 10, 20), white=color)
        tinted = tinted.convert('RGBA')
        
        # Preserve original alpha mask if any
        alpha = base_resized.split()[3]
        tinted.putalpha(alpha)
        
        # Add a subtle glowing rounded border / icon container
        icon_canvas = Image.new('RGBA', tile_size, (0, 0, 0, 0))
        
        # Draw tinted image inside
        icon_canvas.paste(tinted, (0, 0), tinted)
        
        out_name = f'trippy_{i}.png'
        out_path = os.path.join(puzzle_dir, out_name)
        icon_canvas.save(out_path, 'PNG')
        print(f"Saved {out_path}")

if __name__ == '__main__':
    create_puzzle_sprites()
