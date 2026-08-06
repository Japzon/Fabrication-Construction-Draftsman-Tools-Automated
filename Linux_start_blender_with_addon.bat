#!/bin/bash

# Target addon directory for Blender 5.2
BLENDER_VERSION="5.2"
ADDON_NAME="layouts_systems_draftsman_toolkit"
ADDON_DIR="$HOME/.config/blender/$BLENDER_VERSION/scripts/addons"
TARGET_LINK="$ADDON_DIR/$ADDON_NAME"
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "  BLENDER DEVELOPMENT SETUP (UBUNTU NOBLE NUMBAT)"
echo "=================================================="

# 1. Kill any running blender instances
echo "[INFO] Terminating running Blender instances..."
pkill -x "blender" 2>/dev/null

# 2. Create the addons directory if it doesn't exist
mkdir -p "$ADDON_DIR"

# 3. Clean up existing symlink/directory
if [ -e "$TARGET_LINK" ] || [ -L "$TARGET_LINK" ]; then
    echo "[INFO] Removing old add-on files at: $TARGET_LINK"
    rm -rf "$TARGET_LINK"
fi

# 4. Create a symlink
echo "[INFO] Connecting project to Blender..."
ln -s "$SOURCE_DIR" "$TARGET_LINK"
echo "[SUCCESS] Link created successfully!"

# 5. Launch Blender Snap (classic)
echo "[SUCCESS] Attempting to launch Blender $BLENDER_VERSION..."
CLEANUP_SCRIPT="$SOURCE_DIR/_dev/cleanup_addons.py"

if [ -f "$CLEANUP_SCRIPT" ]; then
    echo "[INFO] Using cleanup script: $CLEANUP_SCRIPT"
    blender --python "$CLEANUP_SCRIPT"
else
    blender
fi

echo ""
echo "[INFO] Process finished or Blender closed."
