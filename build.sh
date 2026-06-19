#!/bin/bash
# ============================================
# Manim Studio — Build & Deploy Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎬 Manim Studio — Build Script${NC}"
echo "================================="

# Check for required tools
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
        exit 1
    fi

    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ pip3 is required but not installed.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"
}

# Install Python dependencies
install_deps() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Build Docker image
build_docker() {
    echo -e "${YELLOW}Building Docker image...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is required for containerized deployment.${NC}"
        echo -e "${YELLOW}Falling back to local deployment...${NC}"
        return 1
    fi

    docker build -t manim-studio .
    echo -e "${GREEN}✅ Docker image built: manim-studio${NC}"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    echo -e "${YELLOW}Deploying with Docker Compose...${NC}"

    if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is required.${NC}"
        return 1
    fi

    # Try docker compose first, fall back to docker-compose
    if command -v docker compose &> /dev/null; then
        docker compose up -d --build
    else
        docker-compose up -d --build
    fi

    echo -e "${GREEN}✅ Deployed! Access at http://localhost:5000${NC}"
}

# Deploy locally
deploy_local() {
    echo -e "${YELLOW}Starting local server...${NC}"
    echo -e "${GREEN}✅ Server starting at http://localhost:5000${NC}"
    python3 app.py
}

# Deploy to Vercel
deploy_vercel() {
    echo -e "${YELLOW}Deploying to Vercel...${NC}"

    if ! command -v vercel &> /dev/null; then
        echo -e "${RED}❌ Vercel CLI is required. Install with: npm i -g vercel${NC}"
        return 1
    fi

    vercel --prod
    echo -e "${GREEN}✅ Deployed to Vercel${NC}"
}

# Create zip package
create_zip() {
    echo -e "${YELLOW}Creating zip package...${NC}"

    # Get script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    ZIP_NAME="manim-studio-$(date +%Y%m%d-%H%M%S).zip"

    # Create zip excluding unnecessary files
    cd "$SCRIPT_DIR"
    zip -r "$ZIP_NAME" . \
        -x "renders/*" \
        -x "__pycache__/*" \
        -x "*.pyc" \
        -x ".git/*" \
        -x "node_modules/*" \
        -x "*.zip"

    echo -e "${GREEN}✅ Created: ${ZIP_NAME}${NC}"
    echo -e "${BLUE}📦 Share this file to distribute the project${NC}"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}Available commands:${NC}"
    echo "  1) Install dependencies"
    echo "  2) Build Docker image"
    echo "  3) Deploy with Docker Compose"
    echo "  4) Deploy locally"
    echo "  5) Deploy to Vercel"
    echo "  6) Create zip package"
    echo "  7) Run all (install + local)"
    echo ""
    read -p "Enter choice [1-7]: " choice

    case $choice in
        1) install_deps ;;
        2) build_docker ;;
        3) deploy_docker_compose ;;
        4) deploy_local ;;
        5) deploy_vercel ;;
        6) create_zip ;;
        7)
            check_dependencies
            install_deps
            deploy_local
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac
}

# Parse command line arguments
if [ $# -gt 0 ]; then
    case $1 in
        install) install_deps ;;
        docker) build_docker ;;
        compose) deploy_docker_compose ;;
        local) deploy_local ;;
        vercel) deploy_vercel ;;
        zip) create_zip ;;
        *)
            echo "Usage: $0 {install|docker|compose|local|vercel|zip}"
            exit 1
            ;;
    esac
else
    show_menu
fi
