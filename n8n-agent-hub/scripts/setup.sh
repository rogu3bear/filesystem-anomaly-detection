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

# Trap errors for better error handling
set -o pipefail
trap 'echo -e "${RED}Error occurred at line $LINENO. Command: $BASH_COMMAND${NC}"; exit 1' ERR

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
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    else
        echo "unsupported"
    fi
}

OS=$(detect_os)
if [ "$OS" == "unsupported" ]; then
    print_message $RED "Unsupported operating system. This script works on macOS, Linux, and Windows (via Git Bash)."
    exit 1
fi

# Function to check if n8n is already installed
check_n8n_installed() {
    if command_exists n8n; then
        return 0
    else
        # Try to find n8n in common locations
        if [ -f ~/.npm/bin/n8n ] || [ -f /usr/local/bin/n8n ] || [ -f /usr/bin/n8n ]; then
            return 0
        else
            return 1
        fi
    fi
}

# Function to check if n8n is already running
check_n8n_running() {
    if command_exists curl; then
        if curl -s http://localhost:5678/healthz -m 3 > /dev/null; then
            return 0
        else
            return 1
        fi
    else
        # If curl is not available, try to check if n8n process is running
        if command_exists pgrep && pgrep -x "n8n" > /dev/null; then
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
            
            # Add Homebrew to PATH if it was just installed
            if [ -f ~/.zshrc ]; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
                eval "$(/opt/homebrew/bin/brew shellenv)"
            elif [ -f ~/.bash_profile ]; then
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.bash_profile
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
        fi
        
        # Check for Node.js
        if ! command_exists node; then
            print_message $YELLOW "Installing Node.js..."
            brew install node
        else
            print_message $GREEN "Node.js is already installed."
        fi
        
        # Check for curl
        if ! command_exists curl; then
            print_message $YELLOW "Installing curl..."
            brew install curl
        fi
        
    elif [ "$OS" == "linux" ]; then
        # Detect package manager
        PKG_MANAGER=""
        if command_exists apt-get; then
            PKG_MANAGER="apt"
        elif command_exists dnf; then
            PKG_MANAGER="dnf"
        elif command_exists yum; then
            PKG_MANAGER="yum"
        elif command_exists pacman; then
            PKG_MANAGER="pacman"
        fi
        
        if [ -z "$PKG_MANAGER" ]; then
            print_message $RED "Unable to detect package manager. Please install Node.js manually."
            exit 1
        fi
        
        # Check for Node.js
        if ! command_exists node; then
            print_message $YELLOW "Installing Node.js..."
            case "$PKG_MANAGER" in
                apt)
                    sudo apt-get update
                    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                    sudo apt-get install -y nodejs
                    ;;
                dnf)
                    sudo dnf install -y nodejs
                    ;;
                yum)
                    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
                    sudo yum install -y nodejs
                    ;;
                pacman)
                    sudo pacman -S nodejs npm
                    ;;
            esac
        else
            print_message $GREEN "Node.js is already installed."
        fi
        
        # Check for curl
        if ! command_exists curl; then
            print_message $YELLOW "Installing curl..."
            case "$PKG_MANAGER" in
                apt)
                    sudo apt-get install -y curl
                    ;;
                dnf|yum)
                    sudo $PKG_MANAGER install -y curl
                    ;;
                pacman)
                    sudo pacman -S curl
                    ;;
            esac
        fi
    elif [ "$OS" == "windows" ]; then
        print_message $YELLOW "On Windows, please ensure Node.js is installed from https://nodejs.org/"
        print_message $YELLOW "This script assumes you're running in Git Bash or similar environment."
        
        if ! command_exists node; then
            print_message $RED "Node.js not found. Please install it from https://nodejs.org/"
            print_message $YELLOW "After installing, restart this script."
            exit 1
        else
            print_message $GREEN "Node.js is already installed."
        fi
    fi
    
    # Check npm version
    if ! command_exists npm; then
        print_message $RED "npm is not installed. Please install Node.js properly."
        exit 1
    fi
    
    # Install pm2 for process management if not installed
    if ! command_exists pm2; then
        print_message $YELLOW "Installing pm2 for process management..."
        npm install pm2 -g
    fi
    
    print_message $GREEN "All dependencies installed successfully."
}

