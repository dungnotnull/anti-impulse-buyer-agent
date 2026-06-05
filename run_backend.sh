#!/bin/bash
# anti-impulse-buyer — Backend Launcher (macOS/Linux)
cd "$(dirname "$0")"
source venv/bin/activate
python -m backend.main
