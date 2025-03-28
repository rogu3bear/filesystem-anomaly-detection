#!/bin/bash

# Filesystem Anomaly Detection - Automated Setup Script
# This script handles n8n installation and configuration without requiring credentials

# Color definitions for better user experience
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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_message $RED "Please do not run this script as root. It will use sudo when necessary."
    exit 1
fi

# Function to check if a command exists
command_exists() {
    type "$1" &> /dev/null
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unsupported"
    fi
}

OS=$(detect_os)
if [ "$OS" == "unsupported" ]; then
    print_message $RED "Unsupported operating system. This script works on macOS and Linux."
    exit 1
fi

# Function to check if n8n is already installed
check_n8n_installed() {
    if command_exists n8n; then
        return 0
    else
        return 1
    fi
}

# Function to check if n8n is already running
check_n8n_running() {
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

# Function to install dependencies based on OS
install_dependencies() {
    print_message $YELLOW "Installing dependencies..."
    
    if [ "$OS" == "macos" ]; then
        # Check for Homebrew
        if ! command_exists brew; then
            print_message $YELLOW "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Check for Node.js
        if ! command_exists node; then
            print_message $YELLOW "Installing Node.js..."
            brew install node
        else
            print_message $GREEN "Node.js is already installed."
        fi
        
    elif [ "$OS" == "linux" ]; then
        # Check for Node.js
        if ! command_exists node; then
            print_message $YELLOW "Installing Node.js..."
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        else
            print_message $GREEN "Node.js is already installed."
        fi
    fi
    
    # Check npm version
    if ! command_exists npm; then
        print_message $RED "npm is not installed. Please install Node.js properly."
        exit 1
    fi
    
    print_message $GREEN "All dependencies installed successfully."
}

# Function to install n8n
install_n8n() {
    print_message $YELLOW "Installing n8n..."
    
    if check_n8n_installed; then
        print_message $GREEN "n8n is already installed."
    else
        # Install n8n globally
        npm install n8n -g
        
        if check_n8n_installed; then
            print_message $GREEN "n8n installed successfully."
        else
            print_message $RED "Failed to install n8n. Please try installing it manually."
            exit 1
        fi
    fi
}

# Function to setup n8n directories and configuration
setup_n8n() {
    print_message $YELLOW "Setting up n8n configuration..."
    
    # Create data directory for n8n
    mkdir -p ~/.n8n
    
    # Create configuration file without authentication
    cat > ~/.n8n/.env << EOL
N8N_BASIC_AUTH_ACTIVE=false
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=localhost
N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)
EOL
    
    print_message $GREEN "n8n configuration created successfully."
}

# Function to setup the agent
setup_agent() {
    print_message $YELLOW "Setting up Filesystem Anomaly Detection agent..."
    
    # Create configuration directory
    mkdir -p ~/.config/file_anomaly_detection
    
    # Generate secure API key
    API_KEY=$(openssl rand -hex 24)
    
    # Create agent configuration
    cat > ~/.config/file_anomaly_detection/config.json << EOL
{
    "source_directory": "$HOME/Downloads",
    "target_directory": "$HOME/Organized",
    "organize_by": "extension",
    "scan_interval": 300,
    "api_key": "${API_KEY}"
}
EOL
    
    # Setup directory structure for file organization
    mkdir -p "$HOME/Organized"
    mkdir -p "$HOME/Organized/Documents"
    mkdir -p "$HOME/Organized/Images"
    mkdir -p "$HOME/Organized/Videos"
    mkdir -p "$HOME/Organized/Audio"
    mkdir -p "$HOME/Organized/Archives"
    mkdir -p "$HOME/Organized/Applications"
    mkdir -p "$HOME/Organized/Other"
    
    print_message $GREEN "Agent configuration created successfully."
    print_message $BLUE "API Key: ${API_KEY} (keep this secure!)"
}