# Function to install n8n
install_n8n() {
    print_message $YELLOW "Installing n8n..."
    
    if check_n8n_installed; then
        print_message $GREEN "n8n is already installed."
    else
        # Check if we can install globally
        local INSTALL_DIR="/usr/local/bin"
        local GLOBAL=true
        
        # Test if we can write to the global directory
        if ! touch "$INSTALL_DIR/.n8n-test" 2>/dev/null; then
            print_message $YELLOW "Cannot write to $INSTALL_DIR. Installing n8n locally..."
            GLOBAL=false
            
            # Update PATH to include user npm bin directory
            mkdir -p "$HOME/.npm/bin"
            export PATH="$HOME/.npm/bin:$PATH"
            
            # Install n8n locally
            npm install n8n --global --prefix "$HOME/.npm"
            
            # Add to PATH in shell config if not already present
            local SHELL_CONFIG=""
            if [ -f "$HOME/.zshrc" ]; then
                SHELL_CONFIG="$HOME/.zshrc"
            elif [ -f "$HOME/.bashrc" ]; then
                SHELL_CONFIG="$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                SHELL_CONFIG="$HOME/.bash_profile"
            fi
            
            if [ -n "$SHELL_CONFIG" ]; then
                if ! grep -q "HOME/.npm/bin" "$SHELL_CONFIG"; then
                    echo 'export PATH="$HOME/.npm/bin:$PATH"' >> "$SHELL_CONFIG"
                    print_message $YELLOW "Added ~/.npm/bin to PATH in $SHELL_CONFIG"
                    print_message $YELLOW "Please run 'source $SHELL_CONFIG' after this script completes."
                fi
            else
                print_message $YELLOW "Please add $HOME/.npm/bin to your PATH manually."
            fi
        else
            # Remove test file and install globally
            rm -f "$INSTALL_DIR/.n8n-test"
            npm install n8n -g
        fi
        
        if check_n8n_installed; then
            print_message $GREEN "n8n installed successfully."
        else
            print_message $RED "Failed to install n8n. Please try installing it manually:"
            print_message $YELLOW "npm install n8n -g"
            exit 1
        fi
    fi
}

# Function to setup n8n directories and configuration
setup_n8n() {
    print_message $YELLOW "Setting up n8n configuration..."
    
    # Create data directory for n8n
    mkdir -p ~/.n8n
    
    # Generate secure encryption key
    ENCRYPTION_KEY=$(openssl rand -hex 24 2>/dev/null || head -c 24 /dev/urandom | xxd -p)
    
    # Create configuration file without authentication
    cat > ~/.n8n/.env << EOL
N8N_BASIC_AUTH_ACTIVE=false
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=localhost
N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Uncomment and modify these lines if you want email notifications
# N8N_EMAIL_MODE=smtp
# N8N_SMTP_HOST=smtp.example.com
# N8N_SMTP_PORT=587
# N8N_SMTP_USER=user@example.com
# N8N_SMTP_PASS=password
# N8N_SMTP_SENDER=n8n@example.com
EOL
    
    # Set proper permissions
    chmod 600 ~/.n8n/.env
    
    print_message $GREEN "n8n configuration created successfully."
}

