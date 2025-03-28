import axios from 'axios';

export interface N8nWorkflow {
  id: string;
  name: string;
  active: boolean;
  nodes: any[];
  connections: any;
  settings?: any;
  tags?: string[];
}

export interface N8nCredential {
  id: string;
  name: string;
  type: string;
  data: any;
}

class N8nService {
  private baseUrl: string;
  private username: string;
  private password: string;
  private authToken?: string;

  constructor() {
    this.baseUrl = process.env.N8N_API_BASE_URL || 'http://n8n:5678/api/';
    this.username = process.env.N8N_API_USER || 'admin';
    this.password = process.env.N8N_API_PASS || 'admin';
  }

  private async getAuthToken(): Promise<string> {
    if (this.authToken) {
      return this.authToken;
    }

    try {
      const response = await axios.post(`${this.baseUrl}login`, {
        email: this.username,
        password: this.password
      });

      this.authToken = response.data.token;
      return this.authToken;
    } catch (error) {
      console.error('Failed to authenticate with n8n API:', error);
      throw new Error('Failed to authenticate with n8n API');
    }
  }

  private async request(method: string, endpoint: string, data?: any) {
    try {
      const token = await this.getAuthToken();
      const url = `${this.baseUrl}${endpoint}`;
      
      const response = await axios({
        method,
        url,
        data,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      return response.data;
    } catch (error: any) {
      console.error(`Error in n8n API request to ${endpoint}:`, error.response?.data || error.message);
      throw new Error(`n8n API error: ${error.response?.data?.message || error.message}`);
    }
  }

  // Workflow management
  async getWorkflows(): Promise<N8nWorkflow[]> {
    return this.request('GET', 'workflows');
  }

  async getWorkflow(id: string): Promise<N8nWorkflow> {
    return this.request('GET', `workflows/${id}`);
  }

  async createWorkflow(workflow: Partial<N8nWorkflow>): Promise<N8nWorkflow> {
    return this.request('POST', 'workflows', workflow);
  }

  async updateWorkflow(id: string, workflow: Partial<N8nWorkflow>): Promise<N8nWorkflow> {
    return this.request('PUT', `workflows/${id}`, workflow);
  }

  async deleteWorkflow(id: string): Promise<void> {
    return this.request('DELETE', `workflows/${id}`);
  }

  async activateWorkflow(id: string): Promise<N8nWorkflow> {
    return this.request('POST', `workflows/${id}/activate`);
  }

  async deactivateWorkflow(id: string): Promise<N8nWorkflow> {
    return this.request('POST', `workflows/${id}/deactivate`);
  }

  // Credentials management
  async getCredentials(): Promise<N8nCredential[]> {
    return this.request('GET', 'credentials');
  }

  async createCredential(type: string, name: string, data: any): Promise<N8nCredential> {
    return this.request('POST', 'credentials', {
      name,
      type,
      data
    });
  }

  async deleteCredential(id: string): Promise<void> {
    return this.request('DELETE', `credentials/${id}`);
  }

  // Create an agent workflow from a template
  async createAgentWorkflow(
    name: string,
    description: string,
    agentType: string,
    model: string,
    prompt: string,
    tools: string[] = [],
    memory: boolean = true
  ): Promise<N8nWorkflow> {
    // Basic workflow template with required nodes
    const workflowTemplate = {
      name,
      nodes: [
        {
          id: 'n8n-nodes-base.webhook',
          parameters: {
            path: `agents/${name.toLowerCase().replace(/\s+/g, '-')}`,
            responseMode: 'lastNode',
            options: {}
          },
          name: 'Webhook',
          type: 'n8n-nodes-base.webhook',
          typeVersion: 1,
          position: [250, 300]
        },
        {
          id: 'n8n-nodes-langchain.agent',
          parameters: {
            agentType,
            options: {
              prompt: prompt,
              memory: memory,
            }
          },
          name: 'AI Agent',
          type: 'n8n-nodes-langchain.agent',
          typeVersion: 1,
          position: [500, 300]
        },
        {
          id: 'n8n-nodes-langchain.chatModel',
          parameters: {
            modelType: model.includes('openai') ? 'openAI' : 
                       model.includes('google') ? 'googlePaLM' : 
                       model.includes('anthropic') ? 'anthropic' : 'openAI',
            options: {
              model: model
            }
          },
          name: 'Chat Model',
          type: 'n8n-nodes-langchain.chatModel',
          typeVersion: 1,
          position: [500, 500]
        }
      ],
      connections: {
        Webhook: {
          main: [
            [
              {
                node: 'AI Agent',
                type: 'main',
                index: 0
              }
            ]
          ]
        },
        'AI Agent': {
          model: [
            [
              {
                node: 'Chat Model',
                type: 'main',
                index: 0
              }
            ]
          ]
        }
      },
      settings: {
        saveExecutionProgress: true,
        saveManualExecutions: true,
        saveDataErrorExecution: 'all',
        saveDataSuccessExecution: 'all'
      },
      tags: ['agent', agentType, ...tools]
    };

    // Add tool nodes if needed based on the tool names
    if (tools.length > 0) {
      // Logic to add tool nodes to the workflow
      // This would be more complex in a real implementation
      // For each tool, add the appropriate node and connection
    }

    return this.createWorkflow(workflowTemplate);
  }
}

export default new N8nService(); 