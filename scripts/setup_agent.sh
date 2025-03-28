#!/bin/bash

# File Organizer Agent Setup Script for n8n
# This script will set up the file organizer agent and configure n8n

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colorful messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    type "$1" &> /dev/null
}

# Function to get user input with default value
get_input() {
    local prompt=$1
    local default=$2
    local input
    
    if [ -n "$default" ]; then
        read -p "${prompt} [${default}]: " input
        echo "${input:-$default}"
    else
        read -p "${prompt}: " input
        echo "$input"
    fi
}

# Function to check if n8n is running
check_n8n() {
    if command_exists curl; then
        if curl -s http://localhost:5678/healthz > /dev/null; then
            return 0
        else
            return 1
        fi
    else
        # If curl is not available, try to check if n8n process is running
        if pgrep -x "n8n" > /dev/null; then
            return 0
        else
            return 1
        fi
    fi
}

# Print welcome message
print_message $BLUE "========================================================"
print_message $BLUE "     File Organizer AI Agent Setup for n8n on macOS     "
print_message $BLUE "========================================================"
echo ""

# Check if running on macOS
if [[ "$(uname)" != "Darwin" ]]; then
    print_message $RED "This script is designed for macOS. Please run it on a Mac."
    exit 1
fi

# Check for required dependencies
print_message $YELLOW "Checking for required dependencies..."

# Check for Homebrew
if ! command_exists brew; then
    print_message $RED "Homebrew is not installed. Please install it first:"
    echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Check for Python
if ! command_exists python3; then
    print_message $YELLOW "Installing Python..."
    brew install python
else
    print_message $GREEN "Python is installed."
fi

# Check for Node.js
if ! command_exists node; then
    print_message $YELLOW "Installing Node.js..."
    brew install node
else
    print_message $GREEN "Node.js is installed."
fi

# Check for n8n
if ! command_exists n8n; then
    print_message $YELLOW "Installing n8n..."
    npm install n8n -g
else
    print_message $GREEN "n8n is installed."
fi

# Create directories
print_message $YELLOW "Setting up directories..."
mkdir -p ~/n8n-data
mkdir -p ~/.config/file_organizer

# Setup Agent
print_message $YELLOW "Setting up File Organizer Agent..."

# Install Python dependencies
print_message $YELLOW "Installing Python dependencies..."
pip3 install -r requirements.txt

# Generate API key
API_KEY=$(openssl rand -hex 24)
print_message $GREEN "Generated API key: $API_KEY"

# Create agent configuration
print_message $YELLOW "Creating agent configuration..."
cat > ~/.config/file_organizer/config.json << EOL
{
    "source_directory": "$(get_input "Enter source directory" "~/Downloads")",
    "target_directory": "$(get_input "Enter target directory" "~/Organized")",
    "organize_by": "$(get_input "Organization method (extension, date, size)" "extension")",
    "api_keys": {
        "default": "${API_KEY}"
    }
}
EOL

# Set up environment variables
print_message $YELLOW "Setting up environment variables..."
DOTENV_PATH=~/.config/file_organizer/.env

cat > $DOTENV_PATH << EOL
FILE_ORGANIZER_API_KEY=${API_KEY}
FILE_ORGANIZER_CONFIG=~/.config/file_organizer/config.json
FILE_ORGANIZER_PORT=3333
FILE_ORGANIZER_HOST=localhost
EOL

# Setup n8n
print_message $YELLOW "Setting up n8n..."

# Create n8n .env file
print_message $YELLOW "Creating n8n configuration..."
cat > ~/n8n-data/.env << EOL
N8N_BASIC_AUTH_ACTIVE=false
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=localhost
N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)
EOL

# Create launch agent for n8n
print_message $YELLOW "Creating launch agent for n8n..."
cat > ~/Library/LaunchAgents/com.n8n.agent.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.n8n.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/n8n</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>~/n8n-data</string>
    <key>StandardOutPath</key>
    <string>~/n8n-data/logs/n8n.log</string>
    <key>StandardErrorPath</key>
    <string>~/n8n-data/logs/n8n-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOL

