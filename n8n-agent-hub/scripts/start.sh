#!/bin/bash

# Load environment variables
if [ -f ../.env ]; then
  export $(grep -v '^#' ../.env | xargs)
fi

echo "Starting N8N Agent Hub..."

# Navigate to docker directory
cd ../docker

# Start containers
docker-compose up -d

echo "N8N Agent Hub is now running!"
echo "- Frontend: http://localhost"
echo "- Backend API: http://localhost:3000"
echo "- N8N: http://localhost:5678"
echo ""
echo "Default credentials:"
echo "- Username: ${N8N_USER:-admin}"
echo "- Password: ${N8N_PASSWORD:-admin}" 