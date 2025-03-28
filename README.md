# Filesystem Anomaly Detection

A powerful, automated file organization system built on n8n workflows. This tool helps you organize your files intelligently with a user-friendly web interface.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- 🔍 **Automated File Organization**: Automatically sort files based on type, date, or custom rules
- 🌐 **Web Interface**: User-friendly dashboard to monitor and control file organization
- 🔄 **n8n Integration**: Leverage n8n workflows for powerful automation capabilities
- 🛠️ **Customizable Rules**: Define your own organization rules and filters
- 📱 **Cross-Platform**: Works on macOS, Linux, and Windows
- 🔒 **Secure**: API key authentication and local-only deployment for privacy

## Table of Contents

- [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Manual Installation](#manual-installation)
  - [Docker Installation](#docker-installation)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [Configuration](#configuration)
  - [Workflows](#workflows)
- [Customization](#customization)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Installation

### Prerequisites

- Node.js 16+ and npm
- Basic familiarity with terminal/command line

### Quick Start

The easiest way to get started is with our setup script:

```bash
# Clone the repository
git clone https://github.com/rogu3bear/FilesystemAnomalyDetection.git
cd FilesystemAnomalyDetection

# Run the setup script
./n8n-agent-hub/scripts/setup.sh
```

The setup script will:
1. Install dependencies (Node.js, npm, etc.)
2. Install n8n globally or locally
3. Configure the application with defaults
4. Launch the setup interface

### Manual Installation

If you prefer manual installation:

#### 1. Install n8n

```bash
# Global installation (recommended)
npm install n8n -g

# OR local installation
npm install n8n --global --prefix ~/.npm
export PATH="$HOME/.npm/bin:$PATH"
```

#### 2. Install application dependencies

```bash
cd FilesystemAnomalyDetection/n8n-agent-hub/backend
npm install
npm run build

cd ../frontend
npm install
npm run build
```

#### 3. Configure the application

Create configuration file:

```bash
mkdir -p ~/.config/file_anomaly_detection
API_KEY=$(openssl rand -hex 24)

cat > ~/.config/file_anomaly_detection/config.json << EOL
{
    "source_directory": "$HOME/Downloads",
    "target_directory": "$HOME/Organized",
    "organize_by": "extension",
    "scan_interval": 300,
    "api_key": "${API_KEY}",
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "version": "1.0"
}
EOL

# Create target directories
mkdir -p ~/Organized/{Documents,Images,Videos,Audio,Archives,Applications,Other}
```

#### 4. Launch the application

```bash
# Start n8n
n8n start &

# Start the application server
cd FilesystemAnomalyDetection/n8n-agent-hub/backend
npm run setup-server
```

### Docker Installation

You can also run the entire system using Docker:

```bash
cd FilesystemAnomalyDetection
docker-compose up -d
```

This will start n8n, the backend, and the frontend in separate containers.

## Usage

### Web Interface

After installation, access the web interface at:

- Setup interface: http://localhost:3000/setup
- Main dashboard: http://localhost:3000
- n8n interface: http://localhost:5678

### Configuration

The main configuration file is located at:

```
~/.config/file_anomaly_detection/config.json
```

Key configuration options:

| Option | Description |
|--------|-------------|
| `source_directory` | Directory to monitor for files |
| `target_directory` | Directory where files are organized |
| `organize_by` | Organization method (`extension`, `date`, `type`, or `size`) |
| `scan_interval` | How often to scan for new files (in seconds) |
| `api_key` | API key for secure access |

### Workflows

The system uses n8n workflows to process files. You can view and modify these workflows in the n8n interface at http://localhost:5678.

Default workflows:

- **File Organization**: Automatically organizes files by type
- **Cleanup**: Removes empty directories and temporary files
- **Notification**: Sends notifications when files are processed

## Customization

### Custom Organization Rules

You can modify the organization rules by editing the workflow in n8n:

1. Open http://localhost:5678
2. Go to the "File Organization" workflow
3. Modify the "Switch" node to change the file classification rules

### Adding Custom File Types

To add custom file type recognition:

1. Edit the n8n workflow
2. Add new file extensions to the appropriate categories
3. Save and activate the workflow

### Scheduling and Automation

You can customize when and how files are organized:

1. In n8n, modify the "Timer" node in the workflow
2. Change the execution schedule
3. Save and activate the workflow

## Development

To contribute to development:

```bash
# Clone the repository
git clone https://github.com/rogu3bear/FilesystemAnomalyDetection.git
cd FilesystemAnomalyDetection

# Install dependencies
cd n8n-agent-hub/backend
npm install
npm run dev

# In another terminal
cd n8n-agent-hub/frontend
npm install
npm start
```

### Project Structure

- `n8n-agent-hub/backend`: Express.js backend server
- `n8n-agent-hub/frontend`: React frontend application
- `n8n-agent-hub/scripts`: Helper scripts for installation and setup
- `scripts`: System-level scripts for various platforms

## Troubleshooting

### Common Issues

#### n8n won't start

```bash
# Check if n8n is in your PATH
which n8n

# Try starting manually
n8n start

# Check logs
cat ~/.n8n/logs/n8n.log
```

#### API connection issues

```bash
# Check if backend is running
curl http://localhost:3000/api/setup/status

# Check configuration file
cat ~/.config/file_anomaly_detection/config.json
```

#### Permission issues

Ensure your source and target directories have proper permissions:

```bash
chmod 755 ~/Downloads
chmod 755 ~/Organized
```

### Getting Help

If you encounter issues:

1. Check the logs at `~/.n8n/logs/n8n.log`
2. Open an issue on GitHub
3. Check the troubleshooting section in documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [n8n](https://n8n.io/) for the excellent workflow automation platform
- Contributors and maintainers of this project

---

**Note**: This is a personal project and is not affiliated with n8n GmbH. 