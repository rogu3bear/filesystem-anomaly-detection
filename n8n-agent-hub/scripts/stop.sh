#!/bin/bash

echo "Stopping N8N Agent Hub..."

# Navigate to docker directory
cd ../docker

# Stop containers
docker-compose down

echo "N8N Agent Hub has been stopped." 