# Create launch agent for the File Organizer API
print_message $YELLOW "Creating launch agent for File Organizer API..."
cat > ~/Library/LaunchAgents/com.file-organizer.agent.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.file-organizer.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>$(pwd)/agent_api_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>StandardOutPath</key>
    <string>~/n8n-data/logs/file-organizer.log</string>
    <key>StandardErrorPath</key>
    <string>~/n8n-data/logs/file-organizer-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>FILE_ORGANIZER_API_KEY</key>
        <string>${API_KEY}</string>
        <key>FILE_ORGANIZER_CONFIG</key>
        <string>~/.config/file_organizer/config.json</string>
    </dict>
</dict>
</plist>
EOL

# Create launch agent for the Auto Organizer
print_message $YELLOW "Creating launch agent for Auto Organizer..."
cat > ~/Library/LaunchAgents/com.auto-organizer.agent.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.auto-organizer.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>$(pwd)/auto_organizer.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$(pwd)</string>
    <key>StandardOutPath</key>
    <string>~/n8n-data/logs/auto-organizer.log</string>
    <key>StandardErrorPath</key>
    <string>~/n8n-data/logs/auto-organizer-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOL

# Create logs directory
mkdir -p ~/n8n-data/logs

# Start services
print_message $YELLOW "Starting services..."

# Unload launch agents if they exist
launchctl unload ~/Library/LaunchAgents/com.n8n.agent.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.file-organizer.agent.plist 2>/dev/null
launchctl unload ~/Library/LaunchAgents/com.auto-organizer.agent.plist 2>/dev/null

# Load launch agents
launchctl load ~/Library/LaunchAgents/com.n8n.agent.plist
launchctl load ~/Library/LaunchAgents/com.file-organizer.agent.plist
launchctl load ~/Library/LaunchAgents/com.auto-organizer.agent.plist

# Wait for n8n to start
print_message $YELLOW "Waiting for n8n to start..."
for i in {1..30}; do
    if check_n8n; then
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

if check_n8n; then
    print_message $GREEN "n8n is running!"
else
    print_message $RED "n8n did not start properly. Please check the logs at ~/n8n-data/logs/n8n.log"
fi

# Import workflow template
print_message $YELLOW "Importing workflow template to n8n..."
n8n import:workflow --input="$(pwd)/n8n_workflow_template.json"

# Final instructions
print_message $GREEN "=============== Setup Complete ==============="
print_message $BLUE "File Organizer Agent has been set up successfully!"
echo ""
print_message $YELLOW "You can access n8n at: http://localhost:5678"
print_message $YELLOW "The File Organizer API is available at: http://localhost:3333"
echo ""
print_message $BLUE "Important Information:"
echo "API Key: ${API_KEY}"
echo "Configuration file: ~/.config/file_organizer/config.json"
echo "n8n logs: ~/n8n-data/logs/n8n.log"
echo "File Organizer logs: ~/n8n-data/logs/file-organizer.log"
echo "Auto Organizer logs: ~/n8n-data/logs/auto-organizer.log"
echo ""
print_message $YELLOW "Next Steps:"
echo "1. Open n8n (http://localhost:5678)"
echo "2. Go to Workflows and activate the 'File Organizer Agent' workflow"
echo "3. Set the environment variables under Workflows > File Organizer Agent > Settings > Variables"
echo "   - FILE_ORGANIZER_API_URL: http://localhost:3333"
echo "   - FILE_ORGANIZER_API_KEY: ${API_KEY}"
echo "   - WATCH_FOLDER: Path to your source directory"
echo ""
print_message $BLUE "Auto Organizer Information:"
echo "The Auto Organizer is running and will:"
echo "- Monitor and automatically restart services if they crash"
echo "- Fix permissions on directories automatically"
echo "- Organize files in your configured directories periodically"
echo ""
print_message $GREEN "Enjoy your organized files! 🎉" 