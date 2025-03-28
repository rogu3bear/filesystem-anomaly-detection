#!/usr/bin/env python3
"""
Setup script for Docker App installation
"""
from setuptools import setup, find_packages

setup(
    name="docker-app",
    version="0.1.0",
    description="Docker installation and management tools",
    author="Docker App Team",
    author_email="admin@example.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "requests",
        "webbrowser",
    ],
    extras_require={
        "dev": ["pytest", "flake8"],
        "app": ["py2app"],
    },
    entry_points={
        "console_scripts": [
            "docker-setup=setup.manager:main",
        ],
    },
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
) 