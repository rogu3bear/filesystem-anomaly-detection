#!/usr/bin/env python3
"""
Setup Wizard for File Organizer AI Agent
Interactive setup utility to configure and install the File Organizer AI Agent
"""

import os
import sys
import json
import shutil
import secrets
import platform
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List

# Check for inquirer package
try:
    import inquirer
except ImportError:
    print("Installing required package: inquirer")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "inquirer"])
    import inquirer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_wizard")

# Constants
DEFAULT_CONFIG = {
    "source_directory": "~/Downloads",
    "target_directory": "~/Organized",
    "rules": {
        "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
        "videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv"],
        "audio": [".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"],
        "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".php", ".rb", ".go"]
    },
    "exclude_files": [".DS_Store", "Thumbs.db"],
    "exclude_dirs": [".git", "node_modules", "__pycache__"],
    "organize_by": "extension",  # Options: extension, date, size
    "create_date_folders": False,
    "duplicate_handling": "rename",  # Options: rename, overwrite, skip
    "max_file_size_mb": 500,
    "min_file_size_kb": 1,  # Ignore very small files
    "notification_email": "",
    "api_keys": {},
    "watch_directories": [],
    "auto_fix_permissions": True,
    "auto_recovery": True,
    "monitor_directories": True,
    "organize_interval": 3600,  # Run organization every hour by default
    "performance": {
        "max_threads": 4,  # Maximum number of threads for parallel processing
        "batch_size": 100,  # Number of files to process in a batch
        "memory_limit_mb": 1024  # Memory limit for operations (1GB default)
    },
    "notifications": {
        "email_enabled": False,
        "email_on_error": True,
        "email_summary": False,
        "desktop_notifications": True,
        "summary_interval_hours": 24  # Daily summary
    },
    "advanced": {
        "min_file_age_minutes": 0,  # Process files regardless of age
        "compress_images": False,  # Don't compress images by default
        "extract_archives": False,  # Don't extract archives by default
        "rename_pattern": "{name}{counter}{ext}"  # Default rename pattern
    },
    "ui": {
        "theme": "light",  # light or dark
        "show_stats_on_dashboard": True,
        "show_recent_files": True,
        "show_disk_usage": True
    }
}

