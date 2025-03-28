import { Router } from 'express';
import {
  getAgents,
  getAgentById,
  createAgent,
  updateAgent,
  deleteAgent,
  activateAgent,
  deactivateAgent,
  executeAgent
} from '../controllers/agentController';

const router = Router();

// GET /api/agents - Get all agents for user
router.get('/', getAgents);

// GET /api/agents/:id - Get a single agent
router.get('/:id', getAgentById);

// POST /api/agents - Create a new agent
router.post('/', createAgent);

// PUT /api/agents/:id - Update an agent
router.put('/:id', updateAgent);

// DELETE /api/agents/:id - Delete an agent
router.delete('/:id', deleteAgent);

// POST /api/agents/:id/activate - Activate an agent
router.post('/:id/activate', activateAgent);

// POST /api/agents/:id/deactivate - Deactivate an agent
router.post('/:id/deactivate', deactivateAgent);

// POST /api/agents/:id/execute - Execute an agent directly
router.post('/:id/execute', executeAgent);

export default router; 