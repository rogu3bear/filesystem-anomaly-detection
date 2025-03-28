# File Organizer AI Agent Testing Guide

This guide provides step-by-step instructions for testing the File Organizer AI Agent and its integration with n8n.

## Prerequisites

Make sure you have completed the setup steps in the README.md file and that both the agent and n8n are running.

## 1. Basic Agent Testing

The `test_agent.sh` script will test the agent's basic functionality by:
1. Creating test files in a source directory
2. Running the agent directly in CLI mode
3. Testing the agent through its API

### Running the Basic Test

```bash
# Make the test script executable
chmod +x test_agent.sh

# Run the test script
./test_agent.sh
```

### Expected Results

You should see the following output:
- Confirmation that test files were created
- Results of the CLI test showing files organized by type
- Results of the API test showing files organized by type

The files should be organized into directories like `documents`, `images`, `videos`, etc.

## 2. n8n Integration Testing

The `test_n8n.sh` script will test the n8n workflow integration by:
1. Creating test files in a watched directory
2. Configuring the n8n workflow
3. Triggering the workflow
4. Checking the results

### Running the n8n Integration Test

```bash
# Make the test script executable
chmod +x test_n8n.sh

# Run the test script
./test_n8n.sh
```

### Expected Results

The script will guide you through:
1. Setting up the n8n workflow with the correct parameters
2. Triggering the workflow by adding a file
3. Checking the results of the file organization

## 3. Manual Testing

You can also test the agent manually to verify specific aspects:

### API Endpoints

Test the health endpoint:
```bash
curl http://localhost:3333/health
```
Expected response: `{"status": "ok", "version": "1.0.0", "secured": true}`

Test the organization endpoint (replace YOUR_API_KEY with your key):
```bash
curl -X POST http://localhost:3333/organize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"config": {"source_directory": "~/Downloads", "target_directory": "~/Organized", "organize_by": "extension"}}'
```

### Configuration Changes

Test updating the configuration:
```bash
curl -X POST http://localhost:3333/config \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"organize_by": "date"}'
```

Verify the configuration was updated:
```bash
curl -X GET http://localhost:3333/config \
  -H "X-API-Key: YOUR_API_KEY"
```

## 4. Troubleshooting

If the tests fail, check the following:

### Agent Issues
- Check the agent logs: `cat file_organizer.log`
- Verify the API server logs: `cat api_server.log`
- Make sure the API key in the requests matches the one in your configuration

### n8n Issues
- Check the n8n logs: `cat ~/n8n-data/logs/n8n.log`
- Verify n8n is running: `curl http://localhost:5678/healthz`
- Make sure the workflow is activated in the n8n interface

### Common Issues
- **Permission denied**: Make sure the source and target directories are accessible
- **API key error**: Check that your API key is correctly set in the requests
- **Files not being organized**: Verify the source directory path is correct
- **n8n workflow not triggering**: Make sure the Watch Folder node has the correct path 