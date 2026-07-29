#!/bin/bash
cd "$(dirname "$0")"

if [ -x "./starnews" ]; then
  APP="./starnews"
else
  APP="python3 -m starnews"
fi

echo "Starting StarNews..."
$APP web &
sleep 2
open "http://127.0.0.1:8765"
