#!/usr/bin/env bash
# Build a folder you can zip and send to teammates (macOS).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -f "starnews/team_defaults.yaml" ]; then
  echo "Missing starnews/team_defaults.yaml"
  echo "Copy: cp starnews/team_defaults.example.yaml starnews/team_defaults.yaml"
  echo "Then add your API keys before building."
  exit 1
fi

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

ZIP="$ROOT/release/StarNews-macOS.zip"
rm -f "$ZIP"
(cd "$ROOT/release" && zip -r "StarNews-macOS.zip" "StarNews-macOS" >/dev/null)

echo ""
echo "Built: $RELEASE"
echo "Zip:   $ZIP"
echo "Share the zip with coworkers — they only choose their output folder on first run."
