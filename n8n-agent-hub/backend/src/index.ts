import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import mongoose from 'mongoose';
import dotenv from 'dotenv';
import { errorHandler } from './middleware/errorHandler';
import routes from './routes';
import path from 'path';
import fs from 'fs';
import bodyParser from 'body-parser';
import { spawn } from 'child_process';
import authMiddleware from './middleware/auth';

// Load environment variables
dotenv.config();

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;
const isSetupMode = process.argv.includes('--setup') || process.argv.includes('setup-server');

// Middleware for security and logging
app.use(cors());
app.use(helmet({
  contentSecurityPolicy: isSetupMode ? false : undefined // Disable CSP in setup mode for simplicity
}));
app.use(morgan('dev'));
app.use(express.json({ limit: '1mb' })); // Limit payload size
app.use(express.urlencoded({ extended: true, limit: '1mb' }));
app.use(express.static(path.join(__dirname, '../../frontend/build')));

// Function to safely get home directory
const getHomeDir = (): string => {
  const homeDir = process.env.HOME || process.env.USERPROFILE || '/tmp';
  return homeDir;
};

// Check if n8n is running
const checkN8nStatus = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:5678/healthz', { 
      signal: AbortSignal.timeout(3000) // Add timeout
    });
    return response.ok;
  } catch (error) {
    console.log('n8n health check failed:', error instanceof Error ? error.message : 'Unknown error');
    return false;
  }
};

