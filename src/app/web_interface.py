#!/usr/bin/env python3
"""
Web Interface for the File Organizer AI Agent
This module provides a web-based interface for managing the File Organizer
"""

import os
import sys
import json
import time
import logging
import secrets
import datetime
import subprocess
import psutil
from pathlib import Path
from functools import lru_cache
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_cors import CORS
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('web_interface.log')
    ]
)
logger = logging.getLogger('web_interface')

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache static files for 5 minutes
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # Handle proxy headers
CORS(app)

# Default configuration
DEFAULT_CONFIG = {
    'watch_directory': os.path.expanduser('~/Downloads'),
    'output_directory': os.path.expanduser('~/Organized'),
    'api_url': os.environ.get('FILE_ORGANIZER_API_URL', 'http://localhost:3333'),
    'n8n_url': os.environ.get('N8N_URL', 'http://localhost:5678'),
    'check_interval': 60,
    'log_level': 'INFO',
    'auto_restart': True,
    'theme': 'light',
    'enable_analytics': False,
    'enable_notifications': True
}

# File paths
CONFIG_FILE = os.environ.get('CONFIG_FILE', 'config.json')
API_KEY_FILE = os.environ.get('API_KEY_FILE', 'api_key.txt')
LOGS_DIR = 'logs'

# Cache settings
CACHE_TIMEOUT = 60  # seconds

# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)

@lru_cache(maxsize=1)
def load_config():
    """Load configuration from file or create with defaults if it doesn't exist"""
    if os.path.exists(CONFIG_FILE):
        try:
            config_timestamp = os.path.getmtime(CONFIG_FILE)
            # Clear cache if file was modified
            load_config.cache_info = getattr(load_config, 'cache_info', 0)
            if load_config.cache_info != config_timestamp:
                load_config.cache_clear()
                load_config.cache_info = config_timestamp
                
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}")
            return DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        load_config.cache_clear()  # Clear cache after saving
        return True
    except IOError as e:
        logger.error(f"Error saving config: {e}")
        return False

@lru_cache(maxsize=1)
def load_api_key():
    """Load API key from file"""
    if os.path.exists(API_KEY_FILE):
        try:
            with open(API_KEY_FILE, 'r') as f:
                return f.read().strip()
        except IOError as e:
            logger.error(f"Error loading API key: {e}")
            return None
    return None

def save_api_key(api_key):
    """Save API key to file"""
    try:
        with open(API_KEY_FILE, 'w') as f:
            f.write(api_key)
        load_api_key.cache_clear()  # Clear cache after saving
        return True
    except IOError as e:
        logger.error(f"Error saving API key: {e}")
        return False

def generate_api_key():
    """Generate a new API key"""
    new_key = secrets.token_hex(32)
    if save_api_key(new_key):
        return new_key
    return None

@lru_cache(maxsize=1, maxage=CACHE_TIMEOUT)
def check_services():
    """Check if API and n8n services are running"""
    config = load_config()
    services = {
        'api': False,
        'n8n': False
    }
    
    # Check API
    try:
        response = requests.get(f"{config['api_url']}/health", timeout=2)
        services['api'] = response.status_code == 200
    except requests.exceptions.RequestException:
        services['api'] = False
    
    # Check n8n
    try:
        response = requests.get(f"{config['n8n_url']}/healthz", timeout=2)
        services['n8n'] = response.status_code == 200
    except requests.exceptions.RequestException:
        services['n8n'] = False
    
    return services

