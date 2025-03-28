import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { ApiError } from './errorHandler';

export interface AuthRequest extends Request {
  user?: {
    id: string;
    email: string;
    role: string;
  };
}

export const authenticateJWT = (
  req: AuthRequest,
  res: Response,
  next: NextFunction
) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    const error: ApiError = new Error('Authentication required');
    error.statusCode = 401;
    return next(error);
  }

  const token = authHeader.split(' ')[1];
  
  try {
    const jwtSecret = process.env.JWT_SECRET || 'your-secret-key';
    const decodedToken = jwt.verify(token, jwtSecret) as {
      id: string;
      email: string;
      role: string;
    };
    
    req.user = {
      id: decodedToken.id,
      email: decodedToken.email,
      role: decodedToken.role
    };
    
    next();
  } catch (error) {
    const err: ApiError = new Error('Invalid or expired token');
    err.statusCode = 401;
    next(err);
  }
};

export const authorizeRoles = (...roles: string[]) => {
  return (req: AuthRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      const error: ApiError = new Error('Authentication required');
      error.statusCode = 401;
      return next(error);
    }

    if (!roles.includes(req.user.role)) {
      const error: ApiError = new Error('Not authorized to access this resource');
      error.statusCode = 403;
      return next(error);
    }
    
    next();
  };
}; 