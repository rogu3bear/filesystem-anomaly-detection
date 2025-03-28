# Filesystem Anomaly Detection

[NOTE] This release has restructured the project. The backend agent is now located in "n8n-agent-hub/backend" and the frontend in "n8n-agent-hub/frontend". Legacy files and directories have been removed and paths updated accordingly.

# File Organizer AI Agent for n8n

A complete solution for automatically organizing files using n8n and a custom AI agent, optimized for macOS.

## Features

- **Automated File Organization**: Automatically organize files by extension, date, or size
- **Configurable Rules**: Define custom rules for file organization
- **n8n Integration**: Seamlessly integrates with n8n for automation workflows
- **Easy Setup**: Simple setup process with an automated installation script
- **macOS Optimized**: Built with macOS best practices in mind, using launchd for service management
- **Self-Managing**: Auto Organizer monitors and automatically recovers services, fixes permissions, and performs regular organization
- **Web Interface**: User-friendly web dashboard to manage your file organization
- **Docker Support**: Run everything in a containerized environment for easy deployment
- **NEW!** Advanced customization options for performance, notifications, and file handling
- **NEW!** Automated desktop and email notifications
- **NEW!** Thread-based file processing for improved performance
- **NEW!** Image compression and archive extraction options

## Getting Started

### Option 1: Docker Installation (Recommended)

The easiest way to set up File Organizer is using Docker:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/file-organizer-agent.git
   cd file-organizer-agent
   ```

2. Run the Docker installation script:
   ```bash
   chmod +x install_docker.sh
   ./install_docker.sh
   ```

3. The script will:
   - Install Docker Desktop on macOS if not already installed
   - Create a Docker container with the File Organizer
   - Configure the required environment
   - Start all services

4. Once installed, access the web interface at http://localhost:8080

### Option 2: Native Installation

If you prefer a native installation without Docker:

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/file-organizer-agent.git
   cd file-organizer-agent
   ```

2. Run the setup script:
   ```bash
   chmod +x setup_agent.sh
   ./setup_agent.sh
   ```

3. The setup script will:
   - Install required dependencies
   - Configure the File Organizer AI Agent
   - Set up n8n without authentication
   - Create launch agents for all services
   - Import the workflow template into n8n
   - Generate and configure API keys

4. Follow the on-screen instructions to complete the setup.

## Using the Web Interface

After installation, you can access the File Organizer web interface:

- **Docker installation**: http://localhost:8080
- **Native installation**: http://localhost:8080

The web interface provides:

1. **Dashboard**: Overview of service status
2. **On-Demand Organization**: Run file organization on specific directories
3. **Configuration**: Update settings for the organizer
4. **API Key Management**: View and copy your API key for external integrations

## Auto Organizer

The Auto Organizer is a self-managing wrapper for the File Organizer AI Agent that:

- **Monitors services** and automatically restarts them if they crash
- **Fixes permissions** on directories automatically
- **Periodically organizes** configured directories without manual intervention
- **Ensures n8n integration** is properly configured

To use the Auto Organizer outside of Docker:

```bash
# Start the Auto Organizer
python3 auto_organizer.py

# Start with custom configuration and interval
python3 auto_organizer.py --config ~/.config/my_custom_config.json --interval 300
```

### Auto Organizer Configuration

The Auto Organizer adds these additional configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| `auto_fix_permissions` | Automatically fix directory permissions | `true` |
| `auto_recovery` | Restart services if they crash | `true` |
| `monitor_directories` | Periodically organize configured directories | `true` |
| `watch_directories` | List of directories to monitor and organize | `["~/Downloads", "~/Documents"]` |

## Docker Configuration

The Docker container is configured using environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `SOURCE_DIR` | Directory to monitor for files | `~/Downloads` |
| `TARGET_DIR` | Directory where files will be organized | `~/Organized` |
| `API_KEY` | Custom API key for authentication | Generated automatically |
| `TZ` | Timezone for the container | System timezone |

To modify these settings, edit the `.env` file and restart the container:

```bash
docker-compose restart
```

## Manual Setup

If you prefer to set things up manually or the setup script doesn't work for you, follow these steps:

### Installing Dependencies

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Node.js
brew install python node

# Install n8n
npm install n8n -g

