#!/bin/bash

# Test script for File Organizer AI Agent

# Create test directory structure
mkdir -p ~/file-organizer-test/source
mkdir -p ~/file-organizer-test/target

# Create test files of different types
touch ~/file-organizer-test/source/document1.pdf
touch ~/file-organizer-test/source/document2.docx
touch ~/file-organizer-test/source/image1.jpg
touch ~/file-organizer-test/source/image2.png
touch ~/file-organizer-test/source/video1.mp4
touch ~/file-organizer-test/source/code1.py
touch ~/file-organizer-test/source/archive1.zip

# Add some content to the files
echo "Test PDF content" > ~/file-organizer-test/source/document1.pdf
echo "Test DOCX content" > ~/file-organizer-test/source/document2.docx
echo "Test JPG content" > ~/file-organizer-test/source/image1.jpg
echo "Test PNG content" > ~/file-organizer-test/source/image2.png
echo "Test MP4 content" > ~/file-organizer-test/source/video1.mp4
echo "print('Hello World')" > ~/file-organizer-test/source/code1.py
echo "Test ZIP content" > ~/file-organizer-test/source/archive1.zip

# Run the agent directly (CLI mode)
echo "Testing the agent in CLI mode..."
python3 file_organizer_agent.py --source ~/file-organizer-test/source --target ~/file-organizer-test/target --organize-by extension

# Check the results
echo "Checking the results..."
ls -la ~/file-organizer-test/target/*

# Clean up test directories for API test
rm -rf ~/file-organizer-test/target/*

# Test the API server (if it's running)
echo "Testing the API server..."
API_KEY=$(grep "default" ~/.config/file_organizer/config.json | cut -d'"' -f4 || echo "unknown-key")

curl -X POST http://localhost:3333/organize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{\"config\": {\"source_directory\": \"$HOME/file-organizer-test/source\", \"target_directory\": \"$HOME/file-organizer-test/target\", \"organize_by\": \"extension\"}}"

# Check the results again
echo "Checking the API results..."
ls -la ~/file-organizer-test/target/*

echo "Test complete!" 