# Function to setup the agent
setup_agent() {
    print_message $YELLOW "Setting up Filesystem Anomaly Detection agent..."
    
    # Create configuration directory
    CONFIG_DIR="$HOME/.config/file_anomaly_detection"
    mkdir -p "$CONFIG_DIR"
    
    # Generate secure API key
    API_KEY=$(openssl rand -hex 24 2>/dev/null || head -c 24 /dev/urandom | xxd -p)
    
    # Determine default paths based on OS
    if [ "$OS" == "windows" ]; then
        DEFAULT_SOURCE_DIR=$(cygpath -u "${USERPROFILE:-$HOME}/Downloads" 2>/dev/null || echo "$HOME/Downloads")
        DEFAULT_TARGET_DIR=$(cygpath -u "${USERPROFILE:-$HOME}/Organized" 2>/dev/null || echo "$HOME/Organized")
    else
        DEFAULT_SOURCE_DIR="$HOME/Downloads"
        DEFAULT_TARGET_DIR="$HOME/Organized"
    fi
    
    # Get user input for directories with defaults
    read -p "Source directory [$DEFAULT_SOURCE_DIR]: " SOURCE_DIR
    SOURCE_DIR="${SOURCE_DIR:-$DEFAULT_SOURCE_DIR}"
    
    read -p "Target directory [$DEFAULT_TARGET_DIR]: " TARGET_DIR
    TARGET_DIR="${TARGET_DIR:-$DEFAULT_TARGET_DIR}"
    
    # Create agent configuration
    cat > "$CONFIG_DIR/config.json" << EOL
{
    "source_directory": "${SOURCE_DIR}",
    "target_directory": "${TARGET_DIR}",
    "organize_by": "extension",
    "scan_interval": 300,
    "api_key": "${API_KEY}",
    "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "version": "1.0"
}
EOL
    
    # Set proper permissions
    chmod 600 "$CONFIG_DIR/config.json"
    
    # Setup directory structure for file organization
    mkdir -p "$TARGET_DIR"
    mkdir -p "$TARGET_DIR/Documents"
    mkdir -p "$TARGET_DIR/Images"
    mkdir -p "$TARGET_DIR/Videos"
    mkdir -p "$TARGET_DIR/Audio"
    mkdir -p "$TARGET_DIR/Archives"
    mkdir -p "$TARGET_DIR/Applications"
    mkdir -p "$TARGET_DIR/Other"
    
    print_message $GREEN "Agent configuration created successfully."
    print_message $BLUE "API Key: ${API_KEY} (keep this secure!)"
    print_message $BLUE "Configuration saved to: $CONFIG_DIR/config.json"
}

