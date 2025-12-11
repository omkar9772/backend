#!/bin/bash

# Naad Bailgada - Quick Start Script
# This script starts all required services for the Naad Bailgada application

echo "======================================"
echo "Naad Bailgada - Starting Services"
echo "======================================"
echo ""

# Check if Docker is running
echo "1. Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo "   ERROR: Docker is not running!"
    echo "   Please start Docker Desktop and try again."
    exit 1
fi
echo "   Docker is running"
echo ""

# Start Docker services
echo "2. Starting Docker services..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "   Docker services started successfully"
else
    echo "   ERROR: Failed to start Docker services"
    exit 1
fi
echo ""

# Wait for services to be healthy
echo "3. Waiting for services to be healthy..."
sleep 5

# Check service status
echo ""
echo "4. Service Status:"
docker-compose ps
echo ""

# Display access information
echo "======================================"
echo "Services Ready!"
echo "======================================"
echo ""
echo "Backend API:        http://localhost:8000"
echo "API Documentation:  http://localhost:8000/docs"
echo "Database Admin:     http://localhost:8081"
echo ""
echo "To start Admin Web Interface:"
echo "  cd admin-web && ./serve.sh"
echo "  Then open: http://localhost:8080"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "======================================"
echo ""

# Test backend health
echo "5. Testing backend health..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   Backend is healthy: $HEALTH_CHECK"
else
    echo "   WARNING: Backend health check failed"
    echo "   Services may still be starting up..."
    echo "   Check logs with: docker logs naad_bailgada_backend"
fi
echo ""

echo "All services started successfully!"
