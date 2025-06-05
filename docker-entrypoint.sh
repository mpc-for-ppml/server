#!/bin/bash
set -e

# Function to wait for dependencies
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    
    echo "Waiting for $service to be ready..."
    while ! nc -z "$host" "$port"; do
        sleep 1
    done
    echo "$service is ready!"
}

# Create necessary directories if they don't exist
mkdir -p /app/uploads /app/results /app/logs

# Set proper permissions
chmod -R 755 /app/uploads /app/results /app/logs

# Check if we need to wait for any services (e.g., database)
# Uncomment and modify if you add a database
# wait_for_service db 5432 "PostgreSQL"

# Run database migrations if needed
# Uncomment if you add a database
# echo "Running database migrations..."
# alembic upgrade head

# Start the application
echo "Starting MPC PPML Server..."

# Development mode with auto-reload
if [ "$ENVIRONMENT" = "development" ]; then
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir /app \
        --log-level "${LOG_LEVEL:-info}"
# Production mode
else
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers "${WORKERS:-4}" \
        --log-level "${LOG_LEVEL:-info}" \
        --access-log
fi