# Function to setup service for automatic startup
setup_service() {
    print_message $YELLOW "Setting up service for automatic startup..."
    
    if [ "$OS" == "macos" ]; then
        # Create logs directory
        mkdir -p ~/.n8n/logs
        
        # Find n8n path
        N8N_PATH=$(which n8n 2>/dev/null || echo "$HOME/.npm/bin/n8n")
        
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
        <string>${N8N_PATH}</string>
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
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${HOME}/.npm/bin</string>
    </dict>
</dict>
</plist>
EOL
        
        # Unload and load the launch agent
        launchctl unload ~/Library/LaunchAgents/com.n8n.agent.plist 2>/dev/null || true
        launchctl load ~/Library/LaunchAgents/com.n8n.agent.plist
        
    elif [ "$OS" == "linux" ]; then
        # Create logs directory
        mkdir -p ~/.n8n/logs
        
        # Find n8n path
        N8N_PATH=$(which n8n 2>/dev/null || echo "$HOME/.npm/bin/n8n")
        
        # Setup systemd user service if available
        if systemctl --user status >/dev/null 2>&1; then
            print_message $YELLOW "Setting up systemd user service..."
            
            mkdir -p ~/.config/systemd/user/
            
            # Create systemd user service file
            cat > ~/.config/systemd/user/n8n.service << EOL
[Unit]
Description=n8n Workflow Automation
After=network.target

[Service]
Type=simple
ExecStart=${N8N_PATH} start
WorkingDirectory=${HOME}/.n8n
Environment=NODE_ENV=production
Restart=always
StandardOutput=append:${HOME}/.n8n/logs/n8n.log
StandardError=append:${HOME}/.n8n/logs/n8n-error.log

[Install]
WantedBy=default.target
EOL
            
            # Reload systemd user daemon and enable/start service
            systemctl --user daemon-reload
            systemctl --user enable n8n.service
            systemctl --user restart n8n.service
            
            print_message $GREEN "systemd user service installed!"
            print_message $YELLOW "You can control the service with: systemctl --user [start|stop|restart] n8n"
        else
            # If systemd user services not available, use pm2
            print_message $YELLOW "systemd user services not available, using pm2..."
            
            # Create pm2 ecosystem file
            cat > ~/.n8n/ecosystem.config.js << EOL
module.exports = {
  apps: [{
    name: 'n8n',
    script: '${N8N_PATH}',
    args: 'start',
    cwd: '${HOME}/.n8n',
    log_file: '${HOME}/.n8n/logs/n8n.log',
    error_file: '${HOME}/.n8n/logs/n8n-error.log',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOL
            
            # Start with pm2 and save configuration
            pm2 start ~/.n8n/ecosystem.config.js
            pm2 save
            
            # Setup pm2 startup script
            STARTUP_CMD=$(pm2 startup | grep -o "sudo .*$")
            if [ -n "$STARTUP_CMD" ]; then
                print_message $YELLOW "To enable autostart on boot, run the following command:"
                print_message $BLUE "$STARTUP_CMD"
            fi
        fi
    elif [ "$OS" == "windows" ]; then
        print_message $YELLOW "On Windows, we'll use pm2 for process management..."
        
        # Create logs directory
        mkdir -p ~/.n8n/logs
        
        # Find n8n path
        N8N_PATH=$(which n8n 2>/dev/null || echo "$HOME/.npm/bin/n8n.cmd")
        
        # Create pm2 ecosystem file
        cat > ~/.n8n/ecosystem.config.js << EOL
module.exports = {
  apps: [{
    name: 'n8n',
    script: '${N8N_PATH}',
    args: 'start',
    cwd: '${HOME}/.n8n',
    log_file: '${HOME}/.n8n/logs/n8n.log',
    error_file: '${HOME}/.n8n/logs/n8n-error.log',
    env: {
      NODE_ENV: 'production'
    }
  }]
};
EOL
        
        # Start with pm2 and save configuration
        pm2 start ~/.n8n/ecosystem.config.js
        pm2 save
        
        # Setup pm2 startup script
        print_message $YELLOW "To enable autostart on boot, run the following command as Administrator:"
        print_message $BLUE "pm2-startup install"
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
        
        # Alternate locations to check for the workflow template
        ALTERNATE_LOCATIONS=(
            "$SCRIPT_DIR/n8n_workflow_template.json"
            "$(cd "$SCRIPT_DIR/.." && pwd)/n8n_workflow_template.json"
            "$(cd "$SCRIPT_DIR/../.." && pwd)/n8n_workflow_template.json"
        )
        
        if [ -f "$WORKFLOW_TEMPLATE" ]; then
            n8n import:workflow --input="$WORKFLOW_TEMPLATE"
            print_message $GREEN "Workflow imported successfully."
        else
            # Try alternate locations
            for LOCATION in "${ALTERNATE_LOCATIONS[@]}"; do
                if [ -f "$LOCATION" ]; then
                    n8n import:workflow --input="$LOCATION"
                    print_message $GREEN "Workflow imported successfully from $LOCATION."
                    break
                fi
            done
            
            if [ ! -f "$WORKFLOW_TEMPLATE" ] && [ ! -f "${ALTERNATE_LOCATIONS[0]}" ] && [ ! -f "${ALTERNATE_LOCATIONS[1]}" ] && [ ! -f "${ALTERNATE_LOCATIONS[2]}" ]; then
                print_message $YELLOW "Workflow template not found. You can import it manually in the n8n UI later."
            fi
        fi
    fi
}

# Function to launch setup GUI
launch_setup_gui() {
    print_message $YELLOW "Launching setup GUI..."
    
    # Navigate to the backend directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKEND_DIR="$SCRIPT_DIR/../backend"
    
    if [ ! -d "$BACKEND_DIR" ]; then
        print_message $YELLOW "Backend directory not found at $BACKEND_DIR"
        
        # Try to find the backend directory
        for POTENTIAL_DIR in "$SCRIPT_DIR/../n8n-agent-hub/backend" "$SCRIPT_DIR/../../n8n-agent-hub/backend"; do
            if [ -d "$POTENTIAL_DIR" ]; then
                BACKEND_DIR="$POTENTIAL_DIR"
                print_message $GREEN "Found backend at $BACKEND_DIR"
                break
            fi
        done
        
        if [ ! -d "$BACKEND_DIR" ]; then
            print_message $RED "Backend directory not found. Please run setup from the project root."
            return 1
        fi
    fi
    
    cd "$BACKEND_DIR"
    
    # Check if node_modules exists, if not, install dependencies
    if [ ! -d "node_modules" ]; then
        print_message $YELLOW "Installing backend dependencies..."
        npm install --no-audit --no-fund
    fi
    
    # Check if the build command exists
    if grep -q "\"build\"" package.json; then
        print_message $YELLOW "Building backend..."
        npm run build
    fi
    
    # Check if the frontend is built
    FRONTEND_DIR="$(dirname "$BACKEND_DIR")/frontend"
    if [ -d "$FRONTEND_DIR" ] && [ ! -d "$FRONTEND_DIR/build" ]; then
        print_message $YELLOW "Building frontend..."
        cd "$FRONTEND_DIR"
        if [ ! -d "node_modules" ]; then
            npm install --no-audit --no-fund
        fi
        npm run build
    fi
    
    # Return to backend directory
    cd "$BACKEND_DIR"
    
    # Run the setup server
    print_message $BLUE "Starting setup server..."
    print_message $BLUE "Once the server starts, you can access the setup interface at http://localhost:3000/setup"
    
    # Attempt to open browser automatically
    (sleep 3 && (
        if [ "$OS" == "macos" ]; then
            open "http://localhost:3000/setup"
        elif [ "$OS" == "linux" ]; then
            xdg-open "http://localhost:3000/setup" 2>/dev/null || true
        elif [ "$OS" == "windows" ]; then
            start "http://localhost:3000/setup" 2>/dev/null || true
        fi
    )) &
    
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

# Show installation options
print_message $BLUE "Installation Options:"
echo "1. Full Installation (Install dependencies, n8n, configure, setup service)"
echo "2. Install Dependencies Only"
echo "3. Install n8n Only"
echo "4. Configure Only"
echo "5. Launch Setup GUI Only"
echo "6. Exit"

read -p "Select an option [1-6]: " INSTALL_OPTION

case "$INSTALL_OPTION" in
    1)
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
        ;;
    2)
        # Install dependencies only
        install_dependencies
        ;;
    3)
        # Install n8n only
        install_n8n
        setup_n8n
        ;;
    4)
        # Configure only
        setup_agent
        ;;
    5)
        # Launch setup GUI only
        launch_setup_gui
        ;;
    6)
        # Exit
        print_message $BLUE "Exiting setup."
        exit 0
        ;;
    *)
        print_message $RED "Invalid option. Exiting."
        exit 1
        ;;
esac

print_message $GREEN "=============== Setup Complete ==============="
print_message $BLUE "Filesystem Anomaly Detection has been set up successfully!"
echo ""
print_message $YELLOW "You can access n8n at: http://localhost:5678"
print_message $YELLOW "The setup interface is available at: http://localhost:3000/setup"
echo ""
print_message $BLUE "Important Information:"
echo "API Key: ${API_KEY:-"Check your config file at $HOME/.config/file_anomaly_detection/config.json"}"
echo "Configuration file: ~/.config/file_anomaly_detection/config.json"
echo "n8n logs: ~/.n8n/logs/n8n.log"
echo ""
print_message $GREEN "Enjoy your organized files! 🎉" 