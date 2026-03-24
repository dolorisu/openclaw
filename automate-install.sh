#!/bin/bash
#
# OpenClaw VPS Full Automator
# Run this ONCE on a fresh VPS - handles EVERYTHING
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_banner() {
    echo ""
    echo "🦞 OpenClaw VPS Full Automator"
    echo "=============================="
    echo ""
}

# ==================== STEP 1: INSTALL PREREQUISITES ====================
install_prerequisites() {
    log_info "Step 1/5: Checking prerequisites..."

    # Update package list
    if ! sudo apt-get update > /dev/null 2>&1; then
        log_error "Failed to update package list. Check internet connection."
        exit 1
    fi

    # Check/Install Node.js 22+
    if ! command -v node > /dev/null 2>&1; then
        log_info "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - > /dev/null 2>&1
        sudo apt-get install -y nodejs > /dev/null 2>&1
        log_success "Node.js installed: $(node --version)"
    else
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -lt 22 ]; then
            log_warn "Node.js < 22 detected. Upgrading..."
            curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - > /dev/null 2>&1
            sudo apt-get install -y nodejs > /dev/null 2>&1
            log_success "Node.js upgraded: $(node --version)"
        else
            log_success "Node.js OK: $(node --version)"
        fi
    fi

    # Check/Install Chromium
    if ! command -v chromium-browser > /dev/null 2>&1; then
        log_info "Installing Chromium..."
        sudo apt-get install -y chromium-browser > /dev/null 2>&1
        log_success "Chromium installed"
    else
        log_success "Chromium OK"
    fi

    echo ""
}

# ==================== STEP 2: INSTALL OPENCLAW ====================
install_openclaw() {
    log_info "Step 2/5: Installing OpenClaw..."

    if command -v openclaw > /dev/null 2>&1; then
        log_warn "OpenClaw already installed: $(openclaw --version)"
        read -p "Reinstall/Update? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping OpenClaw installation"
            return
        fi
    fi

    log_info "Installing OpenClaw (this may take a few minutes)..."
    npm install -g openclaw > /tmp/openclaw-install.log 2>&1

    if command -v openclaw > /dev/null 2>&1; then
        log_success "OpenClaw installed: $(openclaw --version)"
    else
        log_error "OpenClaw installation failed! Check /tmp/openclaw-install.log"
        exit 1
    fi

    echo ""
}

# ==================== STEP 3: RUN SETUP ====================
run_setup() {
    log_info "Step 3/5: Running setup..."

    if [ -f ~/.openclaw/setup-vps.sh ]; then
        bash ~/.openclaw/setup-vps.sh
    else
        log_warn "setup-vps.sh not found! Creating basic config..."

        mkdir -p ~/.openclaw/artifacts/generated/{projects,scripts}
        mkdir -p ~/.openclaw/workspace/custom/policies
        mkdir -p /tmp/openclaw/downloads

        # Create openclaw.json
        if [ ! -f ~/.openclaw/openclaw.json ]; then
            cat > ~/.openclaw/openclaw.json << 'JSONEOF'
{
  "meta": { "lastTouchedVersion": "2026.3.7", "lastTouchedAt": "2026-03-24T00:00:00.000Z" },
  "agents": {
    "defaults": {
      "model": {
        "primary": "openai-codex/gpt-5.3-codex",
        "fallbacks": ["kimi-coding/k2p5", "openai-codex/gpt-5.3-codex-spark"]
      }
    }
  }
}
JSONEOF
        fi

        # Create systemd service
        mkdir -p ~/.config/systemd/user
        cat > ~/.config/systemd/user/openclaw-gateway.service << 'SERVICEEOF'
[Unit]
Description=OpenClaw Gateway
After=network-online.target
[Service]
Type=simple
ExecStart=/usr/bin/node /home/rifuki/.npm-global/lib/node_modules/openclaw/dist/index.js gateway --port 18789
Restart=always
Environment=HOME=/home/rifuki
Environment=CHROME_BIN=/usr/bin/chromium-browser
Environment=PUPPETEER_ARGS=--no-sandbox,--disable-setuid-sandbox
[Install]
WantedBy=default.target
SERVICEEOF

        systemctl --user daemon-reload
        systemctl --user enable openclaw-gateway.service 2>/dev/null || true
        log_success "Basic setup complete"
    fi

    echo ""
}

# ==================== STEP 4: START SERVICE ====================
start_service() {
    log_info "Step 4/5: Starting OpenClaw gateway..."

    systemctl --user start openclaw-gateway
    sleep 2

    if systemctl --user is-active --quiet openclaw-gateway; then
        log_success "Gateway is running!"
    else
        log_error "Gateway failed to start!"
        exit 1
    fi

    echo ""
}

# ==================== STEP 5: FINALIZE ====================
finalize() {
    log_info "Step 5/5: Finalizing..."

    echo ""
    echo "=============================="
    echo "🎉 OpenClaw Setup Complete!"
    echo "=============================="
    echo ""
    echo "⚠️  ONE MORE STEP: Run 'openclaw login' to authenticate"
    echo ""
    echo "After login, test with:"
    echo "   openclaw agent --channel whatsapp --to 'GROUP' --message 'Hello' --deliver"
    echo ""
}

# ==================== MAIN ====================
main() {
    print_banner

    if [ "$EUID" -eq 0 ]; then
        log_error "Do not run as root! Run as regular user with sudo access."
        exit 1
    fi

    install_prerequisites
    install_openclaw
    run_setup
    start_service
    finalize
}

main "$@"
