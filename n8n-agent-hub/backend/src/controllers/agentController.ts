import { Request, Response, NextFunction } from 'express';
import Agent from '../models/Agent';
import User from '../models/User';
import n8nService from '../services/n8nService';
import { AuthRequest } from '../middleware/auth';
import mongoose from 'mongoose';
import { ApiError } from '../middleware/errorHandler';

// Get all agents for the authenticated user
export const getAgents = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const agents = await Agent.find({ ownerId: req.user.id });
    res.status(200).json({
      success: true,
      data: agents
    });
  } catch (error) {
    next(error);
  }
};

// Get a single agent by ID
export const getAgentById = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    res.status(200).json({
      success: true,
      data: agent
    });
  } catch (error) {
    next(error);
  }
};

// Create a new agent
export const createAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const { name, description, type, model, prompt, tools, memory } = req.body;
    
    // Check user subscription limits
    const user = await User.findById(req.user.id);
    if (!user) {
      const error: ApiError = new Error('User not found');
      error.statusCode = 404;
      return next(error);
    }
    
    const agentCount = await Agent.countDocuments({ ownerId: req.user.id });
    const maxAgents = user.subscription.features.maxAgents;
    
    if (agentCount >= maxAgents) {
      const error: ApiError = new Error(`Maximum number of agents (${maxAgents}) reached. Please upgrade your subscription.`);
      error.statusCode = 403;
      return next(error);
    }
    
    // Create workflow in n8n
    const workflow = await n8nService.createAgentWorkflow(
      name,
      description,
      type,
      model,
      prompt,
      tools,
      memory
    );
    
    // Create agent in database
    const agent = await Agent.create({
      name,
      description,
      ownerId: new mongoose.Types.ObjectId(req.user.id),
      n8nWorkflowId: workflow.id,
      type,
      configuration: {
        prompt,
        model,
        tools: tools || [],
        memory: memory !== undefined ? memory : true,
        customVariables: {}
      },
      status: 'inactive'
    });
    
    res.status(201).json({
      success: true,
      data: agent
    });
  } catch (error: any) {
    // Check for duplicate agent name
    if (error.code === 11000) {
      const err: ApiError = new Error('Agent with this name already exists');
      err.statusCode = 400;
      return next(err);
    }
    next(error);
  }
};

// Update an existing agent
export const updateAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const { name, description, type, prompt, model, tools, memory, customVariables } = req.body;
    
    // Find the agent
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    // Update the agent in the database
    const updatedAgent = await Agent.findByIdAndUpdate(
      req.params.id,
      {
        name: name || agent.name,
        description: description || agent.description,
        type: type || agent.type,
        configuration: {
          prompt: prompt || agent.configuration.prompt,
          model: model || agent.configuration.model,
          tools: tools || agent.configuration.tools,
          memory: memory !== undefined ? memory : agent.configuration.memory,
          customVariables: customVariables || agent.configuration.customVariables
        }
      },
      { new: true, runValidators: true }
    );
    
    // Update the workflow in n8n
    // This would be more complex in a real implementation
    // For now, we'll just update the basic workflow details
    await n8nService.updateWorkflow(agent.n8nWorkflowId, {
      name: name || agent.name,
      // Other workflow updates would go here
    });
    
    res.status(200).json({
      success: true,
      data: updatedAgent
    });
  } catch (error) {
    next(error);
  }
};

// Delete an agent
export const deleteAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    // Find the agent
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    // Delete the workflow in n8n
    await n8nService.deleteWorkflow(agent.n8nWorkflowId);
    
    // Delete the agent from the database
    await Agent.findByIdAndDelete(req.params.id);
    
    res.status(200).json({
      success: true,
      data: {}
    });
  } catch (error) {
    next(error);
  }
};

// Activate an agent
export const activateAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    // Find the agent
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    // Activate the workflow in n8n
    await n8nService.activateWorkflow(agent.n8nWorkflowId);
    
    // Update the agent status in the database
    const updatedAgent = await Agent.findByIdAndUpdate(
      req.params.id,
      { status: 'active' },
      { new: true }
    );
    
    res.status(200).json({
      success: true,
      data: updatedAgent
    });
  } catch (error) {
    next(error);
  }
};

// Deactivate an agent
export const deactivateAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    // Find the agent
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    // Deactivate the workflow in n8n
    await n8nService.deactivateWorkflow(agent.n8nWorkflowId);
    
    // Update the agent status in the database
    const updatedAgent = await Agent.findByIdAndUpdate(
      req.params.id,
      { status: 'inactive' },
      { new: true }
    );
    
    res.status(200).json({
      success: true,
      data: updatedAgent
    });
  } catch (error) {
    next(error);
  }
};

// Execute an agent directly
export const executeAgent = async (req: AuthRequest, res: Response, next: NextFunction) => {
  try {
    if (!req.user) {
      throw new Error('User not authenticated');
    }
    
    const { input } = req.body;
    
    // Find the agent
    const agent = await Agent.findOne({
      _id: req.params.id,
      ownerId: req.user.id
    });
    
    if (!agent) {
      const error: ApiError = new Error('Agent not found');
      error.statusCode = 404;
      return next(error);
    }
    
    // For direct execution, we'd need to trigger the n8n workflow
    // This is a simplified implementation
    // In a real application, you'd make a proper API call to the workflow
    const result = `Response from agent: ${agent.name} - This is a simulated response. In a real implementation, this would call the agent's n8n workflow with the input: ${input}`;
    
    // Update agent stats
    await Agent.findByIdAndUpdate(req.params.id, {
      $inc: { 'stats.executionsCount': 1 },
      $set: { 'stats.lastExecution': new Date() }
    });
    
    res.status(200).json({
      success: true,
      data: {
        result
      }
    });
  } catch (error) {
    next(error);
  }
}; 