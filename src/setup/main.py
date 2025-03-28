#!/usr/bin/env python3
"""
Main entry point for the Docker Setup Manager
"""
import os
import sys
from .manager import SetupManager

def main():
    """Main entry point for the Docker Setup Manager"""
    setup = SetupManager()
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\nSetup Manager terminated by user.")
        return 1
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 