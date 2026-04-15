#!/usr/bin/env python3
"""
Temporarily replace all black pixels with pink in 'mapImages/ancientMapBlackWhite.webp'
and display the modified image.
"""

from PIL import Image

def replace_black_with_pink(image_path):
    # Open the image
    with Image.open(image_path) as img:
        # Convert to RGB for consistent pixel access
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Load pixel data
        pixels = img.load()
        width, height = img.size

        # Define pink color (R=255, G=192, B=203)
        pink = (255, 192, 203)

        # Replace pure black pixels with pink
        for y in range(height):
            for x in range(width):
                if pixels[x, y] == (0, 0, 0):  # Exact black
                    pixels[x, y] = pink

        # Display the modified image
        img.show()
        print("Modified image opened. Close the viewer to exit.")

if __name__ == "__main__":
    image_path = "mapImages/ancientMapBlackWhite.webp"
    try:
        replace_black_with_pink(image_path)
    except FileNotFoundError:
        print(f"Error: File not found at '{image_path}'")
    except Exception as e:
        print(f"Error processing image: {e}")