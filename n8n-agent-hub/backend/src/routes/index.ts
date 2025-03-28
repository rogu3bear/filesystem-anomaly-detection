import { Router } from 'express';
import agentRoutes from './agentRoutes';
import userRoutes from './userRoutes';
import authRoutes from './authRoutes';
import { authenticateJWT } from '../middleware/auth';

const router = Router();

// Public routes
router.use('/auth', authRoutes);

// Protected routes
router.use('/agents', authenticateJWT, agentRoutes);
router.use('/users', authenticateJWT, userRoutes);

// Health check route
router.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok', timestamp: new Date().toISOString() });
});

export default router; 