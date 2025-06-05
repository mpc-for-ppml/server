#!/bin/bash

# MPC PPML Server - Docker Run Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="mpc-ppml-server"
CONTAINER_NAME="mpc-ppml-server"
PORT=${PORT:-8000}
MODE=${1:-production}

echo -e "${GREEN}🚀 Starting MPC PPML Server${NC}"
echo "Mode: ${MODE}"
echo "Port: ${PORT}"
echo "Container: ${CONTAINER_NAME}"
echo "----------------------------------------"

# Function to stop existing container
stop_container() {
    if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
        echo -e "${YELLOW}🛑 Stopping existing container...${NC}"
        docker stop ${CONTAINER_NAME}
    fi
    
    if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
        echo -e "${YELLOW}🗑️  Removing existing container...${NC}"
        docker rm ${CONTAINER_NAME}
    fi
}

# Function to check if image exists
check_image() {
    if [ -z "$(docker images -q ${IMAGE_NAME}:latest)" ]; then
        echo -e "${YELLOW}⚠️  Image ${IMAGE_NAME}:latest not found. Building...${NC}"
        ./build.sh
    fi
}

# Function to run in development mode
run_dev() {
    echo -e "${BLUE}🔧 Running in DEVELOPMENT mode${NC}"
    
    stop_container
    check_image
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8000 \
        -e ENVIRONMENT=development \
        -e LOG_LEVEL=debug \
        -v "$(pwd)/app:/app/app" \
        -v "$(pwd)/mpyc_task.py:/app/mpyc_task.py" \
        -v "$(pwd)/app/data:/app/app/data" \
        --restart unless-stopped \
        ${IMAGE_NAME}:latest
}

# Function to run in production mode
run_prod() {
    echo -e "${GREEN}🏭 Running in PRODUCTION mode${NC}"
    
    stop_container
    check_image
    
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8000 \
        -e ENVIRONMENT=production \
        -e LOG_LEVEL=info \
        -e WORKERS=4 \
        -v mpc-uploads:/app/uploads \
        -v mpc-results:/app/results \
        -v mpc-logs:/app/logs \
        --restart unless-stopped \
        ${IMAGE_NAME}:latest
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}📋 Showing container logs...${NC}"
    docker logs -f ${CONTAINER_NAME}
}

# Main execution
case "${MODE}" in
    "dev"|"development")
        run_dev
        ;;
    "prod"|"production")
        run_prod
        ;;
    "logs")
        show_logs
        exit 0
        ;;
    "stop")
        stop_container
        echo -e "${GREEN}✅ Container stopped${NC}"
        exit 0
        ;;
    "restart")
        stop_container
        run_prod
        ;;
    *)
        echo -e "${RED}❌ Invalid mode: ${MODE}${NC}"
        echo "Usage: $0 [dev|prod|logs|stop|restart]"
        echo "  dev/development  - Run in development mode with hot reload"
        echo "  prod/production  - Run in production mode (default)"
        echo "  logs            - Show container logs"
        echo "  stop            - Stop the container"
        echo "  restart         - Restart the container"
        exit 1
        ;;
esac

# Wait a moment and check if container is running
sleep 2

if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo -e "${GREEN}✅ Container is running!${NC}"
    echo -e "${GREEN}🌐 Server accessible at: http://localhost:${PORT}${NC}"
    echo -e "${YELLOW}💡 Useful commands:${NC}"
    echo "  - View logs: ./run.sh logs"
    echo "  - Stop server: ./run.sh stop"
    echo "  - Restart: ./run.sh restart"
    echo "  - Container status: docker ps -f name=${CONTAINER_NAME}"
else
    echo -e "${RED}❌ Container failed to start!${NC}"
    echo -e "${YELLOW}📋 Checking logs...${NC}"
    docker logs ${CONTAINER_NAME}
    exit 1
fi