// Setup mode endpoints
if (isSetupMode) {
  app.get('/api/setup/status', async (req, res) => {
    try {
      const n8nRunning = await checkN8nStatus();
      const configDir = path.join(getHomeDir(), '.config/file_anomaly_detection');
      const configExists = fs.existsSync(path.join(configDir, 'config.json'));
      
      // Check for n8n in different possible paths
      const n8nPaths = [
        '/usr/local/bin/n8n',
        '/usr/bin/n8n',
        path.join(getHomeDir(), '.npm/bin/n8n')
      ];
      const n8nInstalled = n8nPaths.some(p => fs.existsSync(p));
      
      res.json({
        n8nInstalled,
        n8nRunning,
        configExists,
        configDir,
        systemInfo: {
          platform: process.platform,
          nodeVersion: process.version,
          homeDir: getHomeDir()
        }
      });
    } catch (error) {
      console.error('Status check error:', error);
      res.status(500).json({ 
        error: 'Failed to get setup status',
        message: error instanceof Error ? error.message : 'Unknown error' 
      });
    }
  });

  app.post('/api/setup/configure', async (req, res) => {
    try {
      const { sourceDir, targetDir, organizeBy, scanInterval } = req.body;
      
      // Validate input
      if (sourceDir && !sourceDir.startsWith('/')) {
        return res.status(400).json({ error: 'Source directory must be an absolute path' });
      }
      
      if (targetDir && !targetDir.startsWith('/')) {
        return res.status(400).json({ error: 'Target directory must be an absolute path' });
      }
      
      // Create config directory if it doesn't exist
      const configDir = path.join(getHomeDir(), '.config/file_anomaly_detection');
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      // Generate API key if not provided
      const apiKey = req.body.apiKey || require('crypto').randomBytes(24).toString('hex');
      
      // Write config file with safe defaults
      const config = {
        source_directory: sourceDir || path.join(getHomeDir(), 'Downloads'),
        target_directory: targetDir || path.join(getHomeDir(), 'Organized'),
        organize_by: organizeBy || 'extension',
        scan_interval: Math.max(10, Math.min(3600, parseInt(scanInterval) || 300)), // Between 10s and 1h
        api_key: apiKey,
        created_at: new Date().toISOString(),
        version: '1.0'
      };
      
      fs.writeFileSync(
        path.join(configDir, 'config.json'),
        JSON.stringify(config, null, 2),
        { mode: 0o600 } // Secure file permissions - owner read/write only
      );
      
      // Create target directories if they don't exist
      const targetDirPath = config.target_directory;
      if (!fs.existsSync(targetDirPath)) {
        fs.mkdirSync(targetDirPath, { recursive: true });
        
        // Create standard subdirectories
        const categories = ['Documents', 'Images', 'Videos', 'Audio', 'Archives', 'Applications', 'Other'];
        categories.forEach(category => {
          fs.mkdirSync(path.join(targetDirPath, category), { recursive: true });
        });
      }
      
      res.json({ 
        success: true, 
        message: 'Configuration saved successfully',
        apiKey,
        configPath: path.join(configDir, 'config.json')
      });
    } catch (error) {
      console.error('Configuration error:', error);
      res.status(500).json({ 
        error: 'Failed to save configuration', 
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });

  app.post('/api/setup/start-n8n', async (req, res) => {
    try {
      // Check if n8n is already running
      const n8nRunning = await checkN8nStatus();
      
      if (n8nRunning) {
        return res.json({ success: true, message: 'n8n is already running' });
      }
      
      // Try to find n8n executable
      const n8nPaths = [
        '/usr/local/bin/n8n',
        '/usr/bin/n8n',
        path.join(getHomeDir(), '.npm/bin/n8n')
      ];
      
      let n8nPath = '';
      for (const p of n8nPaths) {
        if (fs.existsSync(p)) {
          n8nPath = p;
          break;
        }
      }
      
      if (!n8nPath) {
        return res.status(404).json({ 
          error: 'n8n executable not found',
          paths: n8nPaths
        });
      }
      
      // Start n8n
      const n8nProcess = spawn(n8nPath, ['start'], {
        detached: true,
        stdio: 'ignore',
        env: { ...process.env, N8N_BASIC_AUTH_ACTIVE: 'false' }
      });
      
      // Detach the process so it continues running after this process exits
      n8nProcess.unref();
      
      // Wait a moment to see if it started
      await new Promise(resolve => setTimeout(resolve, 2000));
      const started = await checkN8nStatus();
      
      res.json({ 
        success: started, 
        message: started ? 'n8n started successfully' : 'n8n was launched but may take time to start'
      });
    } catch (error) {
      console.error('n8n start error:', error);
      res.status(500).json({ 
        error: 'Failed to start n8n', 
        message: error instanceof Error ? error.message : 'Unknown error' 
      });
    }
  });

  app.post('/api/setup/install-n8n', async (req, res) => {
    try {
      // Check if we have the necessary permissions to install globally
      const testPath = '/usr/local/bin';
      let installGlobally = false;
      
      try {
        const testFile = path.join(testPath, '.n8n-test');
        fs.writeFileSync(testFile, 'test', { mode: 0o755 });
        fs.unlinkSync(testFile);
        installGlobally = true;
      } catch (e) {
        // Can't write to /usr/local/bin, install locally for the user
        installGlobally = false;
      }
      
      // Prepare install command
      const npmCmd = installGlobally ? 
        ['install', 'n8n', '-g'] : 
        ['install', 'n8n', '--global', '--prefix', path.join(getHomeDir(), '.npm')];
      
      // Run n8n installation script
      const installProcess = spawn('npm', npmCmd, {
        detached: false  // Keep attached to control the output
      });
      
      let output = '';
      installProcess.stdout.on('data', (data) => {
        const chunk = data.toString();
        output += chunk;
      });
      
      let errorOutput = '';
      installProcess.stderr.on('data', (data) => {
        const chunk = data.toString();
        errorOutput += chunk;
        // Some npm warnings come on stderr but aren't errors
        if (!chunk.includes('WARN')) {
          output += chunk;
        }
      });
      
      installProcess.on('close', (code) => {
        if (code === 0) {
          // If installed locally, add to PATH
          if (!installGlobally) {
            // Add hint for adding to PATH
            output += '\nn8n installed locally. Add to your PATH: export PATH="$HOME/.npm/bin:$PATH"';
          }
          
          res.json({ 
            success: true, 
            message: 'n8n installed successfully',
            global: installGlobally,
            output
          });
        } else {
          res.status(500).json({ 
            error: 'Failed to install n8n', 
            output, 
            errorOutput,
            code
          });
        }
      });
    } catch (error) {
      console.error('n8n installation error:', error);
      res.status(500).json({ 
        error: 'Failed to install n8n',
        message: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  });
  
  // Serve React app for all other routes in setup mode
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/build/index.html'));
  });
  
  // Start server immediately in setup mode without MongoDB
  app.listen(PORT, () => {
    console.log(`Setup server running on port ${PORT}`);
    console.log('Running in setup mode - database connection skipped');
  });
} else {
  // Normal mode - connect to MongoDB and use auth
  // Use authentication middleware for API routes in normal mode
  app.use('/api', authMiddleware);
  
  // API routes
  app.use('/api', routes);
  
  // Serve React app for all other routes
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/build/index.html'));
  });
  
  // Error handling middleware
  app.use(errorHandler);

  // Connect to MongoDB and start server
  const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/n8n-agent-hub';
  
  mongoose
    .connect(MONGODB_URI)
    .then(() => {
      console.log('Connected to MongoDB');
      app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
      });
    })
    .catch((error) => {
      console.error('MongoDB connection error:', error);
      console.error('If MongoDB is not needed, restart with --setup or setup-server flag');
      process.exit(1);
    });
}

export default app; 