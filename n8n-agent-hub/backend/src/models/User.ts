import mongoose, { Document, Schema } from 'mongoose';
import bcrypt from 'bcryptjs';

export interface IUser extends Document {
  email: string;
  password: string;
  name: string;
  role: 'admin' | 'user';
  apiKeys: {
    openai?: string;
    google?: string;
    anthropic?: string;
    other?: Record<string, string>;
  };
  subscription: {
    plan: 'free' | 'premium' | 'enterprise';
    validUntil?: Date;
    features: {
      maxAgents: number;
      customModels: boolean;
      advancedAnalytics: boolean;
    };
  };
  createdAt: Date;
  updatedAt: Date;
  comparePassword(candidatePassword: string): Promise<boolean>;
}

const UserSchema = new Schema<IUser>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      lowercase: true
    },
    password: {
      type: String,
      required: true,
      minlength: 8
    },
    name: {
      type: String,
      required: true
    },
    role: {
      type: String,
      enum: ['admin', 'user'],
      default: 'user'
    },
    apiKeys: {
      openai: String,
      google: String,
      anthropic: String,
      other: {
        type: Map,
        of: String
      }
    },
    subscription: {
      plan: {
        type: String,
        enum: ['free', 'premium', 'enterprise'],
        default: 'free'
      },
      validUntil: Date,
      features: {
        maxAgents: {
          type: Number,
          default: 3
        },
        customModels: {
          type: Boolean,
          default: false
        },
        advancedAnalytics: {
          type: Boolean,
          default: false
        }
      }
    }
  },
  { timestamps: true }
);

// Hash password before saving
UserSchema.pre('save', async function (next) {
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error as Error);
  }
});

// Method to compare passwords
UserSchema.methods.comparePassword = async function (candidatePassword: string): Promise<boolean> {
  return bcrypt.compare(candidatePassword, this.password);
};

export default mongoose.model<IUser>('User', UserSchema); 