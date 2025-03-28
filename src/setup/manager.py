import curses
import os
import shutil
import subprocess
import socket
import time
import signal
import sys
import webbrowser
import platform

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class SetupManager:
    def __init__(self):
        self.working_dir = os.getcwd()
        self.config = {
            "base_directory": self.working_dir,
            "create_missing_dirs": True,
            "backup_existing_files": True,
            "server_port": 8080,  # Default port
            "default_timeout": 5   # Default timeout for operations
        }
        self.server_process = None
        # Domain rules
        self.max_dir_depth = 10    # Prevent navigation too deep
        self.required_disk_space = 100 * 1024 * 1024  # 100MB minimum
        self.is_macos = platform.system() == 'Darwin'
        
    def main_menu(self, stdscr):
        curses.curs_set(0)
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        
        menu = [
            "Change Working Directory", 
            "Create New Directory", 
            "Upload File (Simple)",
            "Toggle Auto-Create Directories",
            "Toggle Backup Existing Files",
            "Verify Setup & Dependencies",
            "Launch Web Application",
            "Manage Docker",
            "Push to GitHub",
            "Exit"
        ]
        current_row = 0
        
        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            title = "Setup Manager Interface"
            subtitle = "Use arrow keys to navigate. Press Enter to select."
            
            # Prevent writing outside window boundaries
            if h > 1 and w > len(title):
                stdscr.addstr(1, max(0, min((w - len(title)) // 2, w-len(title)-1)), 
                             title[:w-1], 
                             curses.A_BOLD | curses.A_UNDERLINE)
            
            if h > 2 and w > len(subtitle):
                stdscr.addstr(2, max(0, min((w - len(subtitle)) // 2, w-len(subtitle)-1)), 
                             subtitle[:w-1])
            
            # Current status line - check boundaries
            status_line = f"Current directory: {self.config['base_directory']}"
            if h > 3 and w > 2:
                stdscr.addstr(3, 2, status_line[:w-3])
            
            # Check and show Docker status - with boundary checks
            docker_status, _ = self.check_docker(silent=True)
            if docker_status:
                docker_msg = "Docker: RUNNING"
            else:
                docker_msg = "Docker: NOT RUNNING"
            
            if h > 3 and w > len(docker_msg) + 3:
                if not docker_status and curses.has_colors():
                    stdscr.attron(curses.color_pair(2))
                stdscr.addstr(3, w - len(docker_msg) - 3, docker_msg)
                if not docker_status and curses.has_colors():
                    stdscr.attroff(curses.color_pair(2))
            
            # Display menu options - with boundary checks
            for idx, option in enumerate(menu):
                if idx < len(menu) and 5 + idx < h and w > len(option) + 2:
                    x = 2
                    y = 5 + idx
                    if idx == current_row:
                        stdscr.attron(curses.color_pair(1))
                        stdscr.addstr(y, x, option[:w-3])
                        stdscr.attroff(curses.color_pair(1))
                    else:
                        stdscr.addstr(y, x, option[:w-3])
            
            stdscr.refresh()
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                break
                
            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(menu) - 1:
                current_row += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                if current_row == 0:
                    self.change_directory_curses(stdscr)
                elif current_row == 1:
                    self.create_directory_curses(stdscr)
                elif current_row == 2:
                    self.upload_file_curses(stdscr)
                elif current_row == 3:
                    self.toggle_create_dirs()
                    self.show_message(stdscr, f"Auto-create directories: {'ON' if self.config['create_missing_dirs'] else 'OFF'}")
                elif current_row == 4:
                    self.toggle_backup()
                    self.show_message(stdscr, f"Backup existing files: {'ON' if self.config['backup_existing_files'] else 'OFF'}")
                elif current_row == 5:
                    self.verify_setup_curses(stdscr)
                elif current_row == 6:
                    # Exit curses temporarily
                    curses.endwin()
                    self.launch_application()
                    # Restore curses
                    try:
                        stdscr.refresh()
                    except:
                        pass  # Handle potential errors after returning from launch
                elif current_row == 7:
                    self.check_docker_curses(stdscr)
                elif current_row == 8:
                    # Exit curses temporarily for GitHub push
                    curses.endwin()
                    self.push_to_github()
                    # Restore curses
                    try:
                        stdscr.refresh()
                        self.show_message(stdscr, "GitHub operation completed.")
                    except:
                        pass
                elif current_row == 9:
                    # Clean up before exit
                    self.cleanup()
                    break

    def cleanup(self):
        """Clean up resources before exiting"""
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

    def prompt_input(self, stdscr, prompt, ypos, xpos):
        stdscr.addstr(ypos, xpos, prompt)
        stdscr.refresh()
        curses.echo()
        inp = stdscr.getstr(ypos + 1, xpos, 60).decode("utf-8")
        curses.noecho()
        return inp

    def show_message(self, stdscr, msg, error=False):
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        if error and curses.has_colors():
            stdscr.attron(curses.color_pair(2))
            
        # Handle multi-line messages with boundary checks
        lines = msg.split('\n')
        for i, line in enumerate(lines):
            if i < h and len(line) > 0:
                y = min(h-1, max(0, h // 2 - len(lines) // 2 + i))
                x = max(0, min((w - len(line)) // 2, w-len(line)-1))
                stdscr.addstr(y, x, line[:w-1])
            
        if error and curses.has_colors():
            stdscr.attroff(curses.color_pair(2))
        
        continue_msg = "Press any key to continue..."
        if h > 4 and w > len(continue_msg):
            footer_y = min(h-1, h // 2 + len(lines) // 2 + 2)
            footer_x = max(0, min((w - len(continue_msg)) // 2, w-len(continue_msg)-1))
            stdscr.addstr(footer_y, footer_x, continue_msg)
            
        stdscr.refresh()
        try:
            stdscr.getch()
        except KeyboardInterrupt:
            pass

    def change_directory_curses(self, stdscr):
        stdscr.clear()
        new_dir = self.prompt_input(stdscr, "Enter new directory path (absolute or relative):", 2, 2)
        
        # Check for empty input
        if not new_dir.strip():
            self.show_message(stdscr, "No directory specified.", error=True)
            return
            
        # Handle relative paths
        if not os.path.isabs(new_dir):
            new_dir = os.path.join(self.config["base_directory"], new_dir)
            
        # Check directory depth
        if new_dir.count(os.sep) > self.max_dir_depth:
            self.show_message(stdscr, f"Directory depth exceeds maximum ({self.max_dir_depth})", error=True)
            return
            
        if os.path.exists(new_dir):
            if os.path.isdir(new_dir):
                # Check if we have read/write access
                if not os.access(new_dir, os.R_OK | os.W_OK):
                    self.show_message(stdscr, "Error: No read/write permission for this directory.", error=True)
                    return
                    
                self.config["base_directory"] = new_dir
                self.show_message(stdscr, f"Working directory changed to: {new_dir}")
            else:
                self.show_message(stdscr, "Error: The specified path is not a directory.", error=True)
        else:
            self.show_message(stdscr, "Directory does not exist.")
            if self.config["create_missing_dirs"]:
                choice = self.prompt_input(stdscr, "Create this directory? (y/n):", 5, 2)
                if choice.lower() == 'y':
                    try:
                        os.makedirs(new_dir)
                        self.config["base_directory"] = new_dir
                        self.show_message(stdscr, f"Created and switched to: {new_dir}")
                    except Exception as e:
                        self.show_message(stdscr, f"Error creating directory: {e}", error=True)

    def create_directory_curses(self, stdscr):
        stdscr.clear()
        dir_name = self.prompt_input(stdscr, "Enter new directory name to create:", 2, 2)
        
        # Check for empty input or invalid characters
        if not dir_name.strip() or any(c in r'\/:*?"<>|' for c in dir_name):
            self.show_message(stdscr, "Invalid directory name. Please avoid special characters.", error=True)
            return
            
        new_dir = os.path.join(self.config["base_directory"], dir_name)
        
        if os.path.exists(new_dir):
            self.show_message(stdscr, "Directory already exists.")
        else:
            try:
                # Check available disk space
                _, _, free = shutil.disk_usage(os.path.dirname(new_dir))
                if free < self.required_disk_space:
                    self.show_message(stdscr, 
                                    f"Warning: Only {free // (1024*1024)}MB free space available.\n" +
                                    f"Recommended minimum is {self.required_disk_space // (1024*1024)}MB",
                                    error=True)
                
                os.makedirs(new_dir)
                choice = self.prompt_input(stdscr, f"Directory created: {new_dir}\nSwitch to this directory? (y/n):", 4, 2)
                if choice.lower() == 'y':
                    self.config["base_directory"] = new_dir
                self.show_message(stdscr, f"Directory {new_dir} is ready.")
            except Exception as e:
                self.show_message(stdscr, f"Error creating directory: {e}", error=True)

    def upload_file_curses(self, stdscr):
        """Terminal-based file upload without using Tkinter"""
        stdscr.clear()
        file_path = self.prompt_input(stdscr, "Enter the path of the file to upload:", 2, 2)
        
        if not file_path or not file_path.strip():
            self.show_message(stdscr, "No file path provided.", error=True)
            return
            
        # Handle relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
            
        if not os.path.exists(file_path):
            self.show_message(stdscr, "File does not exist.", error=True)
            return
            
        if not os.path.isfile(file_path):
            self.show_message(stdscr, "The specified path is not a file.", error=True)
            return
            
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB limit
            self.show_message(stdscr, f"File too large: {file_size/(1024*1024):.1f}MB\n" +
                            "Maximum recommended size is 100MB", error=True)
            return
        
        # Check available disk space
        _, _, free = shutil.disk_usage(self.config["base_directory"])
        if free < file_size * 1.5:  # Ensure 50% extra space
            self.show_message(stdscr, "Insufficient disk space for this file", error=True)
            return
        
        result = self.upload_file_by_path(file_path)
        if result:
            self.show_message(stdscr, f"File uploaded: {os.path.basename(file_path)}")
        else:
            self.show_message(stdscr, "File upload failed", error=True)

    def upload_file_by_path(self, file_path):
        if not os.path.exists(file_path):
            return False
            
        filename = os.path.basename(file_path)
        destination = os.path.join(self.config["base_directory"], filename)
        
        try:
            # Create backup if needed
            if os.path.exists(destination) and self.config["backup_existing_files"]:
                backup_file = destination + ".bak"
                shutil.copy2(destination, backup_file)
            
            # Copy the file
            shutil.copy2(file_path, destination)
            return True
        except Exception:
            return False

    def verify_setup_curses(self, stdscr):
        stdscr.clear()
        messages = [f"Base directory: {self.config['base_directory']}"]
        all_good = True
        
        # Check directory exists
        if not os.path.exists(self.config["base_directory"]):
            messages.append("WARNING: Base directory does not exist!")
            all_good = False
        
        # Check permissions
        if not os.access(self.config["base_directory"], os.W_OK):
            messages.append("WARNING: No write permission to base directory!")
            all_good = False
        
        # Check available disk space
        try:
            _, _, free = shutil.disk_usage(self.config["base_directory"])
            if free < self.required_disk_space:
                messages.append(f"WARNING: Low disk space: {free // (1024*1024)}MB free")
                all_good = False
            else:
                messages.append(f"✓ Disk space OK: {free // (1024*1024)}MB free")
        except Exception:
            messages.append("WARNING: Could not check disk space")
            all_good = False
        
        # Check Docker
        docker_ready, docker_msg = self.check_docker(silent=True)
        if docker_ready:
            messages.append("✓ Docker is running")
        else:
            messages.append(f"WARNING: Docker issue - {docker_msg}")
            all_good = False
        
        # Check port availability
        if is_port_in_use(self.config["server_port"]):
            messages.append(f"WARNING: Port {self.config['server_port']} is already in use")
            all_good = False
        else:
            messages.append(f"✓ Port {self.config['server_port']} is available")
        
        # Check application files
        test_script_path = os.path.join(self.config["base_directory"], "test_script.py")
        if os.path.exists(test_script_path):
            messages.append("✓ Application file (test_script.py) found")
        else:
            messages.append("WARNING: Application file (test_script.py) not found")
            all_good = False
            choice = self.prompt_input(stdscr, "Create basic test script file? (y/n):", len(messages) + 2, 2)
            if choice.lower() == 'y':
                if self.create_test_script():
                    messages.append("✓ Created test_script.py")
                    all_good = True
                else:
                    messages.append("ERROR: Failed to create test_script.py")
        
        # Display all messages
        stdscr.clear()
        for i, msg in enumerate(messages):
            # Highlight warnings/errors in red
            if "WARNING" in msg or "ERROR" in msg:
                stdscr.attron(curses.color_pair(2))
                stdscr.addstr(i + 2, 2, msg)
                stdscr.attroff(curses.color_pair(2))
            else:
                stdscr.addstr(i + 2, 2, msg)
        
        # Summary message
        if all_good:
            summary = "✓ All checks passed. System is ready."
        else:
            summary = "⚠ Some checks failed. Please resolve issues before launching."
            
        stdscr.addstr(len(messages) + 4, 2, summary)
        stdscr.addstr(len(messages) + 6, 2, "Press any key to continue...")
        stdscr.refresh()
        stdscr.getch()
        
        return all_good

    def check_docker(self, silent=False):
        try:
            # First try standard Docker CLI check
            result = subprocess.run(
                ["docker", "info"], 
                capture_output=True, 
                text=True, 
                timeout=self.config["default_timeout"]
            )
            
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0]
                return True, first_line
            
            # If that failed, try docker context ls (for Docker Desktop)
            if self.is_macos:
                try:
                    context_result = subprocess.run(
                        ["docker", "context", "ls"], 
                        capture_output=True, 
                        text=True, 
                        timeout=self.config["default_timeout"]
                    )
                    if context_result.returncode == 0:
                        # Docker CLI exists but daemon isn't running
                        return False, "Docker is installed but not running"
                except:
                    pass
                
            return False, "Docker command returned error"
        except subprocess.TimeoutExpired:
            if not silent:
                print("Docker check timed out. Docker may be starting or hung.")
            return False, "Command timed out"
        except FileNotFoundError:
            if not silent:
                print("Docker command not found. Please install Docker.")
            return False, "Docker not installed"
        except Exception as e:
            if not silent:
                print(f"Error checking Docker: {str(e)}")
            return False, str(e)

    def check_docker_curses(self, stdscr):
        stdscr.clear()
        stdscr.addstr(2, 2, "Checking Docker status...")
        stdscr.refresh()
        
        docker_ready, message = self.check_docker()
        if docker_ready:
            self.show_message(stdscr, f"Docker is running:\n{message}")
        else:
            # Try to provide helpful diagnostics
            diagnostics = ["Docker is not running or not properly configured."]
            
            # Check if docker daemon is running
            try:
                ps_result = subprocess.run(
                    ["ps", "aux"], 
                    capture_output=True, 
                    text=True
                )
                if "dockerd" not in ps_result.stdout:
                    diagnostics.append("The Docker daemon does not appear to be running.")
                    
                    # Check if Docker is installed but not running
                    docker_installed = self.is_docker_installed()
                    if docker_installed:
                        diagnostics.append("Docker is installed but not running.")
                        choice = self.prompt_input(stdscr, "Do you want to start Docker? (y/n):", len(diagnostics) + 2, 2)
                        if choice.lower() == 'y':
                            # Temporarily exit curses to show start progress
                            curses.endwin()
                            success = self.start_docker()
                            # Reinitialize curses
                            stdscr = curses.initscr()
                            curses.noecho()
                            curses.cbreak()
                            stdscr.keypad(True)
                            
                            if success:
                                self.show_message(stdscr, "Docker started successfully!")
                                return
                            else:
                                diagnostics.append("Failed to start Docker.")
                    else:
                        diagnostics.append("Docker does not appear to be installed.")
                        choice = self.prompt_input(stdscr, "Do you want to install Docker? (y/n):", len(diagnostics) + 2, 2)
                        if choice.lower() == 'y':
                            # Temporarily exit curses to show installation progress
                            curses.endwin()
                            success = self.install_docker()
                            # Reinitialize curses
                            stdscr = curses.initscr()
                            curses.noecho()
                            curses.cbreak()
                            stdscr.keypad(True)
                            
                            if success:
                                self.show_message(stdscr, "Docker installed successfully! Please restart your terminal to ensure Docker is properly configured.")
                                return
                            else:
                                diagnostics.append("Failed to install Docker.")
            except Exception as e:
                diagnostics.append(f"Error checking Docker daemon: {str(e)}")
                
            self.show_message(stdscr, "\n".join(diagnostics), error=True)

    def is_docker_installed(self):
        """Check if Docker is installed but not necessarily running"""
        try:
            # Check for Docker CLI
            result = subprocess.run(
                ["which", "docker"], 
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def start_docker(self):
        """Start Docker if it's installed but not running"""
        try:
            print("Attempting to start Docker...")
            
            if self.is_macos:
                # Check for Docker Desktop first
                app_path = "/Applications/Docker.app"
                if os.path.exists(app_path):
                    print("Found Docker Desktop, attempting to start it...")
                    try:
                        subprocess.run(["open", "-a", "Docker"], check=True)
                        
                        # Wait for Docker to start (with timeout)
                        print("Waiting for Docker to start (this may take a minute)...")
                        for i in range(60):  # 60 second timeout - Docker Desktop can be slow
                            print(".", end="", flush=True)
                            time.sleep(1)
                            docker_ready, _ = self.check_docker(silent=True)
                            if docker_ready:
                                print("\nDocker is now running!")
                                return True
                        
                        print("\nTimed out waiting for Docker to start.")
                        print("Try starting Docker Desktop manually.")
                        return False
                    except subprocess.CalledProcessError:
                        print("Failed to start Docker Desktop.")
                
                # Check for docker-machine as fallback
                try:
                    result = subprocess.run(["which", "docker-machine"], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("Found docker-machine, attempting to start default machine...")
                        try:
                            # Start the default machine
                            subprocess.run(["docker-machine", "start", "default"], check=True)
                            
                            # Set environment variables
                            env_result = subprocess.run(
                                ["docker-machine", "env", "default"], 
                                capture_output=True, text=True, check=True
                            )
                            
                            # Parse and set environment variables
                            for line in env_result.stdout.splitlines():
                                if line.startswith('export '):
                                    var_def = line.replace('export ', '').strip()
                                    if '=' in var_def:
                                        var_name, var_value = var_def.split('=', 1)
                                        os.environ[var_name] = var_value.strip('"')
                            
                            print("Docker machine started and environment variables set.")
                            
                            # Check if Docker is now working
                            for i in range(10):
                                time.sleep(1)
                                docker_ready, _ = self.check_docker(silent=True)
                                if docker_ready:
                                    print("Docker is now running!")
                                    return True
                            
                            print("Docker machine started but Docker is not responding.")
                            return False
                        except subprocess.CalledProcessError as e:
                            print(f"Failed to start docker-machine: {e}")
                            return False
                except:
                    pass
            else:
                # For Linux systems
                try:
                    if os.geteuid() == 0:  # Check if running as root
                        command = ["systemctl", "start", "docker"]
                    else:
                        command = ["sudo", "systemctl", "start", "docker"]
                    
                    print(f"Running: {' '.join(command)}")
                    subprocess.run(command, check=True)
                    
                    # Wait for Docker to start
                    print("Waiting for Docker to start...")
                    for i in range(10):
                        print(".", end="", flush=True)
                        time.sleep(1)
                        docker_ready, _ = self.check_docker(silent=True)
                        if docker_ready:
                            print("\nDocker is now running!")
                            return True
                    
                    print("\nDocker service started, but Docker is not responding.")
                    return False
                except subprocess.CalledProcessError as e:
                    print(f"Failed to start Docker service: {e}")
                    return False
                except Exception as e:
                    print(f"Error: {str(e)}")
                    return False
            
            print("Could not find a way to start Docker on this system.")
            return False
        except Exception as e:
            print(f"Error starting Docker: {str(e)}")
            return False
    
    def install_docker(self):
        """Install Docker if not already installed"""
        try:
            print("Preparing to install Docker...")
            
            if self.is_macos:
                # For macOS, recommend Docker Desktop for simplicity and reliability
                print("For macOS, we recommend installing Docker Desktop for the best experience.")
                print("Would you like to:")
                print("1. Download Docker Desktop (recommended)")
                print("2. Install Docker CLI tools via Homebrew")
                print("3. Cancel installation")
                
                choice = input("Enter your choice (1-3): ")
                
                if choice == "1":
                    print("Opening Docker Desktop download page...")
                    webbrowser.open("https://www.docker.com/products/docker-desktop")
                    print("After installing Docker Desktop, please restart this application.")
                    return False
                elif choice == "2":
                    # Check if Homebrew is installed
                    brew_installed = False
                    try:
                        subprocess.run(["which", "brew"], check=True, stdout=subprocess.PIPE)
                        brew_installed = True
                    except subprocess.CalledProcessError:
                        print("Homebrew not found.")
                        print("Would you like to install Homebrew first? (y/n)")
                        if input().lower() == 'y':
                            print("Installing Homebrew...")
                            try:
                                install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
                                subprocess.run(install_cmd, shell=True, check=True)
                                brew_installed = True
                            except subprocess.CalledProcessError as e:
                                print(f"Failed to install Homebrew: {e}")
                                return False
                        else:
                            return False
                    
                    if brew_installed:
                        print("Installing Docker CLI tools via Homebrew...")
                        try:
                            # Install Docker CLI only
                            subprocess.run(["brew", "install", "docker", "docker-compose"], check=True)
                            print("Docker CLI tools installed.")
                            
                            # Create a Docker context
                            print("\nNOTE: You've installed Docker CLI tools only.")
                            print("You'll need a Docker Engine to connect to.")
                            print("Options:")
                            print("1. Install Docker Desktop: https://www.docker.com/products/docker-desktop")
                            print("2. Set up docker-machine (requires VirtualBox)")
                            print("3. Connect to a remote Docker host")
                            
                            return True
                        except subprocess.CalledProcessError as e:
                            print(f"Error installing Docker with Homebrew: {e}")
                            return False
                else:
                    print("Docker installation cancelled.")
                    return False
            else:
                # For Linux
                if os.path.exists("/etc/debian_version"):
                    # Debian/Ubuntu
                    print("Installing Docker on Debian/Ubuntu...")
                    try:
                        commands = [
                            "sudo apt-get update",
                            "sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common",
                            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -",
                            "sudo add-apt-repository \"deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable\"",
                            "sudo apt-get update",
                            "sudo apt-get install -y docker-ce docker-ce-cli containerd.io"
                        ]
                        
                        for cmd in commands:
                            print(f"Running: {cmd}")
                            subprocess.run(cmd, shell=True, check=True)
                        
                        # Add current user to docker group
                        user = os.environ.get("USER")
                        if user:
                            print(f"Adding user {user} to docker group...")
                            subprocess.run(f"sudo usermod -aG docker {user}", shell=True, check=True)
                            print(f"NOTE: You may need to log out and log back in for group changes to take effect.")
                        
                        print("Docker installed successfully!")
                        return True
                    except subprocess.CalledProcessError as e:
                        print(f"Error installing Docker: {e}")
                        return False
                elif os.path.exists("/etc/fedora-release"):
                    # Fedora
                    print("Installing Docker on Fedora...")
                    try:
                        commands = [
                            "sudo dnf -y install dnf-plugins-core",
                            "sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo",
                            "sudo dnf install -y docker-ce docker-ce-cli containerd.io"
                        ]
                        
                        for cmd in commands:
                            print(f"Running: {cmd}")
                            subprocess.run(cmd, shell=True, check=True)
                        
                        # Add current user to docker group
                        user = os.environ.get("USER")
                        if user:
                            print(f"Adding user {user} to docker group...")
                            subprocess.run(f"sudo usermod -aG docker {user}", shell=True, check=True)
                            print(f"NOTE: You may need to log out and log back in for group changes to take effect.")
                        
                        print("Docker installed successfully!")
                        return True
                    except subprocess.CalledProcessError as e:
                        print(f"Error installing Docker: {e}")
                        return False
                else:
                    print("Unsupported Linux distribution.")
                    print("Please follow the official Docker installation guide:")
                    print("https://docs.docker.com/engine/install/")
                    return False
                
        except Exception as e:
            print(f"Error installing Docker: {str(e)}")
            return False
    
    def create_docker_install_script(self):
        """Create a script to install Docker on macOS without Docker Desktop"""
        with open("install_docker.sh", "w") as f:
            f.write('''#!/bin/bash
set -e

echo "Installing Docker on macOS without Docker Desktop"
echo "------------------------------------------------"

# Check if Homebrew is installed, install if not
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH
    if [[ -f ~/.zshrc ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f ~/.bash_profile ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.bash_profile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    echo "Homebrew installed successfully."
else
    echo "Homebrew already installed."
fi

# Install Docker CLI
echo "Installing Docker CLI and tools..."
brew install docker docker-compose docker-machine

# Install VirtualBox if not already installed (needed for docker-machine)
if ! command -v VBoxManage &> /dev/null; then
    echo "Installing VirtualBox..."
    brew install --cask virtualbox
    
    echo "VirtualBox installed, you may need to approve system extensions in Security & Privacy settings."
    echo "After approving, press Enter to continue..."
    read -p ""
fi

# Create and start a Docker machine
echo "Setting up Docker machine..."
docker-machine create --driver virtualbox default || echo "Docker machine may already exist"
docker-machine start default

# Set up Docker environment
echo "Configuring Docker environment..."
echo 'eval "$(docker-machine env default)"' >> ~/.zshrc
echo 'eval "$(docker-machine env default)"' >> ~/.bash_profile

# Set environment variables for current session
eval "$(docker-machine env default)"

# Test Docker
echo "Testing Docker installation..."
docker version
docker run hello-world

echo "Docker installation completed successfully!"
echo "Please restart your terminal or run: eval \"$(docker-machine env default)\""
''')
        print("Created Docker installation script: install_docker.sh")

    def push_to_github(self):
        """Push changes to GitHub 'macos' branch"""
        try:
            print("Pushing changes to GitHub 'macos' branch...")
            
            # Check if git is installed
            try:
                subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("Git is not installed or not in PATH.")
                return False
            
            # Check if we're in a git repo
            try:
                subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, stdout=subprocess.PIPE)
            except subprocess.CalledProcessError:
                print("Not inside a git repository.")
                return False
            
            # Create and checkout macos branch
            try:
                # Check if branch exists
                result = subprocess.run(
                    ["git", "show-ref", "--verify", "--quiet", "refs/heads/macos"],
                    stderr=subprocess.PIPE
                )
                
                if result.returncode != 0:
                    # Branch doesn't exist, create it
                    subprocess.run(["git", "checkout", "-b", "macos"], check=True)
                else:
                    # Branch exists, just check it out
                    subprocess.run(["git", "checkout", "macos"], check=True)
                
                # Add all changes
                subprocess.run(["git", "add", "."], check=True)
                
                # Commit changes
                subprocess.run(
                    ["git", "commit", "-m", "Updated setup manager with Docker management and macOS support"],
                    check=True
                )
                
                # Push to GitHub
                subprocess.run(["git", "push", "-u", "origin", "macos"], check=True)
                
                print("Successfully pushed changes to GitHub 'macos' branch!")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"Git operation failed: {e}")
                return False
                
        except Exception as e:
            print(f"Error pushing to GitHub: {str(e)}")
            return False

    def find_available_port(self, start_port=8080, max_attempts=10):
        """Find an available port starting from start_port"""
        port = start_port
        for _ in range(max_attempts):
            if not is_port_in_use(port):
                return port
            port += 1
        return None

    def create_index_html(self):
        """Create a basic index.html for the test server"""
        index_path = os.path.join(self.config["base_directory"], "index.html")
        try:
            with open(index_path, 'w') as f:
                f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Test Application</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>Test Application</h1>
    <div class="success">
        <h2>Success!</h2>
        <p>Your web server is running correctly.</p>
    </div>
    <p>This is a simple test page to confirm your setup is working properly.</p>
    <p>Current time: <span id="current-time"></span></p>
    
    <script>
        // Update the current time
        function updateTime() {
            document.getElementById('current-time').textContent = new Date().toLocaleString();
        }
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>''')
            return True
        except Exception:
            return False

    def create_test_script(self):
        """Create a basic test script if it doesn't exist"""
        test_script_path = os.path.join(self.config["base_directory"], "test_script.py")
        try:
            with open(test_script_path, 'w') as f:
                f.write('''def test():
    print("Test Successful")

if __name__ == "__main__":
    test()
''')
            return True
        except Exception:
            return False

    def launch_application(self):
        """Launch the web application after verifying Docker and necessary conditions."""
        # Clear the screen in the terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=== Setup Manager - Web Application Launch ===")
        print(f"Working directory: {self.config['base_directory']}")
        
        # Check Docker status
        print("\nChecking Docker status...")
        docker_ready, docker_msg = self.check_docker()
        if docker_ready:
            print(f"✓ Docker is running: {docker_msg}")
        else:
            print(f"⚠ Docker issue: {docker_msg}")
            retry = input("Docker is not running properly. Try to launch anyway? (y/n): ").lower()
            if retry != 'y':
                input("Press Enter to return to menu...")
                return
        
        # Create test files if needed
        test_script_path = os.path.join(self.config["base_directory"], "test_script.py")
        if not os.path.exists(test_script_path):
            print("\nApplication file (test_script.py) not found.")
            create = input("Create basic test script file? (y/n): ").lower()
            if create == 'y':
                if self.create_test_script():
                    print("✓ Created test_script.py")
                else:
                    print("⚠ Failed to create test_script.py")
                    input("Press Enter to return to menu...")
                    return
            else:
                input("Press Enter to return to menu...")
                return
        
        # Create index.html if it doesn't exist
        index_path = os.path.join(self.config["base_directory"], "index.html")
        if not os.path.exists(index_path):
            print("\nCreating a basic index.html file...")
            if self.create_index_html():
                print("✓ Created index.html")
            else:
                print("⚠ Failed to create index.html")
        
        # Find an available port
        port = self.find_available_port(self.config["server_port"])
        if not port:
            print(f"\n⚠ Could not find an available port (tried {self.config['server_port']} and above)")
            input("Press Enter to return to menu...")
            return
        
        self.config["server_port"] = port
        print(f"\nLaunching HTTP server on port {port}...")
        
        # Try to stop any existing server process
        self.cleanup()
        
        # Change to the target directory
        current_dir = os.getcwd()
        try:
            os.chdir(self.config["base_directory"])
            
            # Start the HTTP server
            self.server_process = subprocess.Popen(
                ["python", "-m", "http.server", str(port)],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Short delay to ensure server has started
            time.sleep(1)
            
            # Check if server process is still running
            if self.server_process.poll() is not None:
                stderr = self.server_process.stderr.read().decode('utf-8')
                print(f"\n⚠ Failed to start HTTP server: {stderr}")
                input("Press Enter to return to menu...")
                return
            
            # Server is running, open the web browser
            server_url = f"http://localhost:{port}"
            print(f"✓ HTTP server running at {server_url}")
            print("Opening web browser...")
            webbrowser.open(server_url)
            
            print("\nPress Ctrl+C to shut down the server and return to menu...")
            
            # Wait until user presses Ctrl+C
            try:
                while True:
                    time.sleep(0.5)
                    # Check if server is still running
                    if self.server_process.poll() is not None:
                        print("\n⚠ Server stopped unexpectedly")
                        break
            except KeyboardInterrupt:
                print("\nShutting down server...")
            finally:
                self.cleanup()
                
        except Exception as e:
            print(f"\n⚠ Error: {str(e)}")
        finally:
            # Change back to the original directory
            os.chdir(current_dir)
            input("\nPress Enter to return to menu...")

    def toggle_create_dirs(self):
        self.config["create_missing_dirs"] = not self.config["create_missing_dirs"]

    def toggle_backup(self):
        self.config["backup_existing_files"] = not self.config["backup_existing_files"]

    def run(self):
        try:
            curses.wrapper(self.main_menu)
        except KeyboardInterrupt:
            print("Setup Manager terminated by user.")
        finally:
            # Ensure we clean up any resources
            self.cleanup()

def main():
    """Main entry point for command-line use"""
    # Set up signal handler for graceful exit
    def signal_handler(sig, frame):
        print("\nSetup Manager is shutting down...")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    setup = SetupManager()
    setup.run()
    return 0

if __name__ == "__main__":
    main() 