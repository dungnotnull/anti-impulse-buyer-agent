#!/bin/bash
# anti-impulse-buyer — One-time setup script (macOS/Linux)
echo "Setting up anti-impulse-buyer..."
echo ""

# Create virtual environment
echo "[1/4] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python deps
echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt

# Install JS deps and build popup
echo "[3/4] Building popup dashboard..."
cd extension/popup
npm install
npx vite build
cd ../..

echo "[4/4] Setup complete!"
echo ""
echo "============================================="
echo " anti-impulse-buyer is ready!"
echo ""
echo " To start: source venv/bin/activate && python -m backend.main"
echo " Then load extension/ folder in Chrome:"
echo "   chrome://extensions -> Load unpacked"
echo "============================================="
