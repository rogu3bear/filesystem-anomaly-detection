import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import User from '../models/User';
import { ApiError } from '../middleware/errorHandler';

// Register a new user
export const register = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { name, email, password } = req.body;
    
    // Check if user already exists
    const userExists = await User.findOne({ email });
    if (userExists) {
      const error: ApiError = new Error('User with this email already exists');
      error.statusCode = 400;
      return next(error);
    }
    
    // Create new user with free tier subscription
    const user = await User.create({
      name,
      email,
      password,
      role: 'user',
      subscription: {
        plan: 'free',
        features: {
          maxAgents: 3,
          customModels: false,
          advancedAnalytics: false
        }
      }
    });
    
    // Generate JWT token
    const token = generateToken(user._id.toString(), user.email, user.role);
    
    // Send response
    res.status(201).json({
      success: true,
      data: {
        token,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role,
          subscription: user.subscription
        }
      }
    });
  } catch (error) {
    next(error);
  }
};

// Login user
export const login = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { email, password } = req.body;
    
    // Check if user exists
    const user = await User.findOne({ email });
    if (!user) {
      const error: ApiError = new Error('Invalid credentials');
      error.statusCode = 401;
      return next(error);
    }
    
    // Check if password is correct
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      const error: ApiError = new Error('Invalid credentials');
      error.statusCode = 401;
      return next(error);
    }
    
    // Generate JWT token
    const token = generateToken(user._id.toString(), user.email, user.role);
    
    // Send response
    res.status(200).json({
      success: true,
      data: {
        token,
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          role: user.role,
          subscription: user.subscription
        }
      }
    });
  } catch (error) {
    next(error);
  }
};

// Get current user
export const getCurrentUser = async (req: Request, res: Response, next: NextFunction) => {
  try {
    // The user object is attached by the auth middleware
    const user = await User.findById((req as any).user.id).select('-password');
    
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

// Update API keys
export const updateApiKeys = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { openai, google, anthropic, other } = req.body;
    
    // Update user API keys
    const user = await User.findByIdAndUpdate(
      (req as any).user.id,
      {
        apiKeys: {
          openai,
          google,
          anthropic,
          other
        }
      },
      { new: true }
    ).select('-password');
    
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

// Helper function to generate JWT token
const generateToken = (id: string, email: string, role: string): string => {
  const jwtSecret = process.env.JWT_SECRET || 'your-secret-key';
  return jwt.sign({ id, email, role }, jwtSecret, {
    expiresIn: '30d'
  });
}; 