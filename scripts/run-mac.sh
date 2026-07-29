#!/bin/bash
# StarNews — start after install. Usage: bash scripts/run-mac.sh
INSTALL_DIR="${STARNNEWS_DIR:-$HOME/StarTV-Slopautomation}"
cd "$INSTALL_DIR"
starnews web