# Function to setup service for automatic startup
setup_service() {
    print_message $YELLOW "Setting up service for automatic startup..."
    
    if [ "$OS" == "macos" ]; then
        # Create launchd plist file for n8n
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
    <string>${HOME}/.n8n</string>
    <key>StandardOutPath</key>
    <string>${HOME}/.n8n/logs/n8n.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/.n8n/logs/n8n-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOL
        
        # Create logs directory
        mkdir -p ~/.n8n/logs
        
        # Unload and load the launch agent
        launchctl unload ~/Library/LaunchAgents/com.n8n.agent.plist 2>/dev/null
        launchctl load ~/Library/LaunchAgents/com.n8n.agent.plist
        
    elif [ "$OS" == "linux" ]; then
        # Create systemd service file
        cat > /tmp/n8n.service << EOL
[Unit]
Description=n8n Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/.n8n
ExecStart=/usr/bin/n8n start
Restart=always
RestartSec=10
StandardOutput=file:$HOME/.n8n/logs/n8n.log
StandardError=file:$HOME/.n8n/logs/n8n-error.log

[Install]
WantedBy=multi-user.target
EOL
        
        # Create logs directory
        mkdir -p ~/.n8n/logs
        
        # Copy service file to systemd directory and enable it
        sudo cp /tmp/n8n.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable n8n.service
        sudo systemctl start n8n.service
    fi
    
    print_message $GREEN "Service setup completed successfully."
}

# Function to setup n8n workflow
setup_workflow() {
    print_message $YELLOW "Setting up n8n workflow..."
    
    # Wait for n8n to start
    print_message $YELLOW "Waiting for n8n to start..."
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if check_n8n_running; then
            print_message $GREEN "n8n is running!"
            break
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    
    if ! check_n8n_running; then
        print_message $RED "n8n did not start properly. Please check the logs at ~/.n8n/logs/n8n.log"
    else
        # Import workflow template (path relative to the script's location)
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        WORKFLOW_TEMPLATE="$SCRIPT_DIR/../n8n_workflow_template.json"
        
        if [ -f "$WORKFLOW_TEMPLATE" ]; then
            n8n import:workflow --input="$WORKFLOW_TEMPLATE"
            print_message $GREEN "Workflow imported successfully."
        else
            print_message $RED "Workflow template not found at $WORKFLOW_TEMPLATE"
        fi
    fi
}

# Function to launch setup GUI
launch_setup_gui() {
    print_message $YELLOW "Launching setup GUI..."
    
    # Navigate to the frontend directory
    cd "$(dirname "$0")/../frontend"
    
    # Check if build exists and install if needed
    if [ ! -d "build" ] || [ ! -f "build/index.html" ]; then
        print_message $YELLOW "Building setup interface..."
        npm install
        npm run build
    fi
    
    # Launch the setup GUI in the default browser
    if [ "$OS" == "macos" ]; then
        open "http://localhost:3000/setup"
    elif [ "$OS" == "linux" ]; then
        xdg-open "http://localhost:3000/setup"
    fi
    
    # Start the server for setup
    cd "$(dirname "$0")/../backend"
    npm install
    npm run setup-server
}

# Main installation process
print_message $BLUE "========================================================"
print_message $BLUE "     Filesystem Anomaly Detection - Setup Wizard        "
print_message $BLUE "========================================================"
echo ""

# Check for existing installation
if check_n8n_installed && check_n8n_running; then
    print_message $GREEN "n8n is already installed and running."
    print_message $YELLOW "Do you want to reconfigure the installation? (y/n)"
    read -r reconfigure
    
    if [[ "$reconfigure" != "y" && "$reconfigure" != "Y" ]]; then
        print_message $BLUE "Launching setup GUI with existing installation..."
        launch_setup_gui
        exit 0
    fi
fi

# Install dependencies
install_dependencies

# Install n8n
install_n8n

# Setup n8n
setup_n8n

# Setup agent
setup_agent

# Setup service
setup_service

# Setup workflow
setup_workflow

# Launch setup GUI
launch_setup_gui

print_message $GREEN "=============== Setup Complete ==============="
print_message $BLUE "Filesystem Anomaly Detection has been set up successfully!"
echo ""
print_message $YELLOW "You can access n8n at: http://localhost:5678"
print_message $YELLOW "The setup interface is available at: http://localhost:3000/setup"
echo ""
print_message $BLUE "Important Information:"
echo "API Key: ${API_KEY}"
echo "Configuration file: ~/.config/file_anomaly_detection/config.json"
echo "n8n logs: ~/.n8n/logs/n8n.log"
echo ""
print_message $GREEN "Enjoy your organized files! 🎉" 