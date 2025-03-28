#!/usr/bin/env python3
"""
Setup script for building the Setup Manager as a macOS app.
Usage:
    python scripts/setup_app.py py2app
"""

from setuptools import setup
import sys
import os

# Add the src directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

APP = ['src/setup/main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['curses', 'subprocess', 'shutil', 'socket', 'webbrowser', 'setup'],
    'plist': {
        'CFBundleName': 'Setup Manager',
        'CFBundleDisplayName': 'Setup Manager',
        'CFBundleIdentifier': 'com.example.setupmanager',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'NSHumanReadableCopyright': 'GPL-3.0 License',
        'CFBundleIconFile': 'app_icon.icns',
    },
    'iconfile': 'app_icon.icns',
}

setup(
    name='Setup Manager',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 