#!/usr/bin/env python3
"""
Auto Organizer - Self-managing wrapper for the File Organizer AI Agent
This script monitors and manages the file organizer agent and its services,
automatically handling recovery, permissions, and integration with n8n.
"""

import os
import sys
import time
import json
import logging
import subprocess
import shutil
import signal
import argparse
import traceback
from datetime import datetime
import requests
from pathlib import Path
import asyncio
import tempfile
import platform
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import the file organizer
from file_organizer_agent import FileOrganizer, Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_organizer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("auto_organizer")

# Constants
DEFAULT_CONFIG_PATH = os.environ.get("FILE_ORGANIZER_CONFIG", os.path.expanduser("~/.config/file_organizer/config.json"))
API_PORT = int(os.environ.get("API_SERVER_PORT", 3333))
N8N_PORT = int(os.environ.get("N8N_PORT", 5678))
N8N_URL = os.environ.get("N8N_URL", f"http://localhost:{N8N_PORT}")
API_URL = os.environ.get("FILE_ORGANIZER_API_URL", f"http://localhost:{API_PORT}")
CONFIG_FILE = os.environ.get('CONFIG_FILE', 'config.json')
API_KEY_FILE = os.environ.get('API_KEY_FILE', 'api_key.txt')
DEFAULT_INTERVAL = 3600  # Default to 1 hour if not specified
MIN_FILE_AGE = 60  # Default minimum file age in seconds before organizing

class FileHandler(FileSystemEventHandler):
    """Handles file system events for the watched directories"""
    
    def __init__(self, auto_organizer):
        self.auto_organizer = auto_organizer
        self.last_processed = {}  # Keep track of recently processed files
        super().__init__()
    
    def on_created(self, event):
        """Handle file creation event"""
        if not event.is_directory:
            # Don't process immediately to avoid handling files that are still being written
            self.last_processed[event.src_path] = time.time()
            logger.debug(f"File created: {event.src_path}")
    
    def on_modified(self, event):
        """Handle file modification event"""
        if not event.is_directory:
            self.last_processed[event.src_path] = time.time()
            logger.debug(f"File modified: {event.src_path}")
    
    def on_moved(self, event):
        """Handle file move event"""
        if not event.is_directory:
            # If the file was moved into the watch directory
            self.last_processed[event.dest_path] = time.time()
            logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")
    
    def process_pending_files(self):
        """Process files that have been stable for the minimum age"""
        # Advanced setting for minimum file age before processing
        min_age_seconds = self.auto_organizer.config.get("advanced", {}).get("min_file_age_minutes", 0) * 60
        if min_age_seconds < 1:
            min_age_seconds = 5  # 5 seconds minimum to avoid processing files still being written
        
        current_time = time.time()
        files_to_process = []
        
        # Check each pending file
        for file_path, timestamp in list(self.last_processed.items()):
            if current_time - timestamp >= min_age_seconds:
                # File has been stable for the minimum age
                if os.path.exists(file_path) and not file_path.endswith('.part'):
                    try:
                        # Check if file is still being written
                        if self.is_file_ready(file_path):
                            files_to_process.append(file_path)
                            del self.last_processed[file_path]
                    except Exception as e:
                        logger.error(f"Error checking file {file_path}: {e}")
                        del self.last_processed[file_path]
                else:
                    # File doesn't exist anymore or is a partial download
                    del self.last_processed[file_path]
        
        if files_to_process:
            asyncio.run(self.auto_organizer.process_files(files_to_process))
    
    def is_file_ready(self, file_path: str) -> bool:
        """Check if file is ready to be processed (not being written to)"""
        try:
            # Get initial file size
            initial_size = os.path.getsize(file_path)
            time.sleep(1)  # Wait a second
            # Check size again
            current_size = os.path.getsize(file_path)
            
            # If size hasn't changed, file is likely not being written to
            return initial_size == current_size
        except Exception:
            return False

