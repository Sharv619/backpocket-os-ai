#!/bin/bash
# BackPocket OS — MCP Server Startup Script
# Starts all 4 MCP servers for OpenCode orchestrator

set -e

echo "=========================================="
echo "BackPocket OS — MCP Server Launcher"
echo "=========================================="

cd /home/lade/Hackathons/.git/backpocket-mvp

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check if port is in use
check_port() {
    lsof -i:$1 >/dev/null 2>&1
}

# Function to start a server
start_server() {
    local name=$1
    local file=$2
    local port=$3
    
    echo -n "Starting $name... "
    
    if check_port $port; then
        echo -e "${YELLOW}already running on port $port${NC}"
    else
        nohup node mcp_servers/$file > /tmp/mcp-$name.log 2>&1 &
        sleep 1
        if check_port $port; then
            echo -e "${GREEN}✓ running on port $port${NC}"
        else
            echo -e "${RED}✗ failed${NC}"
            cat /tmp/mcp-$name.log
        fi
    fi
}

# Stop existing MCP servers first
echo ""
echo "Stopping any existing MCP servers..."
pkill -f "node mcp_servers" 2>/dev/null || true
sleep 1

# Start all MCP servers
echo ""
echo "Starting MCP servers..."
echo ""

start_server "leads" "leads.mjs" 3100
start_server "quotes" "quotes.mjs" 3101
start_server "pipeline" "pipeline.mjs" 3102
start_server "knowledge" "knowledge.mjs" 3103

# Verify all running
echo ""
echo "=========================================="
echo "MCP Server Status"
echo "=========================================="
echo ""

for port in 3100 3101 3102 3103; do
    if check_port $port; then
        echo -e "Port $port: ${GREEN}✓ Running${NC}"
    else
        echo -e "Port $port: ${RED}✗ Not running${NC}"
    fi
done

echo ""
echo "Logs available at: /tmp/mcp-*.log"
echo ""
echo "To test MCP servers, run OpenCode in this directory."
echo "The .mcp.json will auto-load these 4 servers."

# Show processes
echo ""
echo "Active processes:"
ps aux | grep "node mcp_servers" | grep -v grep | awk '{print $2, $11, $12, $13}'