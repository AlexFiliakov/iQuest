#!/usr/bin/env python3
"""Create installer graphics for NSIS installer."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_installer_welcome_bitmap():
    """Create a 164x314 pixel welcome bitmap for NSIS installer."""
    # Create a new image with the required dimensions
    width, height = 164, 314
    img = Image.new('RGB', (width, height), color='#FFFFFF')
    draw = ImageDraw.Draw(img)
    
    # Draw a gradient background
    for y in range(height):
        # Create a gradient from light blue to white
        r = 240 + int(15 * (y / height))
        g = 248 + int(7 * (y / height))
        b = 255
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw a health monitor icon representation
    # Heart symbol
    heart_y = 80
    heart_size = 40
    # Simple heart shape using circles and polygon
    draw.ellipse([width//2 - 20, heart_y, width//2, heart_y + 20], fill='#FF6B6B')
    draw.ellipse([width//2, heart_y, width//2 + 20, heart_y + 20], fill='#FF6B6B')
    draw.polygon([(width//2 - 20, heart_y + 10), 
                  (width//2 + 20, heart_y + 10),
                  (width//2, heart_y + 35)], fill='#FF6B6B')
    
    # Draw heartbeat line
    line_y = heart_y + 15
    line_points = []
    x = 30
    for i in range(7):
        if i == 3:  # Peak
            line_points.extend([(x, line_y), (x + 5, line_y - 10), (x + 10, line_y + 10), (x + 15, line_y)])
            x += 15
        else:
            line_points.extend([(x, line_y)])
            x += 15
    
    if len(line_points) > 1:
        draw.line(line_points, fill='#FFFFFF', width=2)
    
    # Add text
    try:
        # Try to use a nice font, fallback to default if not available
        font_title = ImageFont.truetype("arial.ttf", 16)
        font_subtitle = ImageFont.truetype("arial.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
    
    # Title text
    text_title = "Apple Health"
    text_subtitle = "Monitor"
    
    # Center the text
    title_bbox = draw.textbbox((0, 0), text_title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    subtitle_bbox = draw.textbbox((0, 0), text_subtitle, font=font_subtitle)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    
    draw.text(((width - title_width) // 2, 150), text_title, fill='#2C3E50', font=font_title)
    draw.text(((width - subtitle_width) // 2, 170), text_subtitle, fill='#2C3E50', font=font_subtitle)
    
    # Add version text at bottom
    version_text = "Version 1.0"
    version_bbox = draw.textbbox((0, 0), version_text, font=font_subtitle)
    version_width = version_bbox[2] - version_bbox[0]
    draw.text(((width - version_width) // 2, 280), version_text, fill='#7F8C8D', font=font_subtitle)
    
    # Save the image
    output_path = os.path.join(os.path.dirname(__file__), 'installer_welcome.bmp')
    img.save(output_path, 'BMP')
    print(f"Created installer welcome bitmap: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Check if PIL/Pillow is available
    try:
        create_installer_welcome_bitmap()
    except ImportError:
        print("Pillow is required to create installer graphics.")
        print("Install with: pip install Pillow")
        
        # Create a placeholder file
        placeholder_path = os.path.join(os.path.dirname(__file__), 'installer_welcome.bmp')
        print(f"\nCreating placeholder at: {placeholder_path}")
        print("Replace this with a proper 164x314 pixel BMP image for the installer.")
        
        # Create empty file as placeholder
        with open(placeholder_path, 'wb') as f:
            f.write(b'')  # Empty placeholder