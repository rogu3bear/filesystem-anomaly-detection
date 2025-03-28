import { Request, Response, NextFunction } from 'express';
import User from '../models/User';
import { ApiError } from '../middleware/errorHandler';
import { AuthRequest } from '../middleware/auth';

// Get user profile
export const getUserProfile = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const user = await User.findById(req.user.id).select('-password');
    
    if (!user) {
      const error: ApiError = new Error('User not found');
      error.statusCode = 404;
      return next(error);
    }
    
    res.status(200).json({
      success: true,
      data: user
    });
  } catch (error) {
    next(error);
  }
};

// Update user profile
export const updateUserProfile = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const { name, email } = req.body;
    
    // Check if email is being changed and if it's already in use
    if (email) {
      const existingUser = await User.findOne({ email });
      if (existingUser && existingUser._id.toString() !== req.user.id) {
        const error: ApiError = new Error('Email already in use');
        error.statusCode = 400;
        return next(error);
      }
    }
    
    const updatedUser = await User.findByIdAndUpdate(
      req.user.id,
      {
        name: name || undefined,
        email: email || undefined
      },
      {
        new: true,
        runValidators: true
      }
    ).select('-password');
    
    if (!updatedUser) {
      const error: ApiError = new Error('User not found');
      error.statusCode = 404;
      return next(error);
    }
    
    res.status(200).json({
      success: true,
      data: updatedUser
    });
  } catch (error) {
    next(error);
  }
};

// Update user subscription (admin only)
export const updateUserSubscription = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    if (req.user.role !== 'admin') {
      const error: ApiError = new Error('Not authorized to access this resource');
      error.statusCode = 403;
      return next(error);
    }
    
    const { userId, plan, validUntil, maxAgents, customModels, advancedAnalytics } = req.body;
    
    const user = await User.findById(userId);
    
    if (!user) {
      const error: ApiError = new Error('User not found');
      error.statusCode = 404;
      return next(error);
    }
    
    const updatedUser = await User.findByIdAndUpdate(
      userId,
      {
        subscription: {
          plan: plan || user.subscription.plan,
          validUntil: validUntil || user.subscription.validUntil,
          features: {
            maxAgents: maxAgents !== undefined ? maxAgents : user.subscription.features.maxAgents,
            customModels: customModels !== undefined ? customModels : user.subscription.features.customModels,
            advancedAnalytics: advancedAnalytics !== undefined ? advancedAnalytics : user.subscription.features.advancedAnalytics
          }
        }
      },
      {
        new: true,
        runValidators: true
      }
    ).select('-password');
    
    res.status(200).json({
      success: true,
      data: updatedUser
    });
  } catch (error) {
    next(error);
  }
};

// Get all users (admin only)
export const getAllUsers = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    if (req.user.role !== 'admin') {
      const error: ApiError = new Error('Not authorized to access this resource');
      error.statusCode = 403;
      return next(error);
    }
    
    const users = await User.find().select('-password');
    
    res.status(200).json({
      success: true,
      count: users.length,
      data: users
    });
  } catch (error) {
    next(error);
  }
}; 