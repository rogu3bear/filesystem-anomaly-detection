# N8N Agent Hub

A complete platform for hosting and managing n8n AI agents. This application enables users to create, customize, and deploy n8n AI agents for various tasks with minimal setup.

## Features

- Create and manage n8n instances on-demand
- Configure AI agents through a user-friendly interface
- Support for multiple AI models (OpenAI, Google Gemini, DeepSeek, etc.)
- Free tier with basic functionality and premium tiers for advanced features
- RESTful API for programmatic management of agents
- Automated agent deployment via Docker
- Detailed analytics and monitoring of agent usage

## Architecture

- **Frontend**: React-based web interface for managing agents
- **Backend**: Node.js REST API for controlling n8n instances
- **Docker**: Containerized n8n instances with preconfigured tools
- **Database**: MongoDB for storing agent configurations and user data

## Quick Start

1. Clone this repository
2. Install dependencies with `npm install`
3. Set up environment variables (see .env.example)
4. Start the development server with `npm run dev`

## Technologies Used

- **Frontend**: React, TypeScript, Material-UI
- **Backend**: Node.js, Express, TypeScript
- **Database**: MongoDB
- **Container**: Docker
- **Workflow Automation**: n8n
- **AI Models**: OpenAI, Google Gemini, etc.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 