#!/bin/bash
# PyReader Uninstallation Script
#Licensed under GPL-3.0-or-later
# Exit on error
set -e

# Define paths
INSTALL_DIR="/usr/local/share/pyreader"
LAUNCHER_PATH="/usr/local/bin/pyreader"
MAN_PATH="/usr/local/share/man/man1/pyreader.1"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)."
  exit 1
fi

echo "Uninstalling PyReader..."

# Remove installation directory and script
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "Removed $INSTALL_DIR"
fi

# Remove launcher script
if [ -f "$LAUNCHER_PATH" ]; then
    rm "$LAUNCHER_PATH"
    echo "Removed $LAUNCHER_PATH"
fi

# Remove man page if it exists
if [ -f "$MAN_PATH" ]; then
    rm "$MAN_PATH"
    echo "Removed $MAN_PATH"
fi

echo "Uninstallation complete."
