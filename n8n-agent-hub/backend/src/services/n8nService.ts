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

  async executeWorkflow(id: string, data: any): Promise<any> {
    try {
      // Execute the workflow with the provided data
      const result = await this.request('POST', `workflows/${id}/execute`, {
        data: {
          input: data
        }
      });

      return result;
    } catch (error: any) {
      console.error(`Error executing workflow ${id}:`, error.message);
      throw new Error(`Failed to execute workflow: ${error.message}`);
    }
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
      const toolNodeMapping: Record<string, any> = {
        'file_explorer': {
          id: 'n8n-nodes-langchain.toolCode',
          type: 'n8n-nodes-langchain.toolCode',
          name: 'File Explorer Tool',
          parameters: {
            name: 'file_explorer',
            description: 'Explore and search files in the filesystem',
            code: `const fs = require('fs');
const path = require('path');

// File exploration functionality
return {
  list: (dir) => fs.readdirSync(dir),
  read: (file) => fs.readFileSync(file, 'utf8'),
  exists: (path) => fs.existsSync(path)
};`
          }
        },
        'database_query': {
          id: 'n8n-nodes-langchain.toolCode',
          type: 'n8n-nodes-langchain.toolCode',
          name: 'Database Query Tool',
          parameters: {
            name: 'database_query',
            description: 'Execute database queries and retrieve data',
            code: `// Database query functionality
// Connect to configured database and execute queries
return { query: (sql) => ({ message: 'Query execution placeholder' }) };`
          }
        },
        'web_request': {
          id: 'n8n-nodes-langchain.toolHttpRequest',
          type: 'n8n-nodes-langchain.toolHttpRequest',
          name: 'Web Request Tool',
          parameters: {
            name: 'web_request',
            description: 'Make HTTP requests to external APIs',
            authentication: 'none'
          }
        },
        'image_processing': {
          id: 'n8n-nodes-langchain.toolCode',
          type: 'n8n-nodes-langchain.toolCode',
          name: 'Image Processing Tool',
          parameters: {
            name: 'image_processing',
            description: 'Process and analyze images',
            code: `// Image processing functionality
return { analyze: (imagePath) => ({ message: 'Image analysis placeholder' }) };`
          }
        },
        'data_transformation': {
          id: 'n8n-nodes-langchain.toolCode',
          type: 'n8n-nodes-langchain.toolCode',
          name: 'Data Transformation Tool',
          parameters: {
            name: 'data_transformation',
            description: 'Transform and manipulate data structures',
            code: `// Data transformation functionality
return {
  transform: (data, format) => data,
  convert: (data, to) => data
};`
          }
        }
      };

      let xPosition = 700;
      const yPosition = 300;
      const toolConnections: any[] = [];

      tools.forEach((toolName, index) => {
        const toolTemplate = toolNodeMapping[toolName];
        if (toolTemplate) {
          const toolNode = {
            ...toolTemplate,
            typeVersion: 1,
            position: [xPosition, yPosition + (index * 100)]
          };

          workflowTemplate.nodes.push(toolNode);
          toolConnections.push({
            node: toolTemplate.name,
            type: 'ai_tool',
            index: 0
          });

          xPosition += 250;
        }
      });

      // Connect tools to AI Agent
      if (toolConnections.length > 0) {
        workflowTemplate.connections['AI Agent'] = {
          ...workflowTemplate.connections['AI Agent'],
          tools: [toolConnections]
        };
      }
    }

    return this.createWorkflow(workflowTemplate);
  }

  // Update agent workflow with new configuration
  async updateAgentWorkflow(
    workflowId: string,
    name?: string,
    prompt?: string,
    model?: string,
    tools?: string[],
    memory?: boolean,
    customVariables?: Record<string, string>
  ): Promise<N8nWorkflow> {
    // Get the current workflow
    const currentWorkflow = await this.getWorkflow(workflowId);

    // Update workflow name if provided
    if (name) {
      currentWorkflow.name = name;
    }

    // Update AI Agent node parameters
    const agentNode = currentWorkflow.nodes.find(node => node.type === 'n8n-nodes-langchain.agent');
    if (agentNode) {
      if (prompt !== undefined) {
        agentNode.parameters.options = agentNode.parameters.options || {};
        agentNode.parameters.options.prompt = prompt;
      }
      if (memory !== undefined) {
        agentNode.parameters.options = agentNode.parameters.options || {};
        agentNode.parameters.options.memory = memory;
      }
    }

    // Update Chat Model node parameters
    const modelNode = currentWorkflow.nodes.find(node => node.type === 'n8n-nodes-langchain.chatModel');
    if (modelNode && model !== undefined) {
      modelNode.parameters.modelType = model.includes('openai') ? 'openAI' :
                                       model.includes('google') ? 'googlePaLM' :
                                       model.includes('anthropic') ? 'anthropic' : 'openAI';
      modelNode.parameters.options = modelNode.parameters.options || {};
      modelNode.parameters.options.model = model;
    }

    // Handle tool updates if provided
    if (tools !== undefined) {
      // Remove existing tool nodes
      currentWorkflow.nodes = currentWorkflow.nodes.filter(node =>
        !node.type.includes('tool') ||
        node.type === 'n8n-nodes-langchain.agent'
      );

      // Remove tool connections from AI Agent
      if (currentWorkflow.connections['AI Agent']) {
        delete currentWorkflow.connections['AI Agent'].tools;
      }

      // Add new tool nodes using the same logic as createAgentWorkflow
      if (tools.length > 0) {
        const toolNodeMapping: Record<string, any> = {
          'file_explorer': {
            id: 'n8n-nodes-langchain.toolCode',
            type: 'n8n-nodes-langchain.toolCode',
            name: 'File Explorer Tool',
            parameters: {
              name: 'file_explorer',
              description: 'Explore and search files in the filesystem',
              code: `const fs = require('fs');
const path = require('path');

// File exploration functionality
return {
  list: (dir) => fs.readdirSync(dir),
  read: (file) => fs.readFileSync(file, 'utf8'),
  exists: (path) => fs.existsSync(path)
};`
            }
          },
          'database_query': {
            id: 'n8n-nodes-langchain.toolCode',
            type: 'n8n-nodes-langchain.toolCode',
            name: 'Database Query Tool',
            parameters: {
              name: 'database_query',
              description: 'Execute database queries and retrieve data',
              code: `// Database query functionality
// Connect to configured database and execute queries
return { query: (sql) => ({ message: 'Query execution placeholder' }) };`
            }
          },
          'web_request': {
            id: 'n8n-nodes-langchain.toolHttpRequest',
            type: 'n8n-nodes-langchain.toolHttpRequest',
            name: 'Web Request Tool',
            parameters: {
              name: 'web_request',
              description: 'Make HTTP requests to external APIs',
              authentication: 'none'
            }
          },
          'image_processing': {
            id: 'n8n-nodes-langchain.toolCode',
            type: 'n8n-nodes-langchain.toolCode',
            name: 'Image Processing Tool',
            parameters: {
              name: 'image_processing',
              description: 'Process and analyze images',
              code: `// Image processing functionality
return { analyze: (imagePath) => ({ message: 'Image analysis placeholder' }) };`
            }
          },
          'data_transformation': {
            id: 'n8n-nodes-langchain.toolCode',
            type: 'n8n-nodes-langchain.toolCode',
            name: 'Data Transformation Tool',
            parameters: {
              name: 'data_transformation',
              description: 'Transform and manipulate data structures',
              code: `// Data transformation functionality
return {
  transform: (data, format) => data,
  convert: (data, to) => data
};`
            }
          }
        };

        let xPosition = 700;
        const yPosition = 300;
        const toolConnections: any[] = [];

        tools.forEach((toolName, index) => {
          const toolTemplate = toolNodeMapping[toolName];
          if (toolTemplate) {
            const toolNode = {
              ...toolTemplate,
              typeVersion: 1,
              position: [xPosition, yPosition + (index * 100)]
            };

            currentWorkflow.nodes.push(toolNode);
            toolConnections.push({
              node: toolTemplate.name,
              type: 'ai_tool',
              index: 0
            });

            xPosition += 250;
          }
        });

        // Connect tools to AI Agent
        if (toolConnections.length > 0 && currentWorkflow.connections['AI Agent']) {
          currentWorkflow.connections['AI Agent'].tools = [toolConnections];
        }
      }

      // Update workflow tags with new tools
      currentWorkflow.tags = ['agent', ...(currentWorkflow.tags || []).filter(t => !['file_explorer', 'database_query', 'web_request', 'image_processing', 'data_transformation'].includes(t)), ...tools];
    }

    // Apply custom variables if provided (these would be used in workflow settings)
    if (customVariables) {
      currentWorkflow.settings = currentWorkflow.settings || {};
      currentWorkflow.settings.customVariables = customVariables;
    }

    // Update the workflow in n8n
    return this.updateWorkflow(workflowId, currentWorkflow);
  }
}

export default new N8nService(); 