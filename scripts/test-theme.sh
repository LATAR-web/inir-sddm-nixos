#!/usr/bin/env bash
# Test ii-pixel SDDM theme in a nested test window.
set -euo pipefail

THEME_DIR="${1:-/var/lib/sddm/themes/ii-pixel}"

if [[ ! -d "$THEME_DIR" ]]; then
    echo "Theme directory $THEME_DIR does not exist."
    exit 1
fi

echo "Testing SDDM theme from: $THEME_DIR"
if command -v sddm-greeter >/dev/null 2>&1; then
    sddm-greeter --test-mode --theme "$THEME_DIR"
elif command -v sddm-greeter-qt6 >/dev/null 2>&1; then
    sddm-greeter-qt6 --test-mode --theme "$THEME_DIR"
else
    echo "sddm-greeter binary not found in PATH."
    exit 1
fi
