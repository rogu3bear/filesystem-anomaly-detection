#!/usr/bin/env python3
"""
File Organizer AI Agent for n8n integration
"""

import os
import sys
import shutil
import time
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from functools import lru_cache

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("file_organizer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("file_organizer")

# Configuration class
class Config:
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration from file or default values"""
        self.config = {
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
            }
        }
        
        if config_file:
            try:
                with open(os.path.expanduser(config_file), 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                logger.info("Using default configuration")
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def save(self, config_file: str) -> None:
        """Save current configuration to file"""
        with open(os.path.expanduser(config_file), 'w') as f:
            json.dump(self.config, f, indent=4)

# Stats tracking
class Stats:
    def __init__(self):
        self.start_time = time.time()
        self.files_processed = 0
        self.files_moved = 0
        self.files_skipped = 0
        self.errors = 0
        self.duplicates_found = 0
        self.cache_hits = 0
        
    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        return {
            "files_processed": self.files_processed,
            "files_moved": self.files_moved,
            "files_skipped": self.files_skipped,
            "errors": self.errors,
            "duplicates_found": self.duplicates_found,
            "cache_hits": self.cache_hits,
            "elapsed_time": time.time() - self.start_time
        }

# File organizer class
class FileOrganizer:
    def __init__(self, config: Config):
        self.config = config
        self.stats = Stats()
        self._file_hash_cache = {}
        self.max_threads = config.get("performance", {}).get("max_threads", 4)
        
    @lru_cache(maxsize=1000)
    def get_file_category(self, file_ext: str) -> str:
        """Determine category based on file extension with caching"""
        for category, extensions in self.config.get("rules").items():
            if file_ext in extensions:
                return category
        return "others"
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file for duplicate detection"""
        if os.path.getsize(file_path) > 10 * 1024 * 1024:  # Only hash first 10MB for large files
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read(10 * 1024 * 1024)).hexdigest()
        else:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
    
    def get_destination_path(self, file_path: str) -> Optional[str]:
        """Determine destination path based on file type and organization rules"""
        if os.path.basename(file_path) in self.config.get("exclude_files"):
            return None
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Organize by extension
        if self.config.get("organize_by") == "extension":
            category = self.get_file_category(file_ext)
            return os.path.join(
                os.path.expanduser(self.config.get("target_directory")),
                category
            )
        
        # Organize by date
        elif self.config.get("organize_by") == "date":
            file_stat = os.stat(file_path)
            file_date = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Determine folder structure based on configuration
            if self.config.get("create_date_folders", False):
                # Create Year/Month/Day folders
                return os.path.join(
                    os.path.expanduser(self.config.get("target_directory")),
                    str(file_date.year),
                    str(file_date.month).zfill(2),
                    str(file_date.day).zfill(2)
                )
            else:
                # Create Year/Month folders
                return os.path.join(
                    os.path.expanduser(self.config.get("target_directory")),
                    str(file_date.year),
                    str(file_date.month).zfill(2)
                )
        
        # Organize by size
        elif self.config.get("organize_by") == "size":
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            
            if file_size < 1:
                size_category = "small"
            elif file_size < 10:
                size_category = "medium"
            elif file_size < 100:
                size_category = "large"
            else:
                size_category = "very_large"
                
            return os.path.join(
                os.path.expanduser(self.config.get("target_directory")),
                size_category
            )
        
        return None
    
    def handle_duplicate(self, source_path: str, target_path: str) -> str:
        """Handle duplicate files based on configuration"""
        if not os.path.exists(target_path):
            return target_path
            
        duplicate_handling = self.config.get("duplicate_handling")
        
        # Check if files are actually the same by comparing hash
        if os.path.exists(target_path):
            source_hash = self.calculate_file_hash(source_path)
            target_hash = self.calculate_file_hash(target_path)
            
            if source_hash == target_hash:
                self.stats.duplicates_found += 1
                # Files are identical, handle according to policy
                if duplicate_handling == "skip":
                    return None
        
        if duplicate_handling == "overwrite":
            return target_path
        elif duplicate_handling == "skip":
            return None
        elif duplicate_handling == "rename":
            # Get custom rename pattern if available
            pattern = self.config.get("advanced", {}).get("rename_pattern", "{name}{counter}{ext}")
            
            # Get file name and extension
            filename, extension = os.path.splitext(target_path)
            
            # Try counter-based renaming
            counter = 1
            while True:
                # Apply the pattern
                new_name = pattern.format(
                    name=os.path.basename(filename),
                    counter=f"_{counter}",
                    ext=extension
                )
                
                # Get the full path
                new_path = os.path.join(os.path.dirname(target_path), new_name)
                
                if not os.path.exists(new_path):
                    return new_path
                    
                counter += 1
                # Prevent infinite loop
                if counter > 1000:
                    logger.warning(f"Unable to find unique name for {target_path} after 1000 attempts")
                    return None
        
        return None
        
    async def process_file(self, file_path: str) -> bool:
        """Process a single file"""
        try:
            # Check file size limits if configured
            size_bytes = os.path.getsize(file_path)
            size_kb = size_bytes / 1024
            size_mb = size_kb / 1024
            
            # Check minimum file size
            min_size_kb = self.config.get("min_file_size_kb", 0)
            if min_size_kb > 0 and size_kb < min_size_kb:
                logger.debug(f"Skipping file smaller than minimum size: {file_path}")
                self.stats.files_skipped += 1
                return False
                
            # Check maximum file size
            max_size_mb = self.config.get("max_file_size_mb", 0)
            if max_size_mb > 0 and size_mb > max_size_mb:
                logger.debug(f"Skipping file larger than maximum size: {file_path}")
                self.stats.files_skipped += 1
                return False
            
            self.stats.files_processed += 1
            
            # Get destination path
            dest_dir = self.get_destination_path(file_path)
            if not dest_dir:
                logger.debug(f"Skipping file: {file_path}")
                self.stats.files_skipped += 1
                return False
                
            # Create target directory if it doesn't exist
            os.makedirs(dest_dir, exist_ok=True)
            
            # Handle duplicates
            target_path = os.path.join(dest_dir, os.path.basename(file_path))
            final_path = self.handle_duplicate(file_path, target_path)
            
            if not final_path:
                logger.debug(f"Skipped duplicate file: {file_path}")
                self.stats.files_skipped += 1
                return False
                
            # Move the file
            shutil.move(file_path, final_path)
            logger.info(f"Moved file: {file_path} -> {final_path}")
            self.stats.files_moved += 1
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.stats.errors += 1
            
            # Send notification if enabled
            if self.config.get("notifications", {}).get("email_on_error", False) and self.config.get("notification_email"):
                self.send_error_email(f"Error processing file {file_path}", str(e))
            
            return False
    
    def send_error_email(self, subject: str, error: str) -> None:
        """Send error notification email"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # This is a placeholder for email sending functionality
            # In a real implementation, SMTP server details would be configured
            logger.info(f"Would send error email: {subject} - {error}")
            
            # Example implementation (commented out):
            """
            smtp_server = "smtp.example.com"
            smtp_port = 587
            smtp_user = "username"
            smtp_password = "password"
            
            email_to = self.config.get("notification_email")
            if not email_to:
                return
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email_to
            msg['Subject'] = subject
            
            msg.attach(MIMEText(error, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            """
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
    
    async def organize(self) -> Dict:
        """Organize files in the source directory with parallel processing"""
        logger.info(f"Starting file organization from {self.config.get('source_directory')}")
        source_dir = os.path.expanduser(self.config.get("source_directory"))
        
        files_to_process = []
        for root, dirs, files in os.walk(source_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.config.get("exclude_dirs")]
            
            for file in files:
                if file not in self.config.get("exclude_files"):
                    file_path = os.path.join(root, file)
                    files_to_process.append(file_path)
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process files in parallel using ThreadPoolExecutor
        # Use performance settings to determine max threads
        max_threads = min(self.max_threads, len(files_to_process))
        batch_size = self.config.get("performance", {}).get("batch_size", 100)
        
        if max_threads > 1 and len(files_to_process) > 1:
            logger.info(f"Processing files in parallel with {max_threads} threads")
            
            # Process files in batches to avoid memory issues
            results = []
            for i in range(0, len(files_to_process), batch_size):
                batch = files_to_process[i:min(i + batch_size, len(files_to_process))]
                logger.info(f"Processing batch of {len(batch)} files")
                
                with ThreadPoolExecutor(max_workers=max_threads) as executor:
                    # Create tasks for the asyncio event loop
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(executor, lambda file=file: asyncio.run(self.process_file(file)))
                        for file in batch
                    ]
                    
                    # Wait for all tasks to complete
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    results.extend(batch_results)
                    
                    # Give the system a moment to release resources
                    await asyncio.sleep(0.1)
        else:
            # Process files sequentially
            logger.info("Processing files sequentially")
            results = []
            for file_path in files_to_process:
                result = await self.process_file(file_path)
                results.append(result)
        
        # Log final statistics
        logger.info(f"Organization completed:")
        logger.info(f"  Files processed: {self.stats.files_processed}")
        logger.info(f"  Files moved: {self.stats.files_moved}")
        logger.info(f"  Files skipped: {self.stats.files_skipped}")
        logger.info(f"  Duplicates found: {self.stats.duplicates_found}")
        logger.info(f"  Errors: {self.stats.errors}")
        logger.info(f"  Time taken: {time.time() - self.stats.start_time:.2f} seconds")
        
        # Send notifications if configured
        if self.config.get("notifications", {}).get("desktop_notifications", False):
            self.send_desktop_notification()
        
        if self.config.get("notifications", {}).get("email_summary", False) and self.config.get("notification_email"):
            self.send_summary_email()
        
        return self.stats.to_dict()
    
    def send_desktop_notification(self) -> None:
        """Send desktop notification with results"""
        try:
            import platform
            system = platform.system()
            
            title = "File Organization Complete"
            message = f"Processed: {self.stats.files_processed}, Moved: {self.stats.files_moved}, Errors: {self.stats.errors}"
            
            if system == "Darwin":  # macOS
                os.system(f"""osascript -e 'display notification "{message}" with title "{title}"'""")
            elif system == "Linux":
                os.system(f'notify-send "{title}" "{message}"')
            elif system == "Windows":
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
    
    def send_summary_email(self) -> None:
        """Send summary email with results"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # This is a placeholder for email sending functionality
            # In a real implementation, SMTP server details would be configured
            logger.info("Would send summary email with results")
            
            # Example implementation (commented out):
            """
            smtp_server = "smtp.example.com"
            smtp_port = 587
            smtp_user = "username"
            smtp_password = "password"
            
            email_to = self.config.get("notification_email")
            if not email_to:
                return
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = email_to
            msg['Subject'] = "File Organization Summary"
            
            body = f'''
            File Organization Summary
            ------------------------
            
            Source Directory: {self.config.get('source_directory')}
            Target Directory: {self.config.get('target_directory')}
            
            Results:
            - Files processed: {self.stats.files_processed}
            - Files moved: {self.stats.files_moved}
            - Files skipped: {self.stats.files_skipped}
            - Duplicates found: {self.stats.duplicates_found}
            - Errors: {self.stats.errors}
            - Time taken: {time.time() - self.stats.start_time:.2f} seconds
            
            This is an automated message from the File Organizer AI Agent.
            '''
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            """
        except Exception as e:
            logger.error(f"Error sending summary email: {e}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="File Organizer AI Agent")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--source", help="Source directory to organize")
    parser.add_argument("--target", help="Target directory for organized files")
    parser.add_argument("--organize-by", choices=["extension", "date", "size"], help="Organization method")
    return parser.parse_args()

async def main():
    """Main entry point"""
    args = parse_args()
    
    # Load configuration
    config = Config(args.config)
    
    # Override config with command line arguments
    if args.source:
        config.config["source_directory"] = args.source
    if args.target:
        config.config["target_directory"] = args.target
    if args.organize_by:
        config.config["organize_by"] = args.organize_by
    
    # Create and run organizer
    organizer = FileOrganizer(config)
    result = await organizer.organize()
    
    # Print results
    print(f"Organization completed successfully!")
    print(f"  Files processed: {result['files_processed']}")
    print(f"  Files moved: {result['files_moved']}")
    print(f"  Files skipped: {result['files_skipped']}")
    print(f"  Errors: {result['errors']}")
    print(f"  Time taken: {result['elapsed_time']:.2f} seconds")

# API handler for n8n integration
async def api_handler(request_data: Dict) -> Dict:
    """Handle API requests for n8n integration"""
    try:
        # Extract configuration from request
        config_data = request_data.get("config", {})
        
        # Create configuration
        config = Config()
        
        # Update configuration with request data
        if "source_directory" in config_data:
            config.config["source_directory"] = config_data["source_directory"]
        if "target_directory" in config_data:
            config.config["target_directory"] = config_data["target_directory"]
        if "organize_by" in config_data:
            config.config["organize_by"] = config_data["organize_by"]
        
        # Create and run organizer
        organizer = FileOrganizer(config)
        result = await organizer.organize()
        
        # Return results
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        logger.error(f"API handler error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    asyncio.run(main()) 