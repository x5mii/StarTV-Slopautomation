#!/usr/bin/env bash
# Build a folder you can zip and send to teammates (macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! python3 -c "import PyInstaller" 2>/dev/null; then
  echo "Installing PyInstaller..."
  python3 -m pip install pyinstaller
fi

python3 -m PyInstaller starnews.spec --noconfirm

RELEASE="$ROOT/release/StarNews-macOS"
rm -rf "$RELEASE"
mkdir -p "$RELEASE"

cp -R dist/starnews/* "$RELEASE/"
cp config.yaml "$RELEASE/"
cp config.local.example.yaml "$RELEASE/"
cp scripts/Start-StarNews.command "$RELEASE/"
chmod +x "$RELEASE/Start-StarNews.command"

echo ""
echo "Built: $RELEASE"
echo "1. Copy config.local.example.yaml -> config.local.yaml and fill in team keys"
echo "2. Zip the StarNews-macOS folder and send it privately"
echo "3. Teammate double-clicks Start-StarNews.command"
