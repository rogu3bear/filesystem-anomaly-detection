import mongoose, { Document, Schema } from 'mongoose';

export interface IAgent extends Document {
  name: string;
  description: string;
  ownerId: mongoose.Types.ObjectId;
  n8nWorkflowId: string;
  status: 'active' | 'inactive' | 'error';
  type: 'tools' | 'conversational' | 'openai' | 'react' | 'sql' | 'plan-and-execute';
  configuration: {
    prompt: string;
    model: string;
    tools: string[];
    memory: boolean;
    customVariables: Record<string, string>;
  };
  stats: {
    executionsCount: number;
    lastExecution: Date;
    averageExecutionTime: number;
    successRate: number;
  };
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

const AgentSchema = new Schema<IAgent>(
  {
    name: {
      type: String,
      required: true,
      trim: true
    },
    description: {
      type: String,
      required: true
    },
    ownerId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true
    },
    n8nWorkflowId: {
      type: String,
      required: true
    },
    status: {
      type: String,
      enum: ['active', 'inactive', 'error'],
      default: 'inactive'
    },
    type: {
      type: String,
      enum: ['tools', 'conversational', 'openai', 'react', 'sql', 'plan-and-execute'],
      default: 'tools'
    },
    configuration: {
      prompt: {
        type: String,
        required: true
      },
      model: {
        type: String,
        required: true
      },
      tools: {
        type: [String],
        default: []
      },
      memory: {
        type: Boolean,
        default: true
      },
      customVariables: {
        type: Map,
        of: String,
        default: {}
      }
    },
    stats: {
      executionsCount: {
        type: Number,
        default: 0
      },
      lastExecution: Date,
      averageExecutionTime: {
        type: Number,
        default: 0
      },
      successRate: {
        type: Number,
        default: 100
      }
    },
    tags: {
      type: [String],
      default: []
    }
  },
  { timestamps: true }
);

// Create compound index for ownerId and name
AgentSchema.index({ ownerId: 1, name: 1 }, { unique: true });

export default mongoose.model<IAgent>('Agent', AgentSchema); 