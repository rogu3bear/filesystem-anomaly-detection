import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, TextField, Button, Paper, Typography, 
  List, ListItem, Chip, IconButton, Divider 
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import FolderIcon from '@mui/icons-material/Folder';
import SearchIcon from '@mui/icons-material/Search';
import SettingsIcon from '@mui/icons-material/Settings';
import CircularProgress from '@mui/material/CircularProgress';
import { styled } from '@mui/material/styles';

const API_URL = process.env.REACT_APP_API_URL || '/api';

// Message types
interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  suggestedActions?: string[];
  context?: any;
  files?: any[];
}

// Styled components
const MessageContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(1.5),
  marginBottom: theme.spacing(1.5),
  maxWidth: '80%',
  borderRadius: 10,
}));

const UserMessage = styled(MessageContainer)(({ theme }) => ({
  marginLeft: 'auto',
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
}));

const AssistantMessage = styled(MessageContainer)(({ theme }) => ({
  marginRight: 'auto',
  backgroundColor: theme.palette.grey[100],
}));

const ActionButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(0.5),
  borderRadius: 20,
}));

// Main component
const ConversationUI: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationContext, setConversationContext] = useState<any>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Add welcome message when component mounts
  useEffect(() => {
    const welcomeMessage: Message = {
      id: `msg-${Date.now()}`,
      text: "Hi there! I'm your file organization assistant. I can help you organize files, search for specific items, or provide information about your storage. What can I help you with today?",
      sender: 'assistant',
      timestamp: new Date(),
      suggestedActions: ['Organize my Downloads', 'Find a file', 'Help me back up files']
    };
    
    setMessages([welcomeMessage]);
  }, []);
  
  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle sending a message
  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;
    
    // Add user message to the conversation
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);
    
    try {
      // Send to backend for processing
      const response = await fetch(`${API_URL}/conversation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: inputValue,
          context: conversationContext
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Update conversation context
        if (data.response.context) {
          setConversationContext({
            ...conversationContext,
            ...data.response.context
          });
        }
        
        // Add assistant response
        const assistantMessage: Message = {
          id: `msg-${Date.now()}`,
          text: data.response.responseText,
          sender: 'assistant',
          timestamp: new Date(),
          suggestedActions: data.response.suggestedActions,
          context: data.response.context
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // Handle action execution if needed
        if (data.response.intent === 'organize' && data.response.executeAction) {
          executeOrganizeAction(data.response.context);
        } else if (data.response.intent === 'search' && data.response.executeAction) {
          executeSearchAction(data.response.context);
        }
      } else {
        // Handle error
        const errorMessage: Message = {
          id: `msg-${Date.now()}`,
          text: "I'm sorry, I encountered an error processing your request. Please try again.",
          sender: 'assistant',
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        text: "I'm sorry, there was a problem connecting to the server. Please check your connection and try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle suggested action click
  const handleActionClick = (action: string) => {
    setInputValue(action);
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };
  
  // Execute organize action
  const executeOrganizeAction = async (context: any) => {
    try {
      setLoading(true);
      
      // Add a message to show we're organizing
      const processingMessage: Message = {
        id: `msg-${Date.now()}`,
        text: `Organizing files in ${context.directory}. This might take a moment...`,
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, processingMessage]);
      
      // Call organize endpoint
      const response = await fetch(`${API_URL}/organize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          source: context.directory 
        }),
      });
      
      const data = await response.json();
      
      // Add result message
      const resultMessage: Message = {
        id: `msg-${Date.now()}`,
        text: data.success 
          ? data.message 
          : "I encountered an error while organizing files. Please try again.",
        sender: 'assistant',
        timestamp: new Date(),
        files: data.success ? data.results.details : undefined
      };
      
      setMessages(prev => [...prev, resultMessage]);
    } catch (error) {
      console.error('Error organizing files:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        text: "I'm sorry, there was a problem organizing your files. Please try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
  // Execute search action
  const executeSearchAction = async (context: any) => {
    try {
      setLoading(true);
      
      // Add a message to show we're searching
      const searchingMessage: Message = {
        id: `msg-${Date.now()}`,
        text: `Searching for "${context.searchTerms}" in ${context.directory}...`,
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, searchingMessage]);
      
      // Call search endpoint
      const response = await fetch(`${API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: context.searchTerms,
          directory: context.directory,
          recursive: context.recursive || true
        }),
      });
      
      const data = await response.json();
      
      // Add result message
      const resultMessage: Message = {
        id: `msg-${Date.now()}`,
        text: data.success 
          ? `I found ${data.results.length} files matching "${context.searchTerms}".` 
          : "I couldn't find any files matching your search criteria.",
        sender: 'assistant',
        timestamp: new Date(),
        files: data.success ? data.results : undefined
      };
      
      setMessages(prev => [...prev, resultMessage]);
    } catch (error) {
      console.error('Error searching files:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: `msg-${Date.now()}`,
        text: "I'm sorry, there was a problem searching for files. Please try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle Enter key press
  const handleKeyPress = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  // Format file list for display
  const renderFileList = (files: any[]) => {
    return (
      <List dense>
        {files.slice(0, 10).map((file, index) => (
          <ListItem key={index} sx={{ display: 'block' }}>
            <Box display="flex" alignItems="center">
              <FolderIcon sx={{ mr: 1, fontSize: 16 }} />
              <Typography variant="body2">{file.name || file.file}</Typography>
            </Box>
            {file.category && (
              <Chip 
                label={file.category} 
                size="small" 
                sx={{ ml: 4, mt: 0.5 }} 
              />
            )}
          </ListItem>
        ))}
        {files.length > 10 && (
          <Typography variant="caption" sx={{ pl: 2 }}>
            ...and {files.length - 10} more files
          </Typography>
        )}
      </List>
    );
  };
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="h6">File Organizer Assistant</Typography>
      </Box>
      
      {/* Messages area */}
      <Box sx={{ 
        flexGrow: 1, 
        p: 2, 
        overflowY: 'auto',
        backgroundColor: '#f5f5f5'
      }}>
        {messages.map((message) => (
          <Box key={message.id}>
            {message.sender === 'user' ? (
              <UserMessage elevation={1}>
                <Typography variant="body1">{message.text}</Typography>
              </UserMessage>
            ) : (
              <AssistantMessage elevation={1}>
                <Typography variant="body1" 
                  sx={{ whiteSpace: 'pre-line' }}>{message.text}</Typography>
                
                {/* Files list if available */}
                {message.files && message.files.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ mb: 1 }} />
                    {renderFileList(message.files)}
                  </Box>
                )}
                
                {/* Suggested actions */}
                {message.suggestedActions && message.suggestedActions.length > 0 && (
                  <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap' }}>
                    {message.suggestedActions.map((action, index) => (
                      <ActionButton 
                        key={index}
                        size="small" 
                        variant="outlined"
                        onClick={() => handleActionClick(action)}
                      >
                        {action}
                      </ActionButton>
                    ))}
                  </Box>
                )}
              </AssistantMessage>
            )}
          </Box>
        ))}
        <div ref={messagesEndRef} />
        
        {/* Loading indicator */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
      </Box>
      
      {/* Input area */}
      <Box sx={{ 
        p: 2, 
        borderTop: 1, 
        borderColor: 'divider',
        backgroundColor: '#fff'
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <TextField
            fullWidth
            placeholder="Ask me to organize or find files..."
            variant="outlined"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            size="small"
          />
          <IconButton 
            color="primary" 
            onClick={handleSendMessage}
            disabled={loading}
            sx={{ ml: 1 }}
          >
            <SendIcon />
          </IconButton>
          
          <IconButton 
            sx={{ ml: 1 }}
          >
            <SearchIcon />
          </IconButton>
          
          <IconButton 
            sx={{ ml: 1 }}
          >
            <SettingsIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default ConversationUI; 