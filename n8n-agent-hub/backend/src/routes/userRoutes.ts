import { Router } from 'express';
import {
  getUserProfile,
  updateUserProfile,
  updateUserSubscription,
  getAllUsers
} from '../controllers/userController';
import { authenticateJWT, authorizeRoles } from '../middleware/auth';

const router = Router();

// GET /api/users/profile - Get user profile
router.get('/profile', authenticateJWT, getUserProfile);

// PUT /api/users/profile - Update user profile
router.put('/profile', authenticateJWT, updateUserProfile);

// PUT /api/users/subscription - Update user subscription (admin only)
router.put('/subscription', authenticateJWT, authorizeRoles('admin'), updateUserSubscription);

// GET /api/users - Get all users (admin only)
router.get('/', authenticateJWT, authorizeRoles('admin'), getAllUsers);

export default router; 