class AutoOrganizer:
    """Self-managing wrapper for the File Organizer AI Agent"""
    
    def __init__(self, config_path=DEFAULT_CONFIG_PATH, monitor_interval=60):
        """Initialize the auto organizer"""
        self.config_path = config_path
        self.monitor_interval = monitor_interval
        self.running = False
        self.api_process = None
        self.n8n_process = None  # Only used if starting n8n internally
        self.load_config()
        self.setup_signal_handlers()
        self.observers = []
        self.scheduler_thread = None
        self.event_handler = FileHandler(self)
        self.setup_directories()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Config file {self.config_path} not found. Using defaults.")
                self.config = {
                    "source_directory": os.path.expanduser("~/Downloads"),
                    "target_directory": os.path.expanduser("~/Organized"),
                    "organize_by": "extension",
                    "api_keys": {
                        "default": self.generate_api_key()
                    },
                    "auto_fix_permissions": True,
                    "auto_recovery": True,
                    "monitor_directories": True,
                    "watch_directories": [
                        os.path.expanduser("~/Downloads"),
                        os.path.expanduser("~/Documents")
                    ],
                    "advanced": {
                        "min_file_age_minutes": 0
                    },
                    "performance": {
                        "max_threads": 4,
                        "batch_size": 100,
                        "memory_limit_mb": 1024
                    }
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.error(traceback.format_exc())
            self.config = {}

    def save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def generate_api_key(self):
        """Generate a random API key"""
        import secrets
        return secrets.token_hex(32)
    
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
    
    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received. Stopping services...")
        self.running = False
        self.stop_services()
        sys.exit(0)
    
    def check_permissions(self, directory):
        """Check and fix permissions for a directory"""
        try:
            expanded_dir = os.path.expanduser(directory)
            if not os.path.exists(expanded_dir):
                logger.info(f"Creating directory {expanded_dir}")
                os.makedirs(expanded_dir, exist_ok=True)
            
            # Check if directory is writable
            if not os.access(expanded_dir, os.W_OK):
                if self.config.get("auto_fix_permissions", True):
                    logger.warning(f"Directory {expanded_dir} is not writable. Fixing permissions...")
                    try:
                        os.chmod(expanded_dir, 0o755)
                    except Exception as e:
                        logger.error(f"Could not fix permissions: {e}")
                        return False
                else:
                    logger.error(f"Directory {expanded_dir} is not writable. Please fix permissions.")
                    return False
            
            return os.access(expanded_dir, os.W_OK)
        except Exception as e:
            logger.error(f"Error checking permissions for {directory}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def check_api_server(self):
        """Check if the API server is running"""
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"API server check failed: {e}")
            return False
    
    def check_n8n(self):
        """Check if n8n is running"""
        try:
            response = requests.get(f"{N8N_URL}/healthz", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"n8n check failed: {e}")
            return False
    
    def start_api_server(self):
        """Start the API server"""
        try:
            if not self.check_api_server():
                logger.info("Starting API server...")
                # Start API server as a subprocess
                api_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_api_server.py")
                
                # Check if the script exists
                if not os.path.exists(api_script):
                    logger.error(f"API server script not found at {api_script}")
                    return False
                
                # Prepare environment variables
                env = os.environ.copy()
                env["FILE_ORGANIZER_CONFIG"] = self.config_path
                api_key = self.config.get("api_keys", {}).get("default", "")
                if api_key:
                    env["FILE_ORGANIZER_API_KEY"] = api_key
                
                # Set the port
                cmd = [sys.executable, api_script, "--port", str(API_PORT), "--host", "0.0.0.0"]
                
                # Start the process
                self.api_process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait a bit for it to start
                time.sleep(5)
                
                # Check if it's running
                if self.check_api_server():
                    logger.info("API server started successfully")
                    return True
                else:
                    # Get the error output
                    try:
                        stderr = self.api_process.stderr.read().decode("utf-8")
                        logger.error(f"API server failed to start. Error: {stderr}")
                    except:
                        logger.error("API server failed to start, but couldn't get error output")
                    
                    # Try to terminate it
                    self.api_process.terminate()
                    self.api_process = None
                    return False
            else:
                logger.info("API server is already running")
                return True
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def stop_api_server(self):
        """Stop the API server"""
        if self.api_process:
            logger.info("Stopping API server...")
            try:
                self.api_process.terminate()
                try:
                    self.api_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("API server did not terminate gracefully, forcing...")
                    self.api_process.kill()
                    self.api_process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")
            finally:
                self.api_process = None
    
    def configure_n8n(self):
        """Configure n8n with the File Organizer workflow"""
        if not self.check_n8n():
            logger.warning("n8n is not running. Skipping n8n configuration.")
            return False
        
        try:
            # Check if the workflow template exists
            workflow_template = os.path.join(os.path.dirname(os.path.abspath(__file__)), "n8n_workflow_template.json")
            
            if not os.path.exists(workflow_template):
                logger.warning(f"n8n workflow template not found at {workflow_template}")
                return False
            
            # Set environment variables for n8n
            n8n_env = os.environ.copy()
            n8n_env["FILE_ORGANIZER_API_URL"] = API_URL
            n8n_env["FILE_ORGANIZER_API_KEY"] = self.config.get("api_keys", {}).get("default", "")
            
            # Import the workflow template
            logger.info("Importing workflow template to n8n...")
            try:
                # Try to execute n8n import command
                result = subprocess.run(
                    ["n8n", "import:workflow", "--input", workflow_template],
                    env=n8n_env, 
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"n8n workflow import result: {result.stdout}")
                logger.info("Workflow template imported successfully")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # If the command fails, try to use the n8n API instead
                logger.warning(f"n8n command failed: {e}. Trying API instead.")
                
                # Load the workflow template
                with open(workflow_template, 'r') as f:
                    workflow_data = json.load(f)
                
                # Set environment variables in the workflow
                # (This would need customization based on your workflow structure)
                
                # Try to import via API
                try:
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(
                        f"{N8N_URL}/rest/workflows", 
                        json=workflow_data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code in (200, 201):
                        logger.info("Workflow imported via API successfully")
                        return True
                    else:
                        logger.warning(f"Failed to import workflow via API: {response.status_code} {response.text}")
                        return False
                except Exception as e:
                    logger.error(f"Error importing workflow via API: {e}")
                    return False
        except Exception as e:
            logger.error(f"Error configuring n8n: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run_automatic_organization(self):
        """Run automatic organization on configured directories"""
        if not self.check_api_server():
            logger.warning("API server is not running. Skipping automatic organization.")
            return
        
        # Get API key
        api_key = self.config.get("api_keys", {}).get("default", "")
        if not api_key:
            logger.warning("No API key found. Skipping automatic organization.")
            return
        
        # Get directories to watch
        watch_dirs = self.config.get("watch_directories", [])
        if not watch_dirs:
            logger.warning("No watch directories configured. Skipping automatic organization.")
            return
        
        # Organize each directory
        for directory in watch_dirs:
            expanded_dir = os.path.expanduser(directory)
            if not os.path.exists(expanded_dir):
                logger.warning(f"Watch directory {expanded_dir} does not exist. Skipping.")
                continue
            
            logger.info(f"Automatically organizing files in {expanded_dir}")
            
            try:
                # Call the organize endpoint
                headers = {"X-API-Key": api_key}
                payload = {
                    "source_directory": expanded_dir,
                    "target_directory": os.path.expanduser(self.config.get("target_directory")),
                    "organize_by": self.config.get("organize_by", "extension")
                }
                
                response = requests.post(
                    f"{API_URL}/api/organize",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Organization result: {result.get('message', 'Success')}")
                else:
                    logger.error(f"Error organizing files: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error calling organize API: {e}")
                logger.error(traceback.format_exc())
    
    def start_services(self):
        """Start all required services"""
        logger.info("Starting services...")
        
        # Check and fix directory permissions
        source_dir = os.path.expanduser(self.config.get("source_directory", "~/Downloads"))
        target_dir = os.path.expanduser(self.config.get("target_directory", "~/Organized"))
        
        if not self.check_permissions(source_dir):
            logger.error(f"Cannot access source directory: {source_dir}")
        
        if not self.check_permissions(target_dir):
            logger.error(f"Cannot access target directory: {target_dir}")
            
        # Start API server
        if not self.start_api_server():
            logger.error("Failed to start API server")
        
        # Configure n8n if it's running
        if self.check_n8n():
            if self.configure_n8n():
                logger.info("n8n configured successfully")
            else:
                logger.warning("Failed to configure n8n")
        else:
            logger.info("n8n is not running. Skipping configuration.")
        
        # Set up watchdog observers if monitoring is enabled
        if self.config.get("monitor_directories", True):
            self.setup_observers()
        
        # Set up scheduler for periodic organization
        self.setup_scheduler()
    
    def stop_services(self):
        """Stop all services"""
        self.stop_api_server()
        
        # Stop observers
        for observer in self.observers:
            observer.stop()
        
        # Wait for observers to finish
        for observer in self.observers:
            observer.join()
        
        # Clear observers list
        self.observers = []
    
    def monitor_services(self):
        """Monitor and recover services if needed"""
        if not self.config.get("auto_recovery", True):
            return
        
        if not self.check_api_server():
            logger.warning("API server is not running. Attempting to restart...")
            self.stop_api_server()  # Ensure any hanging process is terminated
            self.start_api_server()
    
    def setup_directories(self):
        """Ensure all directories exist"""
        # Ensure target directory exists
        target_dir = os.path.expanduser(self.config.get("target_directory"))
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
                logger.info(f"Created target directory: {target_dir}")
            except Exception as e:
                logger.error(f"Error creating target directory: {e}")
        
        # Ensure source directory exists
        source_dir = os.path.expanduser(self.config.get("source_directory"))
        if not os.path.exists(source_dir):
            try:
                os.makedirs(source_dir, exist_ok=True)
                logger.info(f"Created source directory: {source_dir}")
            except Exception as e:
                logger.error(f"Error creating source directory: {e}")
        
        # Ensure watch directories exist
        for directory in self.config.get("watch_directories", []):
            expanded_dir = os.path.expanduser(directory)
            if not os.path.exists(expanded_dir):
                try:
                    os.makedirs(expanded_dir, exist_ok=True)
                    logger.info(f"Created watch directory: {expanded_dir}")
                except Exception as e:
                    logger.error(f"Error creating watch directory: {e}")
    
    def setup_observers(self):
        """Set up file system observers for all watched directories"""
        directories = [self.config.get("source_directory")]
        directories.extend(self.config.get("watch_directories", []))
        
        for dir_path in directories:
            expanded_path = os.path.expanduser(dir_path)
            if os.path.exists(expanded_path):
                observer = Observer()
                observer.schedule(self.event_handler, expanded_path, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"Watching directory: {expanded_path}")
            else:
                logger.warning(f"Directory does not exist, cannot watch: {expanded_path}")
    
    def setup_scheduler(self):
        """Set up scheduler for periodic organization"""
        interval = self.config.get("organize_interval", DEFAULT_INTERVAL)
        logger.info(f"Setting up scheduler to run every {interval} seconds")
        
        def scheduler_task():
            next_run = time.time() + interval
            
            while self.running:
                current_time = time.time()
                
                # Process any pending files from the file watcher
                self.event_handler.process_pending_files()
                
                if current_time >= next_run:
                    logger.info("Running scheduled organization")
                    asyncio.run(self.organize_all())
                    next_run = time.time() + interval
                
                # Sleep for a short time to avoid high CPU usage
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=scheduler_task, daemon=True)
        self.scheduler_thread.start()
    
    async def organize_all(self):
        """Organize files in all watched directories"""
        try:
            # Start with the main source directory
            await self.organize_directory(self.config.get("source_directory"))
            
            # Then process any additional watch directories
            for directory in self.config.get("watch_directories", []):
                await self.organize_directory(directory)
        except Exception as e:
            logger.error(f"Error in organize_all: {e}")
    
    async def organize_directory(self, directory: str):
        """Organize files in a single directory"""
        expanded_dir = os.path.expanduser(directory)
        if not os.path.exists(expanded_dir):
            logger.warning(f"Directory does not exist: {expanded_dir}")
            return
        
        logger.info(f"Organizing directory: {expanded_dir}")
        
        # Create configuration for the organizer
        organizer_config = Config()
        organizer_config.config.update(self.config)
        organizer_config.config["source_directory"] = expanded_dir
        
        # Create organizer
        organizer = FileOrganizer(organizer_config)
        
        # Run the organizer
        result = await organizer.organize()
        
        # Log results
        logger.info(f"Organization completed for {expanded_dir}:")
        logger.info(f"  Files processed: {result.get('files_processed', 0)}")
        logger.info(f"  Files moved: {result.get('files_moved', 0)}")
        logger.info(f"  Files skipped: {result.get('files_skipped', 0)}")
        logger.info(f"  Errors: {result.get('errors', 0)}")
        logger.info(f"  Time taken: {result.get('elapsed_time', 0):.2f} seconds")
        
        # Send notifications if enabled
        if self.config.get("notifications", {}).get("desktop_notifications", False):
            self.send_desktop_notification(
                "File Organization Complete",
                f"Processed: {result.get('files_processed', 0)}, Moved: {result.get('files_moved', 0)}"
            )
    
    async def process_files(self, file_paths: List[str]):
        """Process a list of files that need organization"""
        if not file_paths:
            return
        
        logger.info(f"Processing {len(file_paths)} new files")
        
        # Get batch size from performance settings
        batch_size = self.config.get("performance", {}).get("batch_size", 100)
        
        # Process files in batches
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i+batch_size]
            await self.process_batch(batch)
    
    async def process_batch(self, file_paths: List[str]):
        """Process a batch of files"""
        # Create configuration for the organizer
        organizer_config = Config()
        organizer_config.config.update(self.config)
        
        # Create organizer
        organizer = FileOrganizer(organizer_config)
        
        # Process each file
        for file_path in file_paths:
            try:
                # Check minimum file size if configured
                min_size_kb = self.config.get("min_file_size_kb", 0)
                if min_size_kb > 0:
                    file_size_kb = os.path.getsize(file_path) / 1024
                    if file_size_kb < min_size_kb:
                        logger.debug(f"Skipping file smaller than minimum size: {file_path}")
                        continue
                
                # Check maximum file size if configured
                max_size_mb = self.config.get("max_file_size_mb", 0)
                if max_size_mb > 0:
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if file_size_mb > max_size_mb:
                        logger.debug(f"Skipping file larger than maximum size: {file_path}")
                        continue
                
                # Special handling for images if configured
                if self.config.get("advanced", {}).get("compress_images", False) and self.is_image(file_path):
                    await self.compress_image(file_path)
                
                # Special handling for archives if configured
                if self.config.get("advanced", {}).get("extract_archives", False) and self.is_archive(file_path):
                    await self.extract_archive(file_path)
                
                # Process the file
                await organizer.process_file(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    async def compress_image(self, file_path: str):
        """Compress an image file to save space"""
        try:
            # Only attempt compression if PIL is available
            import PIL
            from PIL import Image
            
            logger.info(f"Compressing image: {file_path}")
            
            # Open the image
            img = Image.open(file_path)
            
            # Create a temporary file for the compressed image
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_path)[1]) as tmp:
                # Save the image with reduced quality
                img.save(tmp.name, optimize=True, quality=85)
                
                # Check if the compressed file is smaller
                orig_size = os.path.getsize(file_path)
                comp_size = os.path.getsize(tmp.name)
                
                if comp_size < orig_size:
                    # Replace the original with the compressed version
                    shutil.move(tmp.name, file_path)
                    logger.info(f"Compressed image from {orig_size/1024:.1f}KB to {comp_size/1024:.1f}KB")
                else:
                    # Keep the original
                    os.unlink(tmp.name)
                    logger.info("Compression did not reduce file size, keeping original")
        except ImportError:
            logger.warning("PIL not available, skipping image compression")
        except Exception as e:
            logger.error(f"Error compressing image {file_path}: {e}")
    
    async def extract_archive(self, file_path: str):
        """Extract an archive file"""
        try:
            import zipfile
            import tarfile
            
            logger.info(f"Extracting archive: {file_path}")
            
            # Determine the extract directory (same as the archive but without extension)
            extract_dir = os.path.splitext(file_path)[0]
            
            # Create extract directory if it doesn't exist
            os.makedirs(extract_dir, exist_ok=True)
            
            # Extract based on file type
            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif tarfile.is_tarfile(file_path):
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            else:
                logger.warning(f"Unsupported archive format: {file_path}")
                return
            
            logger.info(f"Extracted archive to {extract_dir}")
        except Exception as e:
            logger.error(f"Error extracting archive {file_path}: {e}")
    
    def is_image(self, file_path: str) -> bool:
        """Check if a file is an image"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in image_extensions
    
    def is_archive(self, file_path: str) -> bool:
        """Check if a file is an archive"""
        archive_extensions = ['.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in archive_extensions
    
    def send_desktop_notification(self, title: str, message: str):
        """Send a desktop notification"""
        try:
            system = platform.system()
            
            if system == "Darwin":  # macOS
                os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
            elif system == "Linux":
                os.system(f'notify-send "{title}" "{message}"')
            elif system == "Windows":
                # Use Windows 10 Toast Notifications
                try:
                    from win10toast import ToastNotifier
                    toaster = ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                except ImportError:
                    # Fall back to a simpler approach
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(0, message, title, 0)
        except Exception as e:
            logger.error(f"Error sending desktop notification: {e}")
    
    def run(self):
        """Run the auto organizer"""
        logger.info("Starting Auto Organizer...")
        self.running = True
        
        # Start services
        self.start_services()
        
        # Main loop
        last_organize_time = 0
        organize_interval = self.config.get("organize_interval", 3600)  # Default to 1 hour
        
        try:
            while self.running:
                # Monitor services
                self.monitor_services()
                
                # Run automatic organization if needed
                current_time = time.time()
                if current_time - last_organize_time > organize_interval and self.config.get("monitor_directories", True):
                    self.run_automatic_organization()
                    last_organize_time = current_time
                
                # Sleep for the monitor interval
                time.sleep(self.monitor_interval)
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            logger.error(traceback.format_exc())
        finally:
            self.stop_services()
            logger.info("Auto Organizer stopped")
            

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Auto Organizer for File Organizer AI Agent")
    parser.add_argument("--config", help="Path to configuration file", default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--interval", type=int, help="Monitor interval in seconds", default=60)
    args = parser.parse_args()
    
    try:
        organizer = AutoOrganizer(config_path=args.config, monitor_interval=args.interval)
        organizer.run()
    except Exception as e:
        logger.error(f"Error running Auto Organizer: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main() 