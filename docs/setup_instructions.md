# n8n Installation and Setup Guide for macOS

## Prerequisites
- macOS 10.15 or higher
- [Homebrew](https://brew.sh/) package manager
- Node.js 16 or higher

## Installation Steps

### 1. Install Dependencies

```bash
# Install Node.js and npm if not already installed
brew install node

# Install n8n globally
npm install n8n -g
```

### 2. Configure n8n Without Authentication

Create a `.env` file in your n8n working directory:

```bash
# Create n8n directory
mkdir -p ~/n8n-data
cd ~/n8n-data

# Create .env file
cat > .env << EOL
N8N_BASIC_AUTH_ACTIVE=false
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_HOST=localhost
N8N_ENCRYPTION_KEY=$(openssl rand -hex 24)
EOL
```

### 3. Create a Launch Agent for Automatic Startup

```bash
# Create a launch agent plist file
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

# Create logs directory
mkdir -p ~/n8n-data/logs

# Load the launch agent
launchctl load ~/Library/LaunchAgents/com.n8n.agent.plist
```

### 4. Configure macOS Firewall

1. Open System Preferences > Security & Privacy > Firewall
2. Click the lock icon to make changes
3. Click "Firewall Options..."
4. Add n8n to the list of applications and set it to "Allow incoming connections"

### 5. Verify Installation

1. Open your browser and navigate to `http://localhost:5678`
2. You should see the n8n interface without a login prompt
3. If you can access the interface, n8n is correctly set up without authentication

## Backup Strategy

### Setup Time Machine Backup
1. Connect an external drive to your Mac
2. Go to System Preferences > Time Machine
3. Click "Select Backup Disk..." and choose your external drive
4. Make sure your n8n-data directory is not excluded from the backup

### Manual Backups
Create a backup script:

```bash
# Create backup script
cat > ~/n8n-backup.sh << EOL
#!/bin/bash
TIMESTAMP=\$(date +"%Y%m%d-%H%M%S")
BACKUP_DIR=~/n8n-backups
mkdir -p \$BACKUP_DIR
cd ~/n8n-data
tar -czf \$BACKUP_DIR/n8n-backup-\$TIMESTAMP.tar.gz .
EOL

# Make the script executable
chmod +x ~/n8n-backup.sh

# Add to crontab to run daily
(crontab -l 2>/dev/null; echo "0 0 * * * ~/n8n-backup.sh") | crontab -
``` 