import { Router } from 'express';
import {
  register,
  login,
  getCurrentUser,
  updateApiKeys
} from '../controllers/authController';
import { authenticateJWT } from '../middleware/auth';

const router = Router();

// POST /api/auth/register - Register a new user
router.post('/register', register);

// POST /api/auth/login - Login user
router.post('/login', login);

// GET /api/auth/me - Get current user profile (protected)
router.get('/me', authenticateJWT, getCurrentUser);

// PUT /api/auth/api-keys - Update user API keys (protected)
router.put('/api-keys', authenticateJWT, updateApiKeys);

export default router; 