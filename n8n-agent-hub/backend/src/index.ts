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

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.static(path.join(__dirname, '../../frontend/build')));

// Check if n8n is running
const checkN8nStatus = async (): Promise<boolean> => {
  try {
    const response = await fetch('http://localhost:5678/healthz');
    return response.ok;
  } catch (error) {
    return false;
  }
};

// Setup mode endpoints
if (isSetupMode) {
  app.get('/api/setup/status', async (req, res) => {
    try {
      const n8nRunning = await checkN8nStatus();
      const configExists = fs.existsSync(path.join(process.env.HOME || '', '.config/file_anomaly_detection/config.json'));
      
      res.json({
        n8nInstalled: fs.existsSync('/usr/local/bin/n8n') || fs.existsSync('/usr/bin/n8n'),
        n8nRunning,
        configExists,
        systemInfo: {
          platform: process.platform,
          release: process.release,
          nodeVersion: process.version
        }
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to get setup status' });
    }
  });

  app.post('/api/setup/configure', async (req, res) => {
    try {
      const { sourceDir, targetDir, organizeBy, scanInterval } = req.body;
      
      // Create config directory if it doesn't exist
      const configDir = path.join(process.env.HOME || '', '.config/file_anomaly_detection');
      if (!fs.existsSync(configDir)) {
        fs.mkdirSync(configDir, { recursive: true });
      }
      
      // Generate API key if not provided
      const apiKey = req.body.apiKey || require('crypto').randomBytes(24).toString('hex');
      
      // Write config file
      const config = {
        source_directory: sourceDir || path.join(process.env.HOME || '', 'Downloads'),
        target_directory: targetDir || path.join(process.env.HOME || '', 'Organized'),
        organize_by: organizeBy || 'extension',
        scan_interval: scanInterval || 300,
        api_key: apiKey
      };
      
      fs.writeFileSync(
        path.join(configDir, 'config.json'),
        JSON.stringify(config, null, 2)
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
        apiKey
      });
    } catch (error) {
      console.error('Configuration error:', error);
      res.status(500).json({ error: 'Failed to save configuration' });
    }
  });

  app.post('/api/setup/start-n8n', async (req, res) => {
    try {
      // Check if n8n is already running
      const n8nRunning = await checkN8nStatus();
      
      if (n8nRunning) {
        return res.json({ success: true, message: 'n8n is already running' });
      }
      
      // Start n8n
      const n8nProcess = spawn('n8n', ['start'], {
        detached: true,
        stdio: 'ignore'
      });
      
      // Detach the process so it continues running after this process exits
      n8nProcess.unref();
      
      res.json({ success: true, message: 'n8n started successfully' });
    } catch (error) {
      console.error('n8n start error:', error);
      res.status(500).json({ error: 'Failed to start n8n' });
    }
  });

  app.post('/api/setup/install-n8n', async (req, res) => {
    try {
      // Run n8n installation script
      const installProcess = spawn('npm', ['install', 'n8n', '-g'], {
        detached: true
      });
      
      let output = '';
      installProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      let errorOutput = '';
      installProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      installProcess.on('close', (code) => {
        if (code === 0) {
          res.json({ 
            success: true, 
            message: 'n8n installed successfully',
            output
          });
        } else {
          res.status(500).json({ 
            error: 'Failed to install n8n', 
            output, 
            errorOutput 
          });
        }
      });
    } catch (error) {
      console.error('n8n installation error:', error);
      res.status(500).json({ error: 'Failed to install n8n' });
    }
  });
  
  // Serve React app for all other routes in setup mode
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/build/index.html'));
  });
} else {
  // Use authentication middleware for API routes in normal mode
  app.use('/api', authMiddleware);
  
  // API routes
  app.use('/api', routes);
  
  // Serve React app for all other routes
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../../frontend/build/index.html'));
  });
}

// Error handling middleware
app.use(errorHandler);

// Connect to MongoDB and start server
mongoose
  .connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/n8n-agent-hub')
  .then(() => {
    console.log('Connected to MongoDB');
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
      if (isSetupMode) {
        console.log('Running in setup mode');
      }
    });
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error);
    process.exit(1);
  });

export default app; 