#!/bin/bash

# N8N Agent Hub setup script
echo "Setting up N8N Agent Hub..."

# Generate a secure encryption key for n8n
ENCRYPTION_KEY=$(openssl rand -hex 24)

# Create .env file
cat > ../.env <<EOL
# N8N Configuration
N8N_USER=admin
N8N_PASSWORD=changeme
N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}

# MongoDB Configuration
MONGODB_URI=mongodb://mongodb:27017/n8n-agent-hub

# JWT Secret for backend
JWT_SECRET=$(openssl rand -hex 32)

# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
EOL

echo ".env file created with secure keys"
echo "Please edit the .env file to add your actual API keys"

# Ensure script files are executable
chmod +x ./start.sh
chmod +x ./stop.sh

echo "Setup complete!"
echo "To start the application, run: ./scripts/start.sh" 