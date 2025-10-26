#!/bin/bash

# Business Search Engine - Quick Start Script
# This script sets up and starts all services for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Business Search Engine - Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed${NC}"
echo -e "${GREEN}✓ Docker Compose is installed${NC}"
echo ""

# Check if Ollama is running (optional but recommended)
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Ollama is not running on localhost:11434${NC}"
    echo -e "${YELLOW}  The LLM features will not work without Ollama${NC}"
    echo -e "${YELLOW}  Install: https://ollama.com/download${NC}"
    echo -e "${YELLOW}  Then run: ollama pull llama3.2${NC}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Ollama is running${NC}"
    echo ""
fi

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}  Please review and update backend/.env with your settings${NC}"
    echo ""
fi

# Stop any existing containers
echo -e "${BLUE}Stopping existing containers...${NC}"
docker-compose down > /dev/null 2>&1 || true

# Build images
echo -e "${BLUE}Building Docker images...${NC}"
echo -e "${YELLOW}This may take a few minutes on first run...${NC}"
docker-compose build

echo ""
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

# Start services
echo -e "${BLUE}Starting services...${NC}"
docker-compose up -d

echo ""
echo -e "${GREEN}✓ All services started${NC}"
echo ""

# Wait for services to be healthy
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Check service health
echo ""
echo -e "${BLUE}Checking service health...${NC}"

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is ready${NC}"
else
    echo -e "${RED}❌ Redis is not responding${NC}"
fi

# Check Backend
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend API is ready${NC}"
else
    echo -e "${YELLOW}⚠ Backend API is not responding yet (may need more time)${NC}"
fi

# Show service URLs
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Services are running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}📡 API Documentation:${NC}    http://localhost:8000/docs"
echo -e "${GREEN}🏥 Health Check:${NC}         http://localhost:8000/health"
echo -e "${GREEN}🌸 Flower Dashboard:${NC}     http://localhost:5555"
echo -e "${GREEN}🔴 Redis:${NC}                localhost:6379"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "  View logs:           docker-compose logs -f"
echo "  View backend logs:   docker-compose logs -f backend"
echo "  View worker logs:    docker-compose logs -f celery-worker"
echo "  Stop services:       docker-compose down"
echo "  Restart services:    docker-compose restart"
echo ""
echo -e "${GREEN}To test the API, run:${NC}"
echo ""
echo "curl -X POST http://localhost:8000/api/search \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"Google Inc.\"}'"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Happy searching! 🚀${NC}"
echo -e "${BLUE}========================================${NC}"
