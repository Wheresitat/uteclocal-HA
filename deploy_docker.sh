#!/bin/bash
# U-tec Gateway Auto-Refresh Deployment Script
# Optimized for uteclocal-HA repository structure

set -e

echo "================================================"
echo "U-tec Gateway - Docker Deployment"
echo "Enhanced with Automatic Token Refresh"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the uteclocal-HA directory"
    exit 1
fi

# Check if gateway/main.py exists
if [ ! -f "gateway/main.py" ]; then
    echo -e "${RED}Error: gateway/main.py not found${NC}"
    echo "The repository structure may be incomplete."
    echo "Please make sure you extracted the complete zip file."
    exit 1
fi

echo -e "${GREEN}✓ Repository structure verified${NC}"
echo ""

# Create backup
echo -e "${YELLOW}Creating backup...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup existing config from running container (if exists)
if docker ps | grep -q uteclocal-gateway; then
    echo -e "${YELLOW}Backing up existing config from container...${NC}"
    docker cp uteclocal-gateway:/data/config.json "$BACKUP_DIR/config.json" 2>/dev/null || true
    docker cp uteclocal-gateway:/data/gateway.log "$BACKUP_DIR/gateway.log" 2>/dev/null || true
    echo -e "${GREEN}✓ Config backed up${NC}"
fi

# Backup current files
if [ -f "Dockerfile" ]; then
    cp Dockerfile "$BACKUP_DIR/" 2>/dev/null || true
fi
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true
fi

echo -e "${GREEN}✓ Backup created in $BACKUP_DIR${NC}"
echo ""

# Check if APScheduler is in requirements
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! grep -q "APScheduler" requirements.txt 2>/dev/null; then
    echo -e "${YELLOW}Note: APScheduler not in requirements.txt${NC}"
    echo -e "${YELLOW}It should already be there, but if build fails, this might be why${NC}"
else
    echo -e "${GREEN}✓ APScheduler found in requirements${NC}"
fi
echo ""

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker compose -p uteclocal down 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Build and start
echo -e "${YELLOW}Building and starting enhanced gateway...${NC}"
echo "This may take a minute..."
docker compose -p uteclocal up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Gateway container started${NC}"
else
    echo -e "${RED}✗ Failed to start gateway${NC}"
    echo "Check errors above. You can view logs with:"
    echo "  docker compose -p uteclocal logs gateway"
    exit 1
fi
echo ""

# Wait for gateway to be ready
echo -e "${YELLOW}Waiting for gateway to be ready...${NC}"
RETRIES=0
MAX_RETRIES=30

while [ $RETRIES -lt $MAX_RETRIES ]; do
    if docker compose -p uteclocal ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ Gateway is healthy and ready!${NC}"
        break
    fi
    
    if docker compose -p uteclocal ps | grep -q "Up"; then
        RETRIES=$((RETRIES + 1))
        if [ $((RETRIES % 5)) -eq 0 ]; then
            echo "  Still starting... ($RETRIES/$MAX_RETRIES)"
        fi
        sleep 2
    else
        echo -e "${RED}✗ Container is not running${NC}"
        docker compose -p uteclocal ps
        echo ""
        echo "View logs with: docker compose -p uteclocal logs gateway"
        exit 1
    fi
done

if [ $RETRIES -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠ Gateway started but health check pending${NC}"
    echo "Check status with: docker compose -p uteclocal ps"
fi
echo ""

# Test connectivity
echo -e "${YELLOW}Testing gateway connectivity...${NC}"
if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Gateway is accessible on http://localhost:8000${NC}"
    
    # Show health status
    HEALTH=$(curl -s http://localhost:8000/health)
    echo ""
    echo "Health Status:"
    echo "$HEALTH" | python3 -m json.tool 2>/dev/null || echo "$HEALTH"
else
    echo -e "${RED}✗ Gateway not responding on http://localhost:8000${NC}"
    echo "This is unusual. Check logs:"
    echo "  docker compose -p uteclocal logs gateway"
fi
echo ""

# Show container status
echo -e "${YELLOW}Container Status:${NC}"
docker compose -p uteclocal ps
echo ""

# Display summary
echo "================================================"
echo -e "${GREEN}✅ Docker Deployment Complete!${NC}"
echo "================================================"
echo ""
echo "Gateway URL: ${GREEN}http://localhost:8000${NC}"
echo "Web UI:      ${GREEN}http://localhost:8000/${NC}"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Open web UI in browser:"
echo "   http://localhost:8000"
echo ""
echo "2. If this is a fresh install, configure OAuth:"
echo "   - Enter your U-tec API credentials"
echo "   - Complete OAuth authorization flow"
echo ""
echo "3. Verify auto-refresh is enabled:"
echo "   - Check 'Token Status' section"
echo "   - Should show 'Auto-refresh: ✅ Enabled'"
echo ""
echo "4. Your Home Assistant integration will continue"
echo "   working without any changes!"
echo ""
echo "📊 Useful Commands:"
echo ""
echo "  View logs:        docker compose -p uteclocal logs -f gateway"
echo "  Check status:     docker compose -p uteclocal ps"
echo "  Restart:          docker compose -p uteclocal restart gateway"
echo "  Stop:             docker compose -p uteclocal down"
echo "  Test health:      curl http://localhost:8000/health"
echo ""
echo "💾 Your config and tokens are stored in a Docker volume"
echo "   and will persist across container restarts/rebuilds."
echo ""
echo "================================================"

echo ""
echo "Deployment completed successfully! 🎉"
