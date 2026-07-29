#!/bin/bash
# StarNews — install once, then run. Usage: bash scripts/install-mac.sh
set -euo pipefail

INSTALL_DIR="${STARNNEWS_DIR:-$HOME/StarTV-Slopautomation}"
BRANCH="cursor/starnews-daily-pipeline"
REPO="https://github.com/x5mii/StarTV-Slopautomation.git"

echo "=== StarNews Install (Mac) ==="
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python fehlt. Installiere es von https://www.python.org/downloads/"
  echo "Dann dieses Script nochmal starten."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "Git fehlt. Installiere Xcode Command Line Tools:"
  echo "  xcode-select --install"
  exit 1
fi

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "Update vorhandene Installation in $INSTALL_DIR"
  git -C "$INSTALL_DIR" fetch origin
  git -C "$INSTALL_DIR" checkout "$BRANCH"
  git -C "$INSTALL_DIR" pull origin "$BRANCH"
else
  echo "Lade StarNews nach $INSTALL_DIR"
  git clone -b "$BRANCH" "$REPO" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
python3 -m pip install -e .

echo ""
echo "=== Fertig! Starte StarNews... ==="
echo "Ordner: $INSTALL_DIR"
echo ""
starnews web
