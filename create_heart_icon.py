#!/usr/bin/env python3
"""
Create heart emoji icon for Apple Health Monitor Dashboard
Generates ICO file with multiple resolutions from emoji
"""

import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_heart_icon():
    """Create heart emoji icon with multiple resolutions."""
    # Icon sizes required for Windows ICO
    sizes = [16, 32, 48, 64, 128, 256]
    
    # Create images for each size
    images = []
    
    for size in sizes:
        # Create transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Use heart emoji - we'll use a red filled heart shape
        # Since emoji rendering is complex, we'll draw a heart shape
        
        # Calculate heart dimensions
        margin = size * 0.1
        heart_size = size - (2 * margin)
        
        # Heart shape using bezier curves approximation
        # Top center
        cx = size / 2
        cy = size / 2
        
        # Scale factor
        s = heart_size / 100.0
        
        # Heart path points (scaled)
        points = []
        
        # Draw heart using polygon approximation
        # Left lobe
        for t in range(0, 180, 10):
            import math
            rad = math.radians(t)
            x = cx - 25 * s + 25 * s * math.cos(rad)
            y = cy - 30 * s + 25 * s * math.sin(rad)
            points.append((x, y))
        
        # Right lobe  
        for t in range(180, 360, 10):
            import math
            rad = math.radians(t)
            x = cx + 25 * s + 25 * s * math.cos(rad)
            y = cy - 30 * s + 25 * s * math.sin(rad)
            points.append((x, y))
        
        # Bottom point
        points.append((cx, cy + 40 * s))
        
        # Draw filled heart
        draw.polygon(points, fill=(255, 69, 58, 255))  # Apple Health red color
        
        # Add slight gradient/glow effect for larger sizes
        if size >= 48:
            # Create a slightly larger heart for glow
            glow_points = []
            for px, py in points:
                # Expand points outward from center
                dx = px - cx
                dy = py - cy
                glow_points.append((px + dx * 0.05, py + dy * 0.05))
            
            # Draw glow
            for i in range(3):
                alpha = 30 - i * 10
                glow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_img)
                glow_draw.polygon(glow_points, fill=(255, 69, 58, alpha))
                img = Image.alpha_composite(glow_img, img)
        
        images.append(img)
    
    # Also create PNG versions for each size
    for size, img in zip(sizes, images):
        img.save(f'assets/heart_icon_{size}x{size}.png', 'PNG')
    
    # Save as ICO with all sizes
    images[0].save('assets/heart_icon.ico', format='ICO', 
                   sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    
    print("Heart emoji icon created successfully!")
    print("Files created:")
    print("  - assets/heart_icon.ico (multi-resolution)")
    for size in sizes:
        print(f"  - assets/heart_icon_{size}x{size}.png")

if __name__ == '__main__':
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Installing Pillow for icon generation...")
        import subprocess
        subprocess.check_call(["pip", "install", "Pillow"])
        from PIL import Image, ImageDraw
    
    create_heart_icon()