#!/bin/bash
# Script to build the Setup Manager macOS application
set -e

echo "Building Setup Manager macOS App"
echo "--------------------------------"

# Navigate to the project root
cd "$(dirname "$0")/.."

# Check for required tools
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install py2app if not available
if ! python3 -c "import py2app" &> /dev/null; then
    echo "Installing py2app..."
    pip3 install py2app
fi

# Create a simple app icon (or use existing one)
if [ ! -f "app_icon.icns" ]; then
    echo "Creating app icon..."
    
    # Check if iconutil is available (part of macOS developer tools)
    if ! command -v iconutil &> /dev/null; then
        echo "Warning: iconutil not available. Please install macOS Command Line Developer Tools."
        echo "Creating a placeholder icon instead..."
        
        # Create a placeholder icon using Python
        python3 - <<EOF
import os
import base64

# Base64 encoded 1x1 pixel png
png_data = b"""
iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9i
ZSBJbWFnZVJlYWR5ccllPAAAAyhpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tl
dCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1l
dGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUu
Ni1jMDY3IDc5LjE1Nzc0NywgMjAxNS8wMy8zMC0yMzo0MDo0MiAgICAgICAgIj4gPHJkZjpS
REYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgt
bnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8v
bnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNv
bS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEu
MC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9w
IENDIDIwMTUgKE1hY2ludG9zaCkiIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6RTVGN0I1
OTUyMzJCMTFFOTk5NkJBODRBRDIwRkQ3NzEiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6
RTVGN0I1OTYyMzJCMTFFOTk5NkJBODRBRDIwRkQ3NzEiPiA8eG1wTU06RGVyaXZlZEZyb20g
c3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDpFNUY3QjU5MzIzMkIxMUU5OTk2QkE4NEFEMjBG
RDc3MSIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDpFNUY3QjU5NDIzMkIxMUU5OTk2QkE4
NEFEMjBGRDc3MSIvPiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0
YT4gPD94cGFja2V0IGVuZD0iciI/PuDqTGEAAABHSURBVHjaYvz//z8DJYCJgUIwoouAIXzF
WYZDh3IZvvw+z/jtx3G4OKsmQQMuXbIlzYBrN3MYVqzKZxgwA3B55SqOYQ8YGAAQYADkSxKj
L2VgJQAAAABJRU5ErkJggg==
"""

# Write the icon data to a file
with open("app_icon.png", "wb") as f:
    f.write(base64.b64decode(png_data))

print("Created placeholder icon: app_icon.png")
EOF
        
        # Copy the PNG to icns format (not ideal, but will allow build to continue)
        cp app_icon.png app_icon.icns
    else
        # Create a proper icon set using iconutil
        mkdir -p AppIcon.iconset
        # Create the needed icon sizes
        for size in 16 32 64 128 256 512; do
            echo "Creating icon size ${size}x${size}..."
            # Use Python to create a colored square icon
            python3 - <<EOF
import os
from PIL import Image, ImageDraw
import sys

size = int(sys.argv[1])
img = Image.new('RGBA', (size, size), color=(0, 119, 204, 255))
draw = ImageDraw.Draw(img)
draw.rectangle([size//4, size//4, size*3//4, size*3//4], fill=(255, 255, 255, 200))
img.save(f"AppIcon.iconset/icon_{size}x{size}.png")
img.save(f"AppIcon.iconset/icon_{size}x{size}@2x.png")
EOF "${size}"
        done

        # Convert the iconset to icns file
        iconutil -c icns AppIcon.iconset
        mv AppIcon.icns app_icon.icns
        rm -rf AppIcon.iconset
    fi
fi

# Clean build directories if they exist
echo "Cleaning previous builds..."
rm -rf build dist

# Run py2app
echo "Building macOS app with py2app..."
python3 scripts/setup_app.py py2app

# Check if build was successful
if [ -d "dist/Setup Manager.app" ]; then
    echo "App build successful!"
    echo "App created at: $(pwd)/dist/Setup Manager.app"
    
    # Create a DMG if hdiutil is available
    if command -v hdiutil &> /dev/null; then
        echo "Creating DMG file..."
        hdiutil create -volname "Setup Manager" -srcfolder "dist/Setup Manager.app" -ov -format UDZO "dist/SetupManager.dmg"
        echo "DMG created at: $(pwd)/dist/SetupManager.dmg"
    fi
else
    echo "Error: App build failed. Check the output for errors."
    exit 1
fi

echo "Done!" 