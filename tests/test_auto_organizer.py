#!/usr/bin/env python3
"""
Test script for Auto Organizer
This script tests the functionality of the Auto Organizer by simulating different scenarios.
"""

import os
import sys
import time
import json
import signal
import subprocess
import tempfile
import shutil
import logging
import requests
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_auto_organizer")

# Constants
API_PORT = 3333
TEST_DIR = os.path.expanduser("~/auto-organizer-test")
CONFIG_PATH = os.path.join(TEST_DIR, "config.json")
SOURCE_DIR = os.path.join(TEST_DIR, "source")
TARGET_DIR = os.path.join(TEST_DIR, "target")

def setup_test_environment():
    """Set up the test environment"""
    logger.info("Setting up test environment...")
    
    # Create test directories
    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(SOURCE_DIR, exist_ok=True)
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # Create test configuration
    config = {
        "source_directory": SOURCE_DIR,
        "target_directory": TARGET_DIR,
        "organize_by": "extension",
        "api_keys": {
            "default": "test-api-key-12345"
        },
        "auto_fix_permissions": True,
        "auto_recovery": True,
        "monitor_directories": True,
        "watch_directories": [SOURCE_DIR]
    }
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    
    # Create sample test files
    extensions = [".pdf", ".docx", ".jpg", ".png", ".mp4", ".py", ".zip"]
    for ext in extensions:
        with open(os.path.join(SOURCE_DIR, f"test_file{ext}"), 'w') as f:
            f.write(f"Test content for {ext} file")
    
    logger.info("Test environment set up successfully")

def cleanup_test_environment():
    """Clean up the test environment"""
    logger.info("Cleaning up test environment...")
    try:
        shutil.rmtree(TEST_DIR)
        logger.info("Test environment cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

def test_api_server():
    """Test the API server functionality"""
    try:
        # Check if API server is running
        response = requests.get(f"http://localhost:{API_PORT}/health", timeout=5)
        if response.status_code == 200:
            logger.info("API server is running")
            return True
        else:
            logger.error(f"API server returned status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to API server: {e}")
        return False

def test_auto_organizer_startup():
    """Test the Auto Organizer startup"""
    logger.info("Testing Auto Organizer startup...")
    
    # Start Auto Organizer
    process = subprocess.Popen(
        [sys.executable, "auto_organizer.py", "--config", CONFIG_PATH, "--interval", "10"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for it to initialize
    time.sleep(5)
    
    # Check if process is still running
    if process.poll() is None:
        logger.info("Auto Organizer started successfully")
        return process
    else:
        stdout, stderr = process.communicate()
        logger.error(f"Auto Organizer failed to start: {stderr.decode('utf-8')}")
        return None

def test_auto_organization():
    """Test automatic organization of files"""
    logger.info("Testing automatic organization...")
    
    # Wait for files to be organized
    time.sleep(15)
    
    # Check if target directory has organized files
    categories = ["documents", "images", "videos", "code", "archives"]
    
    organized_files = 0
    for category in categories:
        category_path = os.path.join(TARGET_DIR, category)
        if os.path.exists(category_path):
            files = os.listdir(category_path)
            organized_files += len(files)
            logger.info(f"Found {len(files)} files in category {category}")
    
    if organized_files > 0:
        logger.info("Automatic organization successful")
        return True
    else:
        logger.error("No files were organized")
        return False

def test_service_recovery():
    """Test auto recovery of services"""
    logger.info("Testing service recovery...")
    
    # Try to find the API server process
    api_pid = None
    try:
        output = subprocess.check_output(
            ["ps", "-ef"], 
            universal_newlines=True
        )
        for line in output.split('\n'):
            if "agent_api_server.py" in line and "python" in line:
                api_pid = int(line.split()[1])
                break
    except Exception as e:
        logger.error(f"Error finding API server process: {e}")
        return False
    
    if not api_pid:
        logger.error("Could not find API server process")
        return False
    
    # Kill the API server
    logger.info(f"Killing API server process (PID: {api_pid})...")
    try:
        os.kill(api_pid, signal.SIGTERM)
        logger.info("API server process terminated")
    except Exception as e:
        logger.error(f"Error killing API server: {e}")
        return False
    
    # Wait for Auto Organizer to detect and restart
    logger.info("Waiting for Auto Organizer to recover the service...")
    time.sleep(15)
    
    # Check if API server is up again
    if test_api_server():
        logger.info("Service recovery successful")
        return True
    else:
        logger.error("Service recovery failed")
        return False

def run_tests():
    """Run all tests"""
    logger.info("Starting Auto Organizer tests...")
    
    # Set up test environment
    setup_test_environment()
    
    # Start Auto Organizer
    auto_organizer_process = test_auto_organizer_startup()
    if not auto_organizer_process:
        cleanup_test_environment()
        sys.exit(1)
    
    # Test API server
    api_server_running = test_api_server()
    if not api_server_running:
        logger.warning("API server test failed, but continuing with other tests")
    
    # Test automatic organization
    organization_successful = test_auto_organization()
    
    # Test service recovery
    recovery_successful = test_service_recovery()
    
    # Terminate Auto Organizer
    logger.info("Terminating Auto Organizer...")
    if auto_organizer_process:
        auto_organizer_process.terminate()
        try:
            auto_organizer_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            auto_organizer_process.kill()
    
    # Clean up test environment
    cleanup_test_environment()
    
    # Report test results
    logger.info("===== Test Results =====")
    logger.info(f"API Server: {'PASS' if api_server_running else 'FAIL'}")
    logger.info(f"Auto Organization: {'PASS' if organization_successful else 'FAIL'}")
    logger.info(f"Service Recovery: {'PASS' if recovery_successful else 'FAIL'}")
    
    if api_server_running and organization_successful and recovery_successful:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests()) 