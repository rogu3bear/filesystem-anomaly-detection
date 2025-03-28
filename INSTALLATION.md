# File Organizer AI Agent - Docker Installation Guide

This guide covers the installation of the File Organizer AI Agent using Docker, which is the recommended approach for most users. Docker provides a consistent environment and simplifies the setup process.

## Prerequisites

- Docker and Docker Compose installed on your system
- For macOS users, we provide an automated installer script that will handle Docker installation as well
- Basic familiarity with the terminal/command line

## Installation Options

### Option 1: Automated Installation (macOS only)

1. Download the repository:
   ```bash
   git clone https://github.com/yourusername/file-organizer-agent.git
   cd file-organizer-agent
   ```

2. Run the automated installer script:
   ```bash
   chmod +x install_docker.sh
   ./install_docker.sh
   ```

3. Follow the prompts to configure your installation.

4. Once complete, access the web interface at `http://localhost:8080`

### Option 2: Manual Docker Installation (All Platforms)

1. Download the repository:
   ```bash
   git clone https://github.com/yourusername/file-organizer-agent.git
   cd file-organizer-agent
   ```

2. Create a `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file to configure your settings:
   ```bash
   # Edit the file with your preferred text editor
   nano .env
   
   # Be sure to update at minimum:
   # - SOURCE_DIR: Directory to monitor for files
   # - TARGET_DIR: Directory where files will be organized
   ```

4. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

5. Access the web interface at `http://localhost:8080`

## Post-Installation

After installation, you should:

1. **Generate an API Key**: Visit the API Key page in the web interface to generate an API key if you didn't specify one in the `.env` file.

2. **Configure File Organization Settings**: Update the configuration settings through the web interface.

3. **Check System Status**: Verify all services are running correctly on the dashboard.

## Common Commands

Here are some useful Docker commands for managing your installation:

```bash
# Start the services
docker-compose up -d

# Stop the services
docker-compose stop

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update to a new version (after pulling changes)
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Services Not Starting

Check the logs for error messages:
```bash
docker-compose logs file-organizer
```

### Cannot Access Web Interface

Ensure the ports are not being used by other applications:
```bash
# Check what's using port 8080
lsof -i :8080
```

### Permission Issues with Mounted Directories

Make sure the directories in your `.env` file exist and have the correct permissions:
```bash
# Create directories if they don't exist
mkdir -p ~/Downloads ~/Organized

# Check permissions
ls -la ~/Downloads ~/Organized
```

## Uninstallation

To completely remove the File Organizer AI Agent:

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: This will delete all data)
docker-compose down -v

# Delete the directory
cd ..
rm -rf file-organizer-agent
```

## Next Steps

For more advanced usage and configuration, please refer to the main [README.md](README.md) file. 