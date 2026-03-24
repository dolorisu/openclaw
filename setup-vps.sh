#!/bin/bash
# OpenClaw VPS Setup Script
# Run ONCE after: npm install -g openclaw
# Safe to re-run (won't overwrite existing configs)

set -e

echo "🚀 OpenClaw VPS Setup Script"
echo "=============================="
echo ""

# Check openclaw
if ! command -v openclaw > /dev/null 2>&1; then
    echo "[ERROR] OpenClaw not found! Install: npm install -g openclaw"
    exit 1
fi

# Check Chromium
if ! command -v chromium-browser > /dev/null 2>&1; then
    echo "[WARN] Chromium not found! Image search won't work."
    echo "[WARN] Install: sudo apt install chromium-browser"
fi

echo "[OK] Prerequisites OK"
echo ""

# Setup directories
echo "[INFO] Creating directories..."
mkdir -p ~/.openclaw/artifacts/generated/{projects,scripts,configs,reports,assets}
mkdir -p ~/.openclaw/workspace/custom/{policies,ops}
mkdir -p /tmp/openclaw/downloads

# Create openclaw.json (if not exists)
if [ -f ~/.openclaw/openclaw.json ]; then
    echo "[WARN] openclaw.json exists - SKIPPING"
    echo "[INFO] Backup first if you want fresh config:"
    echo "       mv ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup.$(date +%Y%m%d)"
else
    echo "[INFO] Creating openclaw.json..."
    cat > ~/.openclaw/openclaw.json << 'JSONEOF'
{
  "meta": {
    "lastTouchedVersion": "2026.3.7",
    "lastTouchedAt": "2026-03-24T00:00:00.000Z"
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai-codex/gpt-5.3-codex",
        "fallbacks": [
          "kimi-coding/k2p5",
          "openai-codex/gpt-5.3-codex-spark"
        ]
      }
    }
  }
}
JSONEOF
    echo "[OK] openclaw.json created"
fi
echo ""

# Create systemd service
echo "[INFO] Creating systemd service..."
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/openclaw-gateway.service << 'SERVICEEOF'
[Unit]
Description=OpenClaw Gateway
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/node /home/rifuki/.npm-global/lib/node_modules/openclaw/dist/index.js gateway --port 18789
Restart=always
RestartSec=5
Environment=HOME=/home/rifuki
Environment=PATH=/home/rifuki/.local/bin:/home/rifuki/.npm-global/bin:/usr/local/bin:/usr/bin:/bin
# Chrome headless fix - CRITICAL for image search
Environment=DISPLAY=:99
Environment=CHROME_BIN=/usr/bin/chromium-browser
Environment=CHROME_PATH=/usr/bin/chromium-browser
Environment=PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
Environment=PUPPETEER_ARGS=--no-sandbox,--disable-setuid-sandbox,--disable-dev-shm-usage,--disable-gpu

[Install]
WantedBy=default.target
SERVICEEOF

systemctl --user daemon-reload
systemctl --user enable openclaw-gateway.service 2>/dev/null || true

echo "[OK] Systemd service created"
echo ""

# Create workspace configs (if not exist)
if [ ! -f ~/.openclaw/workspace/AGENTS.md ]; then
    echo "[INFO] Creating AGENTS.md..."
    cat > ~/.openclaw/workspace/AGENTS.md << 'EOF'
# AGENTS.md

## File Location Policy
- Generated projects: ~/.openclaw/artifacts/generated/projects/
- Media for WhatsApp: /tmp/openclaw/downloads/
- Scripts: ~/.openclaw/artifacts/generated/scripts/
- Configs: ~/.openclaw/artifacts/generated/configs/
EOF
fi

if [ ! -f ~/.openclaw/workspace/SOUL.md ]; then
    echo "[INFO] Creating SOUL.md..."
    cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
# SOUL.md

Core personality: 50% Doloris/Misumi
- Use kaomoji: (◕‿◕), (｡♥‿♥｡), (⌒‿⌒)
- Natural Bahasa: "nih", "ya~", "dong"
- Warm, engaging, but technically precise
EOF
fi

echo ""
echo "=============================="
echo "✅ Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "  1. openclaw login"
echo "  2. systemctl --user start openclaw-gateway"
echo "  3. Test: openclaw agent --to 'YOUR_GROUP' --message 'test' --deliver"
echo ""
