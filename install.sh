#!/bin/bash
# PyReader Installation Script
#Licensed under GPL-3.0-or-later
# Exit on error
set -e

# Define paths
INSTALL_DIR="/usr/local/share/pyreader"
LAUNCHER_PATH="/usr/local/bin/pyreader"
MAN_DIR="/usr/local/share/man/man1"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)."
  exit 1
fi

echo "Installing PyReader..."

# Create installation directory
mkdir -p "$INSTALL_DIR"

# Copy main application script
cp pyreader.py "$INSTALL_DIR/pyreader.py"
chmod +x "$INSTALL_DIR/pyreader.py"

# Copy launcher script
cp pyreader "$LAUNCHER_PATH"
chmod +x "$LAUNCHER_PATH"

# Copy man page if it exists
if [ -f "pyreader.1" ]; then
    mkdir -p "$MAN_DIR"
    cp pyreader.1 "$MAN_DIR/"
    echo "Man page installed to $MAN_DIR/pyreader.1"
fi

# Verify dependencies
echo "Verifying dependencies..."
if python3 -c "import curses, os, re, json, zipfile, xml.etree.ElementTree, pathlib, typing, html; print('All dependencies OK')" 2>/dev/null; then
    echo "Dependencies verified."
else
    echo "Warning: Some dependencies might be missing. Please refer to dependencies.txt."
fi

echo "Installation complete. You can now run PyReader by typing 'pyreader'."
