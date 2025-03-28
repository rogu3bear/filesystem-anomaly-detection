# Setup Manager - macOS App

This document provides instructions for building and using the Setup Manager as a native macOS application.

## Features

- Interactive graphical interface for setup management
- Docker installation and management without needing Docker Desktop
- Automated setup verification and dependency checking
- Web application launcher with automatic port management
- GitHub integration for pushing changes

## Building the macOS App

### Prerequisites

- macOS 10.14 or later
- Python 3.6 or later
- pip3
- Xcode Command Line Tools (recommended for proper icon generation)

### Building the App

1. Make sure all prerequisites are installed:
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Install Python dependencies
pip3 install py2app pillow
```

2. Run the build script:
```bash
# Make the build script executable
chmod +x create_macos_app.sh

# Run the build script
./create_macos_app.sh
```

3. When successful, the app will be created in the `dist` directory:
   - The app: `dist/Setup Manager.app`
   - The disk image (if `hdiutil` is available): `dist/SetupManager.dmg`

## Using the macOS App

### Installation

1. Copy `Setup Manager.app` to your Applications folder or run it from any location.
2. The first time you run the app, you might need to right-click and select "Open" to bypass Gatekeeper.

### Key Features

- **Directory Management**: Create and navigate directories safely.
- **File Upload**: Upload files to the selected directory with automatic backups.
- **Docker Management**: Install, start, and verify Docker without Docker Desktop.
- **Web Application**: Launch a simple web server to test your application.
- **GitHub Integration**: Push changes to a GitHub repository with automatic branch creation.

### Docker Integration

The Setup Manager can:
- Detect if Docker is installed and running
- Start Docker if it's installed but not running
- Install Docker using Homebrew or a custom installation script if it's not installed
- All without requiring Docker Desktop

## Troubleshooting

### The app doesn't start

- Check Console.app for crash logs related to "Setup Manager"
- Try running from the terminal:
```bash
/Applications/Setup\ Manager.app/Contents/MacOS/Setup\ Manager
```

### Docker installation fails

- Make sure you have administrative privileges
- Check if Homebrew is installed correctly
- Try running the installation script manually:
```bash
chmod +x install_docker.sh
./install_docker.sh
```

### App building fails

- Make sure py2app is installed: `pip3 install py2app`
- Check if Python 3 is properly installed: `python3 --version`
- Make sure all dependencies are installed: `pip3 install -r requirements.txt`

## Development

To modify the app:

1. Edit `setup_manager.py` to change functionality
2. Edit `setup_app.py` to change app bundling options
3. Run `./create_macos_app.sh` to rebuild the app

## License

This project is licensed under the GPL-3.0 License. 