def get_recent_logs(limit=50, before=None):
    """Get recent log entries from the log file"""
    logs = []
    log_files = [
        'web_interface.log',
        'api_server.log',
        'auto_organizer.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    for line in f.readlines():
                        if line.strip():
                            parts = line.split(' - ', 3)
                            if len(parts) >= 4:
                                timestamp = parts[0]
                                source = parts[1]
                                level = parts[2]
                                message = parts[3].strip()
                                
                                # Filter by timestamp if 'before' is specified
                                if before and timestamp >= before:
                                    continue
                                
                                logs.append({
                                    'timestamp': timestamp,
                                    'source': source,
                                    'level': level,
                                    'message': message
                                })
            except IOError as e:
                logger.error(f"Error reading log file {log_file}: {e}")
    
    # Sort logs by timestamp (newest first) and limit the number
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Check if there are more logs beyond the limit
    more_logs = len(logs) > limit
    
    return logs[:limit], more_logs

@lru_cache(maxsize=1, maxage=5)  # Cache for 5 seconds
def get_system_info():
    """Get system information for display"""
    # Get uptime
    boot_time = psutil.boot_time()
    uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Get CPU and memory usage
    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    
    # Get disk usage for the output directory
    config = load_config()
    output_dir = config['output_directory']
    try:
        disk = psutil.disk_usage(output_dir)
        disk_usage = disk.percent
        disk_free = disk.free / (1024 * 1024 * 1024)  # Convert to GB
    except:
        disk_usage = 0
        disk_free = 0
    
    return {
        'uptime': uptime_str,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_usage': disk_usage,
        'disk_free': f"{disk_free:.1f} GB"
    }

def restart_services(services):
    """Restart selected services"""
    results = {}
    
    for service in services:
        if service == 'api':
            # Restart API server
            try:
                # Find and terminate API server process
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if proc.info['cmdline'] and 'agent_api_server.py' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        proc.wait(timeout=5)
                        break
                
                # Start API server
                subprocess.Popen(["python3", "agent_api_server.py", "--port", "3333"])
                results['api'] = True
            except Exception as e:
                logger.error(f"Failed to restart API server: {e}")
                results['api'] = False
        
        elif service == 'n8n':
            # Restart n8n (in Docker environment, this is handled by docker-compose)
            logger.info("n8n restart requested, but this is managed by Docker in container mode")
            results['n8n'] = True
        
        elif service == 'auto_organizer':
            # Restart auto organizer
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    if proc.info['cmdline'] and 'auto_organizer.py' in ' '.join(proc.info['cmdline']):
                        proc.terminate()
                        proc.wait(timeout=5)
                        break
                
                subprocess.Popen(["python3", "auto_organizer.py"])
                results['auto_organizer'] = True
            except Exception as e:
                logger.error(f"Failed to restart auto organizer: {e}")
                results['auto_organizer'] = False
    
    # Clear caches
    check_services.cache_clear()
    
    return results

def get_recent_organized_files(limit=20):
    """Get a list of recently organized files"""
    config = load_config()
    api_key = load_api_key()
    
    if not api_key:
        return []
    
    try:
        response = requests.get(
            f"{config['api_url']}/api/recent-files",
            headers={"X-API-Key": api_key},
            params={"limit": limit},
            timeout=3
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API returned error: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get recent files: {e}")
        return []

def get_organization_summary():
    """Get summary statistics for organized files"""
    config = load_config()
    api_key = load_api_key()
    
    if not api_key:
        return {}
    
    try:
        response = requests.get(
            f"{config['api_url']}/api/stats",
            headers={"X-API-Key": api_key},
            timeout=3
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"API returned error: {response.text}")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get organization summary: {e}")
        return {}

def get_mock_recent_files():
    """Generate mock data for recent files (for development)"""
    return [
        {"name": "document.pdf", "category": "documents", "size": "1.2 MB", "timestamp": "2023-06-01 14:30:00"},
        {"name": "image.jpg", "category": "images", "size": "3.4 MB", "timestamp": "2023-06-01 14:35:00"},
        {"name": "video.mp4", "category": "videos", "size": "45.6 MB", "timestamp": "2023-06-01 14:40:00"}
    ]

@app.route('/')
def index():
    """Render the dashboard page"""
    config = load_config()
    services_status = check_services()
    system_info = get_system_info()
    
    # Try to get real data, fall back to mock data for development
    try:
        recent_files = get_recent_organized_files()
        if not recent_files:
            recent_files = get_mock_recent_files()
    except:
        recent_files = get_mock_recent_files()
    
    # Get organization summary
    try:
        summary = get_organization_summary()
    except:
        summary = {
            "files_processed": len(recent_files),
            "files_moved": len(recent_files),
            "files_skipped": 0,
            "errors": 0
        }
    
    return render_template(
        'index.html',
        config=config,
        services_status=services_status,
        recent_files=recent_files,
        summary=summary,
        last_check_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        **system_info
    )

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """Render and handle the configuration page"""
    if request.method == 'POST':
        config = load_config()
        
        # Update config with form values
        config['watch_directory'] = request.form.get('watch_directory', DEFAULT_CONFIG['watch_directory'])
        config['output_directory'] = request.form.get('output_directory', DEFAULT_CONFIG['output_directory'])
        config['api_url'] = request.form.get('api_url', DEFAULT_CONFIG['api_url'])
        config['n8n_url'] = request.form.get('n8n_url', DEFAULT_CONFIG['n8n_url'])
        
        try:
            config['check_interval'] = int(request.form.get('check_interval', DEFAULT_CONFIG['check_interval']))
        except ValueError:
            config['check_interval'] = DEFAULT_CONFIG['check_interval']
        
        config['log_level'] = request.form.get('log_level', DEFAULT_CONFIG['log_level'])
        config['auto_restart'] = 'auto_restart' in request.form
        config['theme'] = request.form.get('theme', DEFAULT_CONFIG['theme'])
        config['enable_analytics'] = 'enable_analytics' in request.form
        config['enable_notifications'] = 'enable_notifications' in request.form
        
        if save_config(config):
            flash("Configuration saved successfully", "success")
            return redirect(url_for('config_page'))
        else:
            flash("Failed to save configuration", "error")
            return render_template('config.html', config=config, error="Failed to save configuration")
    
    # GET request
    config = load_config()
    return render_template('config.html', config=config)

@app.route('/logs')
def logs_page():
    """Render logs page"""
    before = request.args.get('before')
    limit = min(int(request.args.get('limit', 50)), 1000)  # Prevent abuse
    logs, more_logs = get_recent_logs(limit=limit, before=before)
    
    if request.headers.get('HX-Request'):
        # Response for HTMX request (partial content)
        return render_template('partials/logs_content.html', logs=logs, more_logs=more_logs)
    
    return render_template('logs.html', logs=logs, more_logs=more_logs)

@app.route('/logs/stream')
def stream_logs():
    """Stream logs in real-time using server-sent events"""
    def generate():
        # Send initial set of logs
        logs, _ = get_recent_logs(limit=20)
        last_timestamp = logs[0]['timestamp'] if logs else None
        yield f"data: {json.dumps(logs)}\n\n"
        
        while True:
            time.sleep(2)  # Check for new logs every 2 seconds
            if last_timestamp:
                new_logs, _ = get_recent_logs(limit=20, before=last_timestamp)
                if new_logs:
                    last_timestamp = new_logs[0]['timestamp']
                    yield f"data: {json.dumps(new_logs)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api-key', methods=['GET', 'POST'])
def api_key_page():
    """Render and handle API key page"""
    message = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate':
            new_key = generate_api_key()
            if new_key:
                message = "New API key generated successfully"
            else:
                message = "Failed to generate new API key"
    
    api_key = load_api_key()
    return render_template('api_key.html', api_key=api_key, message=message)

@app.route('/organize-now', methods=['GET', 'POST'])
def organize_now():
    """Trigger an immediate file organization"""
    if request.method == 'POST':
        source_dir = request.form.get('source_dir')
        target_dir = request.form.get('target_dir')
    else:
        config = load_config()
        source_dir = config['watch_directory']
        target_dir = config['output_directory']
    
    api_key = load_api_key()
    
    if not api_key:
        flash("No API key found. Please generate one.", "error")
        return redirect(url_for('index'))
    
    try:
        config = load_config()
        response = requests.post(
            f"{config['api_url']}/api/organize",
            headers={"X-API-Key": api_key},
            json={"source_directory": source_dir, "target_directory": target_dir},
            timeout=5
        )
        
        if response.status_code == 200:
            flash("File organization started successfully", "success")
        else:
            flash(f"API returned error: {response.text}", "error")
    except requests.exceptions.RequestException as e:
        flash(f"Failed to connect to API: {e}", "error")
    
    return redirect(url_for('index'))

@app.route('/restart-services', methods=['POST'])
def restart_services_action():
    """Handle service restart requests"""
    services = request.form.getlist('services')
    
    if not services:
        flash("No services selected", "error")
        return redirect(url_for('index'))
    
    results = restart_services(services)
    
    # Check if any service failed to restart
    if not all(results.values()):
        failed_services = [service for service, result in results.items() if not result]
        flash(f"Failed to restart: {', '.join(failed_services)}", "error")
    else:
        flash(f"Successfully restarted services: {', '.join(results.keys())}", "success")
    
    return redirect(url_for('index'))

@app.route('/api/status')
def api_status():
    """JSON endpoint for service status"""
    services_status = check_services()
    system_info = get_system_info()
    
    return jsonify({
        "services": services_status,
        "system": system_info,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/api/organize', methods=['POST'])
def api_organize():
    """API endpoint to trigger file organization"""
    api_key = request.headers.get('X-API-Key')
    if not api_key or api_key != load_api_key():
        return jsonify({"error": "Invalid API key"}), 401
    
    data = request.json
    source_dir = data.get('source_directory')
    target_dir = data.get('target_directory')
    
    config = load_config()
    if not source_dir:
        source_dir = config['watch_directory']
    if not target_dir:
        target_dir = config['output_directory']
    
    try:
        response = requests.post(
            f"{config['api_url']}/organize",
            headers={"X-API-Key": api_key},
            json={"source_directory": source_dir, "target_directory": target_dir},
            timeout=5
        )
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

def main():
    """Main function to run the web interface"""
    port = int(os.environ.get('WEB_INTERFACE_PORT', 8080))
    host = os.environ.get('WEB_INTERFACE_HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting web interface on {host}:{port}")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main() 