class SetupWizard:
    def __init__(self):
        """Initialize the setup wizard"""
        self.config = DEFAULT_CONFIG.copy()
        self.install_dir = os.path.abspath(os.path.dirname(__file__))
        self.docker_mode = False
        self.api_key = ""
        self.custom_categories = []
        self.check_environment()
    
    def check_environment(self):
        """Check the system environment"""
        self.system = platform.system()
        print(f"\n🔍 Detected {self.system} operating system.")
        
        # Check if running in Docker
        if os.path.exists("/.dockerenv"):
            self.docker_mode = True
            print("🐳 Running in Docker container.")
    
    def setup_intro(self):
        """Display introduction and perform initial setup checks"""
        print("\n" + "="*80)
        print("📁 File Organizer AI Agent - Setup Wizard")
        print("="*80)
        print("\nThis wizard will guide you through the setup of your File Organizer AI Agent.")
        print("It will help you configure directories, settings, and installation options.")
        
        if self.check_dependencies():
            print("✅ All dependencies are met.")
        else:
            print("❌ Some dependencies are missing. Please install them before continuing.")
            if self.prompt_yes_no("Would you like to install the missing dependencies now?"):
                self.install_dependencies()
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        try:
            # Check Python version
            python_version = tuple(map(int, platform.python_version_tuple()))
            if python_version < (3, 8):
                print(f"❌ Python 3.8+ required. Found {platform.python_version()}")
                return False
            
            # Check required Python packages
            missing_packages = []
            required_packages = [
                "fastapi", "uvicorn", "requests", "python-dotenv", 
                "psutil", "pydantic", "flask", "flask-cors"
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
                return False
            
            # Check Docker if not in Docker mode
            if not self.docker_mode:
                try:
                    result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
                    if result.returncode != 0:
                        print("⚠️ Docker not found. Docker installation will be offered.")
                except FileNotFoundError:
                    print("⚠️ Docker not found. Docker installation will be offered.")
            
            return True
        except Exception as e:
            print(f"❌ Error checking dependencies: {e}")
            return False
    
    def install_dependencies(self):
        """Install missing dependencies"""
        print("\n📦 Installing dependencies...")
        
        # Create requirements.txt if it doesn't exist
        if not os.path.exists("requirements.txt"):
            print("Creating requirements.txt file...")
            with open("requirements.txt", "w") as f:
                f.write("""# Core functionality
fastapi>=0.95.0
uvicorn>=0.22.0
pydantic>=2.0.0
python-dotenv>=1.0.0
psutil>=5.9.0
requests>=2.28.0
inquirer>=3.1.2

# Async functionality
httpx>=0.24.0
aiofiles>=23.1.0

# Web interface
flask>=2.3.2
flask-cors>=4.0.0
werkzeug>=2.3.4
jinja2>=3.1.2

# Security
python-jose>=3.3.0
passlib>=1.7.4
cryptography>=41.0.0

# Testing
pytest>=7.3.1
pytest-asyncio>=0.21.0
pytest-mock>=3.10.0

# Utilities
python-multipart>=0.0.6
pillow>=9.5.0
watchdog>=3.0.0
python-dateutil>=2.8.2
""")
        
        # Install Python packages
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
            print("✅ Python dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Python dependencies: {e}")
            return False
        
        # Install Docker if needed
        if not self.docker_mode and self.system == "Darwin" and self.prompt_yes_no("Would you like to install Docker?"):
            self.install_docker_mac()
        
        return True
    
    def install_docker_mac(self):
        """Install Docker on macOS using Homebrew"""
        try:
            # Check if Homebrew is installed
            try:
                subprocess.run(["brew", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Installing Homebrew...")
                subprocess.run(["/bin/bash", "-c", "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"], check=True)
            
            # Install Docker using Homebrew
            print("Installing Docker...")
            subprocess.run(["brew", "install", "--cask", "docker"], check=True)
            
            print("✅ Docker installed successfully. Please start Docker Desktop to complete the setup.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Docker: {e}")
    
    def configure_directories(self):
        """Configure source and target directories"""
        print("\n📂 Directory Configuration")
        print("-------------------------")
        
        # Configure source directory
        default_source = self.config["source_directory"]
        source_dir = input(f"Enter source directory (default: {default_source}): ").strip()
        if not source_dir:
            source_dir = default_source
        self.config["source_directory"] = os.path.expanduser(source_dir)
        
        # Configure target directory
        default_target = self.config["target_directory"]
        target_dir = input(f"Enter target directory (default: {default_target}): ").strip()
        if not target_dir:
            target_dir = default_target
        self.config["target_directory"] = os.path.expanduser(target_dir)
        
        # Configure watch directories
        print("\nWould you like to monitor additional directories? (comma-separated, or leave empty to skip)")
        watch_dirs = input("Additional directories to watch: ").strip()
        if watch_dirs:
            watch_list = [os.path.expanduser(d.strip()) for d in watch_dirs.split(",")]
            self.config["watch_directories"] = watch_list
        
        # Configure excluded files and directories
        if self.prompt_yes_no("\nDo you want to configure excluded files and directories?"):
            print("\nEnter file patterns to exclude (comma-separated, or leave empty for defaults)")
            print(f"Default: {', '.join(self.config['exclude_files'])}")
            exclude_files = input("Excluded files: ").strip()
            if exclude_files:
                self.config["exclude_files"] = [f.strip() for f in exclude_files.split(",")]
            
            print("\nEnter directory patterns to exclude (comma-separated, or leave empty for defaults)")
            print(f"Default: {', '.join(self.config['exclude_dirs'])}")
            exclude_dirs = input("Excluded directories: ").strip()
            if exclude_dirs:
                self.config["exclude_dirs"] = [d.strip() for d in exclude_dirs.split(",")]
        
        # Ensure directories exist
        self.create_directories()
    
    def create_directories(self):
        """Create directories if they don't exist"""
        dirs_to_create = [
            self.config["source_directory"],
            self.config["target_directory"]
        ] + self.config.get("watch_directories", [])
        
        for directory in dirs_to_create:
            expanded_dir = os.path.expanduser(directory)
            if not os.path.exists(expanded_dir):
                try:
                    os.makedirs(expanded_dir, exist_ok=True)
                    print(f"✅ Created directory: {expanded_dir}")
                except Exception as e:
                    print(f"❌ Failed to create directory {expanded_dir}: {e}")
    
    def configure_file_categories(self):
        """Configure custom file categories and extensions"""
        print("\n📑 File Categories Configuration")
        print("-----------------------------")
        
        # Ask if user wants to modify default categories
        if not self.prompt_yes_no("Do you want to customize file categories and extensions?"):
            return
        
        # Display current categories
        print("\nCurrent file categories:")
        for category, extensions in self.config["rules"].items():
            print(f"  - {category}: {', '.join(extensions)}")
        
        # Options
        actions = [
            inquirer.List('action',
                        message="What would you like to do?",
                        choices=[
                            ('Add a new category', 'add'),
                            ('Modify an existing category', 'modify'),
                            ('Remove a category', 'remove'),
                            ('Reset to defaults', 'reset'),
                            ('Continue with current settings', 'continue')
                        ],
                        default='continue')
        ]
        
        while True:
            action = inquirer.prompt(actions)['action']
            
            if action == 'continue':
                break
            
            elif action == 'add':
                category_name = input("Enter new category name: ").strip().lower()
                if not category_name:
                    print("Category name cannot be empty.")
                    continue
                
                extensions = input("Enter file extensions for this category (comma-separated, include dot): ").strip()
                if not extensions:
                    print("You must specify at least one extension.")
                    continue
                
                extension_list = [ext.strip() for ext in extensions.split(",")]
                self.config["rules"][category_name] = extension_list
                print(f"✅ Added category: {category_name}")
            
            elif action == 'modify':
                categories = list(self.config["rules"].keys())
                if not categories:
                    print("No categories to modify.")
                    continue
                
                category_prompt = [
                    inquirer.List('category',
                                message="Select category to modify",
                                choices=categories)
                ]
                category = inquirer.prompt(category_prompt)['category']
                
                print(f"Current extensions for {category}: {', '.join(self.config['rules'][category])}")
                extensions = input("Enter new file extensions (comma-separated, include dot): ").strip()
                
                if extensions:
                    extension_list = [ext.strip() for ext in extensions.split(",")]
                    self.config["rules"][category] = extension_list
                    print(f"✅ Updated category: {category}")
            
            elif action == 'remove':
                categories = list(self.config["rules"].keys())
                if not categories:
                    print("No categories to remove.")
                    continue
                
                category_prompt = [
                    inquirer.List('category',
                                message="Select category to remove",
                                choices=categories)
                ]
                category = inquirer.prompt(category_prompt)['category']
                
                if self.prompt_yes_no(f"Are you sure you want to remove category '{category}'?"):
                    del self.config["rules"][category]
                    print(f"✅ Removed category: {category}")
            
            elif action == 'reset':
                if self.prompt_yes_no("Are you sure you want to reset all categories to defaults?"):
                    self.config["rules"] = DEFAULT_CONFIG["rules"].copy()
                    print("✅ Reset categories to defaults")
            
            # Show updated categories
            print("\nCurrent file categories:")
            for category, extensions in self.config["rules"].items():
                print(f"  - {category}: {', '.join(extensions)}")
    
    def configure_organization(self):
        """Configure organization settings"""
        print("\n🔧 Organization Settings")
        print("-----------------------")
        
        # Basic organization settings
        questions = [
            inquirer.List('organize_by',
                        message="How would you like to organize files?",
                        choices=[
                            ('By file extension (e.g., .pdf → documents folder)', 'extension'),
                            ('By date (Year/Month folders)', 'date'),
                            ('By file size (small, medium, large)', 'size')
                        ],
                        default='extension'),
            
            inquirer.List('duplicate_handling',
                        message="How should duplicate files be handled?",
                        choices=[
                            ('Rename duplicates (file_1.pdf, file_2.pdf)', 'rename'),
                            ('Overwrite existing files', 'overwrite'),
                            ('Skip duplicates', 'skip')
                        ],
                        default='rename'),
                
            inquirer.Confirm('auto_fix_permissions',
                            message="Automatically fix file permissions when needed?",
                            default=True),
                
            inquirer.Confirm('auto_recovery',
                            message="Enable automatic recovery of services if they crash?",
                            default=True),
                
            inquirer.Confirm('monitor_directories',
                            message="Continuously monitor directories for new files?",
                            default=True),
            
            inquirer.List('organize_interval',
                         message="How often should files be automatically organized?",
                         choices=[
                             ('Every 15 minutes', 900),
                             ('Every 30 minutes', 1800),
                             ('Every hour', 3600),
                             ('Every 3 hours', 10800),
                             ('Every 12 hours', 43200),
                             ('Every day', 86400)
                         ],
                         default=3600)
        ]
        
        try:
            answers = inquirer.prompt(questions)
            self.config.update(answers)
        except Exception as e:
            print(f"Error during configuration: {e}")
            print("Using default organization settings.")
        
        # Configure date-based organization if selected
        if self.config["organize_by"] == "date":
            self.config["create_date_folders"] = self.prompt_yes_no(
                "Create Year/Month/Day folders instead of just Year/Month?", 
                default=False
            )
        
        # File size thresholds
        if self.prompt_yes_no("\nDo you want to set file size thresholds?", default=False):
            try:
                max_size = input(f"Maximum file size in MB (default: {self.config['max_file_size_mb']}): ").strip()
                if max_size and max_size.isdigit() and int(max_size) > 0:
                    self.config["max_file_size_mb"] = int(max_size)
                
                min_size = input(f"Minimum file size in KB (default: {self.config['min_file_size_kb']}): ").strip()
                if min_size and min_size.isdigit() and int(min_size) >= 0:
                    self.config["min_file_size_kb"] = int(min_size)
            except Exception as e:
                print(f"Error setting file size thresholds: {e}")
                print("Using default file size thresholds.")
    
    def configure_advanced_settings(self):
        """Configure advanced settings"""
        print("\n⚙️ Advanced Settings")
        print("------------------")
        
        if not self.prompt_yes_no("Would you like to configure advanced settings?", default=False):
            return
        
        # File processing settings
        print("\n📦 File Processing Settings:")
        try:
            # Minimum file age
            min_age = input(f"Minimum file age in minutes before processing (default: {self.config['advanced']['min_file_age_minutes']}): ").strip()
            if min_age and min_age.isdigit() and int(min_age) >= 0:
                self.config["advanced"]["min_file_age_minutes"] = int(min_age)
            
            # Special file handling
            self.config["advanced"]["compress_images"] = self.prompt_yes_no(
                "Automatically compress images to save space?", 
                default=self.config["advanced"]["compress_images"]
            )
            
            self.config["advanced"]["extract_archives"] = self.prompt_yes_no(
                "Automatically extract archives (zip, tar, etc.)?", 
                default=self.config["advanced"]["extract_archives"]
            )
            
            # Custom rename pattern
            print(f"\nCurrent file rename pattern: {self.config['advanced']['rename_pattern']}")
            print("Available variables: {name} = original filename, {counter} = number for duplicates, {ext} = file extension")
            pattern = input("Custom rename pattern (leave empty for default): ").strip()
            if pattern:
                self.config["advanced"]["rename_pattern"] = pattern
        except Exception as e:
            print(f"Error configuring file processing settings: {e}")
        
        # Performance settings
        print("\n⚡ Performance Settings:")
        try:
            threads = input(f"Maximum threads for parallel processing (default: {self.config['performance']['max_threads']}): ").strip()
            if threads and threads.isdigit() and int(threads) > 0:
                self.config["performance"]["max_threads"] = int(threads)
            
            batch = input(f"Batch size for file processing (default: {self.config['performance']['batch_size']}): ").strip()
            if batch and batch.isdigit() and int(batch) > 0:
                self.config["performance"]["batch_size"] = int(batch)
            
            memory = input(f"Memory limit in MB (default: {self.config['performance']['memory_limit_mb']}): ").strip()
            if memory and memory.isdigit() and int(memory) > 0:
                self.config["performance"]["memory_limit_mb"] = int(memory)
        except Exception as e:
            print(f"Error configuring performance settings: {e}")
    
    def configure_notifications(self):
        """Configure notification settings"""
        print("\n🔔 Notification Settings")
        print("----------------------")
        
        if not self.prompt_yes_no("Would you like to configure notification settings?", default=False):
            return
        
        # Desktop notifications
        self.config["notifications"]["desktop_notifications"] = self.prompt_yes_no(
            "Enable desktop notifications?", 
            default=self.config["notifications"]["desktop_notifications"]
        )
        
        # Email notifications
        if self.prompt_yes_no("Would you like to set up email notifications?", default=False):
            self.config["notifications"]["email_enabled"] = True
            email = input("Email address for notifications: ").strip()
            if email:
                self.config["notification_email"] = email
            
            self.config["notifications"]["email_on_error"] = self.prompt_yes_no(
                "Send email notifications on errors?", 
                default=self.config["notifications"]["email_on_error"]
            )
            
            self.config["notifications"]["email_summary"] = self.prompt_yes_no(
                "Send periodic summary emails?", 
                default=self.config["notifications"]["email_summary"]
            )
            
            if self.config["notifications"]["email_summary"]:
                summary_interval_options = [
                    ('Daily', 24),
                    ('Twice daily', 12),
                    ('Every 6 hours', 6),
                    ('Every hour', 1)
                ]
                
                interval_question = [
                    inquirer.List('summary_interval',
                                message="How often should summary emails be sent?",
                                choices=summary_interval_options,
                                default=24)
                ]
                
                try:
                    interval = inquirer.prompt(interval_question)['summary_interval']
                    self.config["notifications"]["summary_interval_hours"] = interval
                except Exception as e:
                    print(f"Error setting summary interval: {e}")
    
    def configure_ui_settings(self):
        """Configure user interface settings"""
        print("\n🎨 User Interface Settings")
        print("------------------------")
        
        if not self.prompt_yes_no("Would you like to configure user interface settings?", default=False):
            return
        
        # Theme
        theme_question = [
            inquirer.List('theme',
                        message="Choose a theme for the web interface",
                        choices=[
                            ('Light theme', 'light'),
                            ('Dark theme', 'dark'),
                            ('Auto (follow system preference)', 'auto')
                        ],
                        default=self.config["ui"]["theme"])
        ]
        
        try:
            theme = inquirer.prompt(theme_question)['theme']
            self.config["ui"]["theme"] = theme
        except Exception as e:
            print(f"Error setting theme: {e}")
        
        # Dashboard elements
        print("\nDashboard elements to display:")
        self.config["ui"]["show_stats_on_dashboard"] = self.prompt_yes_no(
            "Show statistics on dashboard?", 
            default=self.config["ui"]["show_stats_on_dashboard"]
        )
        
        self.config["ui"]["show_recent_files"] = self.prompt_yes_no(
            "Show recently organized files on dashboard?", 
            default=self.config["ui"]["show_recent_files"]
        )
        
        self.config["ui"]["show_disk_usage"] = self.prompt_yes_no(
            "Show disk usage on dashboard?", 
            default=self.config["ui"]["show_disk_usage"]
        )
    
    def configure_api(self):
        """Configure API settings"""
        print("\n🔑 API Configuration")
        print("------------------")
        
        # Generate API key
        self.api_key = secrets.token_hex(32)
        print(f"Generated API Key: {self.api_key}")
        self.config["api_keys"] = {"default": self.api_key}
        
        # Save API key to file
        try:
            with open("api_key.txt", "w") as f:
                f.write(self.api_key)
            print("✅ API key saved to api_key.txt")
        except Exception as e:
            print(f"❌ Failed to save API key: {e}")
    
    def setup_docker(self):
        """Set up Docker configuration"""
        if not self.docker_mode and self.prompt_yes_no("\nWould you like to use Docker for deployment?"):
            print("\n🐳 Docker Configuration")
            print("--------------------")
            
            # Create .env file
            env_content = f"""
# File Organizer Docker configuration
SOURCE_DIR={self.config['source_directory']}
TARGET_DIR={self.config['target_directory']}
API_KEY={self.api_key}
TZ=UTC
DEBUG=False
HOST=0.0.0.0
PORT=8080
N8N_PORT=5678
API_PORT=3333
"""
            try:
                with open(".env", "w") as f:
                    f.write(env_content.strip())
                print("✅ Created .env file for Docker")
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return
            
            if self.prompt_yes_no("Would you like to build and start Docker containers now?"):
                try:
                    # Build and start containers
                    subprocess.run(["docker-compose", "up", "-d", "--build"], check=True)
                    print("✅ Docker containers built and started successfully.")
                    
                    # Show access information
                    print("\n🌐 Access Information:")
                    print("  Web Interface: http://localhost:8080")
                    print("  API Server: http://localhost:3333")
                    print("  n8n: http://localhost:5678")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to build/start Docker containers: {e}")
    
    def setup_standalone(self):
        """Set up standalone installation"""
        if not self.docker_mode and not self.prompt_yes_no("\nWould you like to set up a standalone installation?"):
            return
        
        print("\n💻 Standalone Installation")
        print("-----------------------")
        
        # Create config.json
        config_path = "config.json"
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Configuration saved to {config_path}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return
        
        # Set up launch agent/service
        if self.system == "Darwin" and self.prompt_yes_no("Set up launch agent to start on login?"):
            self.setup_macos_launch_agent()
        elif self.system == "Linux" and self.prompt_yes_no("Set up systemd service to start on boot?"):
            self.setup_linux_systemd()
        elif self.system == "Windows" and self.prompt_yes_no("Set up Windows service to start on boot?"):
            self.setup_windows_service()
    
    def setup_macos_launch_agent(self):
        """Set up macOS launch agent"""
        try:
            # Create launch agent directory if it doesn't exist
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            # Create plist file
            plist_path = os.path.join(launch_agents_dir, "com.fileorganizer.agent.plist")
            
            # Get current working directory for proper pathing
            cwd = os.getcwd()
            
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fileorganizer.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{cwd}/auto_organizer.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>{cwd}/logs/error.log</string>
    <key>StandardOutPath</key>
    <string>{cwd}/logs/output.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>FILE_ORGANIZER_CONFIG</key>
        <string>{cwd}/config.json</string>
        <key>FILE_ORGANIZER_API_KEY</key>
        <string>{self.api_key}</string>
    </dict>
</dict>
</plist>
"""
            with open(plist_path, "w") as f:
                f.write(plist_content)
            
            # Ensure logs directory exists
            os.makedirs(os.path.join(cwd, "logs"), exist_ok=True)
            
            # Load launch agent
            try:
                subprocess.run(["launchctl", "load", plist_path], check=True)
                print(f"✅ Launch agent created and loaded: {plist_path}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Launch agent created but not loaded: {e}")
                print(f"You can manually load it with: launchctl load {plist_path}")
        except Exception as e:
            print(f"❌ Failed to set up launch agent: {e}")
    
    def setup_linux_systemd(self):
        """Set up Linux systemd service"""
        try:
            # Create service file
            service_path = os.path.expanduser("~/.config/systemd/user/fileorganizer.service")
            os.makedirs(os.path.dirname(service_path), exist_ok=True)
            
            # Get current working directory for proper pathing
            cwd = os.getcwd()
            
            service_content = f"""[Unit]
Description=File Organizer AI Agent
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {cwd}/auto_organizer.py
Restart=always
Environment="FILE_ORGANIZER_CONFIG={cwd}/config.json"
Environment="FILE_ORGANIZER_API_KEY={self.api_key}"
WorkingDirectory={cwd}

[Install]
WantedBy=default.target
"""
            with open(service_path, "w") as f:
                f.write(service_content)
            
            # Ensure logs directory exists
            os.makedirs(os.path.join(cwd, "logs"), exist_ok=True)
            
            # Enable and start service
            try:
                subprocess.run(["systemctl", "--user", "enable", "fileorganizer"], check=True)
                subprocess.run(["systemctl", "--user", "start", "fileorganizer"], check=True)
                print(f"✅ Systemd service created and started: {service_path}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Service created but not started: {e}")
                print(f"You can manually enable and start it with: systemctl --user enable fileorganizer && systemctl --user start fileorganizer")
        except Exception as e:
            print(f"❌ Failed to set up systemd service: {e}")
    
    def setup_windows_service(self):
        """Set up Windows service"""
        try:
            # Check if NSSM is installed
            nssm_installed = False
            try:
                subprocess.run(["nssm", "version"], check=True, capture_output=True)
                nssm_installed = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("NSSM (Non-Sucking Service Manager) not found.")
                if self.prompt_yes_no("Would you like to download NSSM?"):
                    # Download NSSM
                    print("Downloading NSSM...")
                    url = "https://nssm.cc/release/nssm-2.24.zip"
                    try:
                        import tempfile
                        import urllib.request
                        import zipfile
                        
                        # Create a temporary directory
                        temp_dir = tempfile.mkdtemp()
                        zip_path = os.path.join(temp_dir, "nssm.zip")
                        
                        # Download NSSM
                        urllib.request.urlretrieve(url, zip_path)
                        
                        # Extract NSSM
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        
                        # Find NSSM executable path
                        for root, dirs, files in os.walk(temp_dir):
                            if "nssm.exe" in files:
                                nssm_path = os.path.join(root, "nssm.exe")
                                # Copy NSSM to current directory
                                dest_path = os.path.join(os.getcwd(), "nssm.exe")
                                shutil.copy2(nssm_path, dest_path)
                                print(f"✅ NSSM downloaded and extracted to {dest_path}")
                                nssm_installed = True
                                break
                        
                        # Clean up temporary directory
                        shutil.rmtree(temp_dir)
                    except Exception as e:
                        print(f"❌ Failed to download NSSM: {e}")
                        return
            
            if not nssm_installed:
                print("Please download and install NSSM manually from: https://nssm.cc/download")
                return
            
            # Get current working directory for proper pathing
            cwd = os.getcwd()
            
            # Create service
            service_name = "FileOrganizerAgent"
            subprocess.run([
                "nssm", "install", service_name,
                sys.executable, f"{cwd}\\auto_organizer.py"
            ], check=True)
            
            # Set environment variables
            subprocess.run([
                "nssm", "set", service_name, "AppEnvironmentExtra",
                f"FILE_ORGANIZER_CONFIG={cwd}\\config.json FILE_ORGANIZER_API_KEY={self.api_key}"
            ], check=True)
            
            # Set working directory
            subprocess.run([
                "nssm", "set", service_name, "AppDirectory", cwd
            ], check=True)
            
            # Ensure logs directory exists
            logs_dir = os.path.join(cwd, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Set log paths
            subprocess.run([
                "nssm", "set", service_name, "AppStdout", f"{logs_dir}\\output.log"
            ], check=True)
            subprocess.run([
                "nssm", "set", service_name, "AppStderr", f"{logs_dir}\\error.log"
            ], check=True)
            
            # Start service
            try:
                subprocess.run(["nssm", "start", service_name], check=True)
                print(f"✅ Windows service created and started: {service_name}")
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Service created but not started: {e}")
                print(f"You can manually start it with: nssm start {service_name}")
        except Exception as e:
            print(f"❌ Failed to set up Windows service: {e}")
    
    def save_config(self):
        """Save configuration file"""
        config_path = "config.json"
        try:
            with open(config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"✅ Configuration saved to {config_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    def prompt_yes_no(self, question: str, default: bool = True) -> bool:
        """Prompt for yes/no input"""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{question} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        return response[0] == 'y'
    
    def start_services(self):
        """Start File Organizer services"""
        if self.docker_mode:
            print("\n🚀 Services are managed by Docker.")
            return
        
        if not self.prompt_yes_no("\nWould you like to start the File Organizer services now?"):
            return
        
        print("\n🚀 Starting File Organizer services...")
        
        try:
            # Create logs directory if it doesn't exist
            os.makedirs("logs", exist_ok=True)
            
            # Start API server
            subprocess.Popen([
                sys.executable, "agent_api_server.py",
                "--port", "3333",
                "--host", "0.0.0.0"
            ], stdout=open("logs/api_server.log", "a"), stderr=subprocess.STDOUT)
            print("✅ API server started.")
            
            # Start web interface
            subprocess.Popen([
                sys.executable, "web_interface.py"
            ], stdout=open("logs/web_interface.log", "a"), stderr=subprocess.STDOUT)
            print("✅ Web interface started.")
            
            # Start auto organizer
            subprocess.Popen([
                sys.executable, "auto_organizer.py"
            ], stdout=open("logs/auto_organizer.log", "a"), stderr=subprocess.STDOUT)
            print("✅ Auto organizer started.")
            
            # Access information
            print("\n🌐 Access Information:")
            print("  Web Interface: http://localhost:8080")
            print("  API Server: http://localhost:3333")
        except Exception as e:
            print(f"❌ Failed to start services: {e}")
    
    def display_feature_overview(self):
        """Display an overview of advanced features"""
        print("\n🔍 Feature Overview")
        print("-----------------")
        print("The File Organizer AI Agent includes these advanced features:")
        print("• Automatic file organization by extension, date, or size")
        print("• Custom file categories and extensions")
        print("• Duplicate file detection and handling")
        print("• Service monitoring and automatic recovery")
        print("• API for integration with other tools")
        print("• n8n workflow integration")
        print("• Web interface for monitoring and configuration")
        print("• Performance optimization settings")
        print("• File filtering by size and age")
        print("• Email and desktop notifications")
        print("• And more!")
        
        input("\nPress Enter to begin setup...")
    
    def run(self):
        """Run the setup wizard"""
        try:
            # Display advanced features overview
            self.display_feature_overview()
            
            # Start the actual setup
            self.setup_intro()
            
            if not self.docker_mode:
                # Configure directories
                self.configure_directories()
                
                # Configure file categories
                self.configure_file_categories()
                
                # Configure organization settings
                self.configure_organization()
                
                # Configure advanced settings
                self.configure_advanced_settings()
                
                # Configure notifications
                self.configure_notifications()
                
                # Configure UI settings
                self.configure_ui_settings()
            
            # Configure API
            self.configure_api()
            
            if not self.docker_mode:
                self.setup_docker()
                self.setup_standalone()
                self.save_config()
                self.start_services()
            
            print("\n✨ Setup Complete! ✨")
            print("Thank you for installing the File Organizer AI Agent.")
            print("For more information, please refer to the README.md file.")
        except KeyboardInterrupt:
            print("\n\nSetup wizard interrupted. You can run it again at any time.")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            print(f"\n❌ An unexpected error occurred: {e}")
            print("Please check the logs and try again.")

if __name__ == "__main__":
    try:
        wizard = SetupWizard()
        wizard.run()
    except KeyboardInterrupt:
        print("\n\nSetup wizard interrupted. You can run it again at any time.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error during setup: {e}", exc_info=True)
        print(f"\n❌ An error occurred during setup: {e}")
        print("Please check the logs for more information.") 