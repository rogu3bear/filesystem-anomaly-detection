#!/bin/bash
# Updated script to setup the backend agent for the Filesystem Anomaly Detection project
# Navigates into the n8n-agent-hub/backend directory, installs dependencies, builds, and starts the agent

cd "$(dirname "$0")/../n8n-agent-hub/backend"

npm install
npm run build
npm start 