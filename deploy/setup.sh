#!/bin/bash
set -euo pipefail

# ═══════════════════════════════════════════════════════════
# AI Voice Agent — Self-Hosted Setup Script
# Runs on a fresh Ubuntu/Debian server with Docker installed
# ═══════════════════════════════════════════════════════════

echo "============================================"
echo "  AI Voice Agent — Self-Hosted Setup"
echo "============================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "Docker installed. Please log out and back in, then re-run this script."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Docker Compose plugin not found. Please install Docker Compose v2."
    exit 1
fi

echo "Docker OK."
echo ""

# Domain
read -p "Enter your domain (e.g., livekit.example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "Domain is required."
    exit 1
fi

# Generate API keys
API_KEY="API$(openssl rand -hex 8)"
API_SECRET="$(openssl rand -hex 32)"

echo ""
echo "Generated LiveKit credentials:"
echo "  API Key:    $API_KEY"
echo "  API Secret: $API_SECRET"
echo ""

# Detect public IP
PUBLIC_IP=$(curl -s https://api.ipify.org 2>/dev/null || echo "")
if [ -n "$PUBLIC_IP" ]; then
    echo "Detected public IP: $PUBLIC_IP"
else
    read -p "Could not detect public IP. Enter it manually: " PUBLIC_IP
fi

# AI Provider keys
echo ""
echo "Enter your AI provider API keys (press Enter to skip):"
read -p "  OpenAI API Key: " OPENAI_KEY
read -p "  Deepgram API Key: " DEEPGRAM_KEY
read -p "  Anthropic API Key (optional): " ANTHROPIC_KEY
read -p "  ElevenLabs API Key (optional): " ELEVENLABS_KEY

# Create .env
cat > .env << EOF
LIVEKIT_DOMAIN=${DOMAIN}
LIVEKIT_API_KEY=${API_KEY}
LIVEKIT_API_SECRET=${API_SECRET}
OPENAI_API_KEY=${OPENAI_KEY}
DEEPGRAM_API_KEY=${DEEPGRAM_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
ELEVEN_API_KEY=${ELEVENLABS_KEY}
AGENT_CONFIG=configs/default.yaml
EOF

echo ""
echo ".env file created."

# Update livekit.yaml with real keys and IP
sed -i "s/devkey: secret-change-me-in-production/${API_KEY}: ${API_SECRET}/" livekit.yaml
sed -i "s/# node_ip: 1.2.3.4/node_ip: ${PUBLIC_IP}/" livekit.yaml
sed -i "s/# use_external_ip: true/use_external_ip: true/" livekit.yaml
sed -i "s/# domain: turn.yourdomain.com/domain: turn.${DOMAIN}/" livekit.yaml

echo "livekit.yaml configured."

# Update Caddyfile
export LIVEKIT_DOMAIN="$DOMAIN"

echo ""
echo "============================================"
echo "  DNS Configuration Required"
echo "============================================"
echo ""
echo "Point these DNS records to $PUBLIC_IP:"
echo "  A  ${DOMAIN}       -> ${PUBLIC_IP}"
echo "  A  app.${DOMAIN}   -> ${PUBLIC_IP}"
echo "  A  turn.${DOMAIN}  -> ${PUBLIC_IP}"
echo ""
read -p "Press Enter when DNS is configured..."

# Open firewall ports
echo ""
echo "Required ports (ensure they are open):"
echo "  80/tcp    - HTTP (Caddy SSL provisioning)"
echo "  443/tcp   - HTTPS"
echo "  443/udp   - HTTP/3 (QUIC)"
echo "  7881/tcp  - WebRTC TCP fallback"
echo "  3478/udp  - TURN UDP"
echo "  5349/tcp  - TURN TLS"
echo "  50000-60000/udp - WebRTC media"
echo ""

# Start services
echo "Starting services..."
docker compose up -d --build

echo ""
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"
echo ""
echo "  LiveKit Server: wss://${DOMAIN}"
echo "  Frontend:       https://app.${DOMAIN}"
echo "  TURN:           turn.${DOMAIN}"
echo ""
echo "  API Key:    ${API_KEY}"
echo "  API Secret: ${API_SECRET}"
echo ""
echo "  Logs:  docker compose logs -f"
echo "  Stop:  docker compose down"
echo ""
