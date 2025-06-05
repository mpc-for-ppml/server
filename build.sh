#!/bin/bash

# MPC PPML Server - Docker Build Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="mpc-ppml-server"
TAG=${1:-latest}
DOCKERFILE=${2:-Dockerfile}

echo -e "${GREEN}🚀 Building MPC PPML Server Docker Image${NC}"
echo "Image: ${IMAGE_NAME}:${TAG}"
echo "Dockerfile: ${DOCKERFILE}"
echo "----------------------------------------"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build \
    -t "${IMAGE_NAME}:${TAG}" \
    -f "${DOCKERFILE}" \
    --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
    --build-arg VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
    echo -e "${GREEN}Image: ${IMAGE_NAME}:${TAG}${NC}"
    
    # Show image info
    echo -e "${YELLOW}📊 Image information:${NC}"
    docker images "${IMAGE_NAME}:${TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    echo -e "${GREEN}🎉 Build completed successfully!${NC}"
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "  - Run with: ./run.sh"
    echo "  - Or use docker-compose: docker-compose up"
    echo "  - For development: ./run.sh dev"
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi