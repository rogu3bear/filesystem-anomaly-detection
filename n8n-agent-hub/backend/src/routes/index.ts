import express from 'express';
import agentRoutes from './agentRoutes';
import userRoutes from './userRoutes';
import authRoutes from './authRoutes';
import { processMessage, organizeFiles, searchFiles } from '../controllers/aiConversationController';
import { executeCommand, isGitHubCLIAvailable } from '../utils/fileUtils';

const router = express.Router();

// Public routes
router.use('/auth', authRoutes);

// Protected routes
router.use('/agents', agentRoutes);
router.use('/users', userRoutes);

// AI Conversation routes
router.post('/conversation', processMessage);
router.post('/organize', organizeFiles);
router.post('/search', searchFiles);

// GitHub integration (using gh CLI)
router.post('/github/push', async (req, res) => {
  try {
    const { repoName, branch, message } = req.body;
    
    if (!repoName) {
      return res.status(400).json({ success: false, message: 'Repository name is required' });
    }
    
    // Check if GitHub CLI is available
    const ghAvailable = await isGitHubCLIAvailable();
    if (!ghAvailable) {
      return res.status(400).json({ 
        success: false, 
        message: 'GitHub CLI (gh) is not available. Please install it first.' 
      });
    }
    
    // Create and push to repository
    try {
      // Check if repo exists
      const repoExists = await executeCommand(`gh repo view ${repoName} --json name 2>/dev/null`);
      
      if (!repoExists || repoExists.includes('not found')) {
        // Create repo if it doesn't exist
        await executeCommand(`gh repo create ${repoName} --public --source=. --remote=origin`);
      }
      
      // Add files
      await executeCommand('git add .');
      
      // Commit
      const commitMessage = message || 'Update files via File Organizer AI';
      await executeCommand(`git commit -m "${commitMessage}"`);
      
      // Push to specified branch or default
      const pushBranch = branch || 'main';
      await executeCommand(`git push origin ${pushBranch}`);
      
      res.json({ 
        success: true, 
        message: `Successfully pushed to ${repoName}` 
      });
    } catch (error) {
      console.error('GitHub operation error:', error);
      res.status(500).json({ 
        success: false, 
        message: 'Failed to push to GitHub',
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  } catch (error) {
    console.error('GitHub integration error:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error in GitHub integration',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

// Health check route
router.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

export default router; 