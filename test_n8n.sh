#!/bin/bash

# Test script for n8n workflow integration

# Create test directory structure
mkdir -p ~/file-organizer-test/n8n-source
mkdir -p ~/file-organizer-test/n8n-target

# Create test files of different types
touch ~/file-organizer-test/n8n-source/document1.pdf
touch ~/file-organizer-test/n8n-source/image1.jpg
touch ~/file-organizer-test/n8n-source/video1.mp4

# Add some content to the files
echo "Test PDF content" > ~/file-organizer-test/n8n-source/document1.pdf
echo "Test JPG content" > ~/file-organizer-test/n8n-source/image1.jpg
echo "Test MP4 content" > ~/file-organizer-test/n8n-source/video1.mp4

# Check if n8n is running
if curl -s http://localhost:5678/healthz > /dev/null; then
    echo "n8n is running."
else
    echo "n8n is not running. Please start n8n first."
    exit 1
fi

# Extract API Key
API_KEY=$(grep "default" ~/.config/file_organizer/config.json | cut -d'"' -f4 || echo "unknown-key")

echo "===================================================================="
echo "n8n Test Setup"
echo "===================================================================="
echo "1. Open n8n in your browser: http://localhost:5678"
echo "2. Go to Workflows and make sure 'File Organizer Agent' is active"
echo "3. Update the workflow variables if not already set:"
echo "   - FILE_ORGANIZER_API_URL: http://localhost:3333"
echo "   - FILE_ORGANIZER_API_KEY: $API_KEY"
echo "   - WATCH_FOLDER: $HOME/file-organizer-test/n8n-source"
echo "4. Save the workflow settings"
echo "5. Manually trigger the workflow or add a new file to the source directory"
echo "   to trigger the workflow automatically"
echo "===================================================================="

# Wait for confirmation to continue
read -p "Press Enter to continue after setting up the workflow..." 

# Add another file to trigger the workflow
echo "Adding a new file to trigger the workflow..."
echo "This is a test text file" > ~/file-organizer-test/n8n-source/test_trigger.txt

# Wait for the workflow to process
echo "Waiting for n8n to process the file (5 seconds)..."
sleep 5

# Check the results
echo "Checking the results..."
ls -la ~/file-organizer-test/n8n-target/*/* 2>/dev/null || echo "No organized files found. Check n8n logs for errors."

echo "Test complete!"
echo "Note: If you don't see organized files, check the n8n logs at ~/n8n-data/logs/n8n.log" 