# Install Python dependencies
pip3 install -r requirements.txt
```

### Configuring the Agent

1. Create the configuration directory:
   ```bash
   mkdir -p ~/.config/file_organizer
   ```

2. Create a configuration file:
   ```bash
   cat > ~/.config/file_organizer/config.json << EOL
   {
       "source_directory": "~/Downloads",
       "target_directory": "~/Organized",
       "organize_by": "extension",
       "api_keys": {
           "default": "your-secret-api-key"
       }
   }
   EOL
   ```

### Setting Up n8n

Follow the instructions in the [setup_instructions.md](setup_instructions.md) file.

## API Endpoints

The File Organizer API provides the following endpoints:

- `GET /health`: Health check endpoint
- `POST /organize`: Organize files according to the provided configuration
- `GET /config`: Get the current configuration
- `POST /config`: Update the configuration

All endpoints except `/health` require an API key to be provided in the `X-API-Key` header.

## Configuration Options

The File Organizer agent supports the following configuration options:

| Option | Description | Default |
|--------|-------------|---------|
| `source_directory` | Directory to monitor for files | `~/Downloads` |
| `target_directory` | Directory where files will be organized | `~/Organized` |
| `organize_by` | Organization method (`extension`, `date`, `size`) | `extension` |
| `rules` | Custom organization rules by file extension | See config file |
| `exclude_files` | Files to exclude from organization | `.DS_Store`, `Thumbs.db` |
| `exclude_dirs` | Directories to exclude from organization | `.git`, `node_modules` |
| `duplicate_handling` | How to handle duplicate files (`rename`, `overwrite`, `skip`) | `rename` |

## Troubleshooting

### Docker Installation

If you encounter issues with the Docker installation:

1. Check the container logs:
   ```bash
   docker-compose logs file-organizer
   ```

2. Restart the container:
   ```bash
   docker-compose restart file-organizer
   ```

3. Rebuild the container if configuration changes were made:
   ```bash
   docker-compose up -d --build
   ```

### Native Installation

If you're using the native installation:

1. Check log files for error messages:
   - n8n logs: `~/n8n-data/logs/n8n.log`
   - File Organizer logs: `~/n8n-data/logs/file-organizer.log`
   - Auto Organizer logs: `auto_organizer.log`
   - Web Interface logs: `web_interface.log`

2. Restart services manually:
   ```bash
   # Restart n8n
   launchctl unload ~/Library/LaunchAgents/com.n8n.agent.plist
   launchctl load ~/Library/LaunchAgents/com.n8n.agent.plist

   # Restart File Organizer API
   launchctl unload ~/Library/LaunchAgents/com.file-organizer.agent.plist
   launchctl load ~/Library/LaunchAgents/com.file-organizer.agent.plist

   # Using Auto Organizer (recommended)
   python3 auto_organizer.py
   ```

## Security Considerations

- The n8n instance is configured without authentication for simplicity. It's recommended to not expose it to the public internet.
- The File Organizer API uses an API key for authentication. Keep this key secure.
- Consider enabling the macOS firewall to restrict network access to these services.
- When using Docker, be cautious about mounting sensitive directories into the container.

## License

MIT License

## Acknowledgements

- [n8n](https://n8n.io/) - Workflow automation tool
- [Flask](https://flask.palletsprojects.com/) - Web framework for the API and interface
- [Homebrew](https://brew.sh/) - Package manager for macOS
- [Docker](https://www.docker.com/) - Containerization platform

## Advanced Customization Options

The latest version of File Organizer AI Agent includes these powerful customization options:

### Custom File Categories
- Create your own file categories with specific extensions
- Modify existing categories to match your workflow
- Organize files exactly how you want them

### Advanced File Handling
- Set minimum and maximum file size thresholds
- Define minimum file age before processing (avoids processing files still being written)
- Optional automatic image compression to save space
- Optional automatic archive extraction

### Performance Tuning
- Control thread count for parallel file processing
- Set batch sizes for optimized memory usage
- Memory limit controls for large operations

### Notification Preferences
- Desktop notifications when organization completes
- Email notifications for summaries and errors
- Customizable notification frequency

### User Interface Options
- Choose between light and dark themes
- Customize dashboard elements
- Control statistics and file information display

All these options can be configured during setup or later through the web interface. 