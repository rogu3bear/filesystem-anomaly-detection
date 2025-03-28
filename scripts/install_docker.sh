#!/bin/bash
#
# File Organizer AI Agent - Docker Installation Script for macOS
#
# This script automates the Docker installation and setup process for macOS.

# Set text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
RESET="\033[0m"

# Display header
echo -e "\n${BOLD}${BLUE}=======================================${RESET}"
echo -e "${BOLD}${BLUE}  File Organizer AI Agent Installer   ${RESET}"
echo -e "${BOLD}${BLUE}=======================================${RESET}\n"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script is only for macOS.${RESET}"
    echo "For other platforms, please follow the manual installation instructions in INSTALLATION.md."
    exit 1
fi

echo -e "${BLUE}This script will help you install the File Organizer AI Agent using Docker.${RESET}\n"

# Function to check if Docker is installed
check_docker() {
    if command -v docker >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker is installed.${RESET}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Docker is not installed.${RESET}"
        return 1
    fi
}

# Function to install Docker Desktop
install_docker() {
    echo -e "\n${BLUE}Installing Docker Desktop for Mac...${RESET}"
    
    # Check if Homebrew is installed
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${RESET}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to install Homebrew.${RESET}"
            exit 1
        fi
    fi
    
    echo "Installing Docker using Homebrew..."
    brew install --cask docker
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to install Docker.${RESET}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker Desktop installed.${RESET}"
    echo -e "${YELLOW}⚠️ Please open Docker Desktop application to complete setup.${RESET}"
    echo -e "${YELLOW}⚠️ Waiting for Docker to start...${RESET}"
    
    # Open Docker Desktop
    open -a Docker
    
    # Wait for Docker to start
    echo "Waiting for Docker to start (this may take a minute)..."
    while ! docker info >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    
    echo -e "\n${GREEN}✅ Docker is running.${RESET}"
}

# Check if Docker is installed, and install if needed
if ! check_docker; then
    echo -e "${YELLOW}Docker is required for this installation.${RESET}"
    read -p "Would you like to install Docker Desktop for Mac? (y/n): " install_docker_answer
    
    if [[ "$install_docker_answer" =~ ^[Yy]$ ]]; then
        install_docker
    else
        echo -e "${YELLOW}Please install Docker Desktop manually and run this script again.${RESET}"
        echo "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ Docker is installed but not running.${RESET}"
    echo "Starting Docker..."
    open -a Docker
    
    echo "Waiting for Docker to start (this may take a minute)..."
    while ! docker info >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo -e "\n${GREEN}✅ Docker is running.${RESET}"
fi

# Create directories
echo -e "\n${BLUE}Setting up directories...${RESET}"

# Get source directory
DEFAULT_SOURCE_DIR="$HOME/Downloads"
read -p "Enter source directory [$DEFAULT_SOURCE_DIR]: " SOURCE_DIR
SOURCE_DIR=${SOURCE_DIR:-$DEFAULT_SOURCE_DIR}
SOURCE_DIR=$(eval echo $SOURCE_DIR) # Expand paths like ~/Downloads

# Get target directory
DEFAULT_TARGET_DIR="$HOME/Organized"
read -p "Enter target directory [$DEFAULT_TARGET_DIR]: " TARGET_DIR
TARGET_DIR=${TARGET_DIR:-$DEFAULT_TARGET_DIR}
TARGET_DIR=$(eval echo $TARGET_DIR) # Expand paths like ~/Organized

# Create directories if they don't exist
mkdir -p "$SOURCE_DIR"
mkdir -p "$TARGET_DIR"

echo -e "${GREEN}✅ Directories created.${RESET}"

# Generate API key
API_KEY=$(openssl rand -hex 32)
echo -e "\n${BLUE}Generated API key:${RESET} $API_KEY"

# Create .env file
echo -e "\n${BLUE}Creating configuration files...${RESET}"

cat > .env << EOL
# File Organizer Docker configuration
SOURCE_DIR=$SOURCE_DIR
TARGET_DIR=$TARGET_DIR
API_KEY=$API_KEY
TZ=UTC
DEBUG=False
HOST=0.0.0.0
PORT=8080
N8N_PORT=5678
API_PORT=3333
EOL

echo -e "${GREEN}✅ Created .env file with your settings.${RESET}"

# Create data directory
mkdir -p data
chmod 777 data

# Pull and start containers
echo -e "\n${BLUE}Building and starting Docker containers...${RESET}"
docker-compose up -d --build

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to start Docker containers.${RESET}"
    echo "Please check the error messages above and try again."
    exit 1
fi

echo -e "\n${GREEN}✅ File Organizer AI Agent has been successfully installed!${RESET}"
echo -e "\n${BLUE}Access Information:${RESET}"
echo -e "  Web Interface: http://localhost:8080"
echo -e "  API Server: http://localhost:3333"
echo -e "  n8n: http://localhost:5678"
echo -e "\n${BLUE}API Key:${RESET} $API_KEY"
echo -e "\nThis key is stored in the .env file and will be needed for API access."
echo -e "\n${BLUE}Useful Commands:${RESET}"
echo -e "  ${YELLOW}docker-compose ps${RESET}        - Show running containers"
echo -e "  ${YELLOW}docker-compose logs -f${RESET}   - View logs"
echo -e "  ${YELLOW}docker-compose down${RESET}      - Stop containers"
echo -e "  ${YELLOW}docker-compose up -d${RESET}     - Start containers"

echo -e "\nThank you for installing the File Organizer AI Agent!"
echo -e "For more information, see the README.md and INSTALLATION.md files." 