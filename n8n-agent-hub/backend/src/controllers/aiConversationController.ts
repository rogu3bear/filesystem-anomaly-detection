import { Request, Response } from 'express';
import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { getHomeDir } from '../utils/fileUtils';

// Define File type for organization operations
interface FileCategory {
  name: string;
  extensions: string[];
  patterns?: string[];
}

// File categories for organization
const fileCategories: FileCategory[] = [
  {
    name: 'Documents',
    extensions: ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
    patterns: ['report', 'document', 'contract', 'agreement', 'resume', 'cv']
  },
  {
    name: 'Images',
    extensions: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff', '.webp', '.heic'],
    patterns: ['photo', 'image', 'picture', 'screenshot']
  },
  {
    name: 'Videos',
    extensions: ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv', '.webm', '.m4v', '.mpeg', '.3gp'],
    patterns: ['video', 'movie', 'recording', 'screencast']
  },
  {
    name: 'Audio',
    extensions: ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a', '.wma'],
    patterns: ['audio', 'sound', 'music', 'song', 'podcast']
  },
  {
    name: 'Archives',
    extensions: ['.zip', '.rar', '.tar', '.gz', '.7z', '.bz2', '.xz', '.iso'],
    patterns: ['archive', 'backup', 'compressed']
  },
  {
    name: 'Code',
    extensions: ['.js', '.py', '.java', '.c', '.cpp', '.cs', '.php', '.html', '.css', '.rb', '.go', '.ts', '.swift', '.kt'],
    patterns: ['code', 'program', 'script', 'source']
  },
  {
    name: 'Data',
    extensions: ['.json', '.xml', '.sql', '.db', '.sqlite', '.yml', '.yaml', '.toml'],
    patterns: ['data', 'database', 'configuration']
  }
];

// Load config
const loadConfig = (): any => {
  const configPath = path.join(getHomeDir(), '.config/file_anomaly_detection/config.json');
  if (fs.existsSync(configPath)) {
    return JSON.parse(fs.readFileSync(configPath, 'utf8'));
  }
  return null;
};

// Identify file category
const identifyFileCategory = (filename: string, content?: string): string => {
  const ext = path.extname(filename).toLowerCase();
  const basename = path.basename(filename).toLowerCase();
  
  // Check by extension first
  for (const category of fileCategories) {
    if (category.extensions.includes(ext)) {
      return category.name;
    }
  }
  
  // Check by filename patterns
  for (const category of fileCategories) {
    if (category.patterns) {
      for (const pattern of category.patterns) {
        if (basename.includes(pattern)) {
          return category.name;
        }
      }
    }
  }
  
  // If content is provided, we could do more sophisticated analysis here
  
  return 'Other'; // Default category
};

// Process conversation message
export const processMessage = async (req: Request, res: Response): Promise<void> => {
  try {
    const { message } = req.body;
    
    if (!message) {
      res.status(400).json({ success: false, message: 'No message provided' });
      return;
    }
    
    const config = loadConfig();
    if (!config) {
      res.status(500).json({ success: false, message: 'Configuration not found' });
      return;
    }
    
    // Process the user message with simple NLU
    const response = analyzeMessage(message, config);
    
    res.json({
      success: true,
      response
    });
  } catch (error) {
    console.error('Error processing message:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error processing message',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

// Organize files
export const organizeFiles = async (req: Request, res: Response): Promise<void> => {
  try {
    const { source, target, options } = req.body;
    
    const config = loadConfig();
    if (!config) {
      res.status(500).json({ success: false, message: 'Configuration not found' });
      return;
    }
    
    const sourceDir = source || config.source_directory;
    const targetDir = target || config.target_directory;
    
    // Ensure directories exist
    if (!fs.existsSync(sourceDir)) {
      res.status(400).json({ success: false, message: 'Source directory does not exist' });
      return;
    }
    
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    
    // Get all files in source directory
    const files = fs.readdirSync(sourceDir);
    const results = {
      organized: 0,
      skipped: 0,
      errors: 0,
      details: [] as any[]
    };
    
    // Process each file
    for (const file of files) {
      const sourcePath = path.join(sourceDir, file);
      
      // Skip directories
      if (fs.statSync(sourcePath).isDirectory()) {
        results.skipped++;
        continue;
      }
      
      // Identify category
      const category = identifyFileCategory(file);
      
      // Create category directory if it doesn't exist
      const categoryDir = path.join(targetDir, category);
      if (!fs.existsSync(categoryDir)) {
        fs.mkdirSync(categoryDir, { recursive: true });
      }
      
      const targetPath = path.join(categoryDir, file);
      
      try {
        // Handle file already exists
        if (fs.existsSync(targetPath)) {
          if (options?.overwrite) {
            fs.unlinkSync(targetPath); // Delete existing file
          } else {
            const ext = path.extname(file);
            const baseName = path.basename(file, ext);
            const timestamp = Date.now();
            const newFile = `${baseName}_${timestamp}${ext}`;
            fs.renameSync(sourcePath, path.join(categoryDir, newFile));
            
            results.details.push({
              file,
              category,
              action: 'renamed',
              newName: newFile
            });
          }
        } else {
          // Move file
          fs.renameSync(sourcePath, targetPath);
          
          results.details.push({
            file,
            category,
            action: 'moved'
          });
        }
        
        results.organized++;
      } catch (error) {
        results.errors++;
        results.details.push({
          file,
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    }
    
    res.json({
      success: true,
      message: `Organized ${results.organized} files, skipped ${results.skipped}, with ${results.errors} errors`,
      results
    });
  } catch (error) {
    console.error('Error organizing files:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error organizing files',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

// Search files
export const searchFiles = async (req: Request, res: Response): Promise<void> => {
  try {
    const { query, directory, recursive } = req.body;
    
    if (!query) {
      res.status(400).json({ success: false, message: 'No search query provided' });
      return;
    }
    
    const config = loadConfig();
    if (!config) {
      res.status(500).json({ success: false, message: 'Configuration not found' });
      return;
    }
    
    const searchDir = directory || config.source_directory;
    
    // Ensure directory exists
    if (!fs.existsSync(searchDir)) {
      res.status(400).json({ success: false, message: 'Directory does not exist' });
      return;
    }
    
    // Simple search for now (can be improved with better algorithms)
    const searchResults = searchInDirectory(searchDir, query, !!recursive);
    
    res.json({
      success: true,
      results: searchResults
    });
  } catch (error) {
    console.error('Error searching files:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error searching files',
      error: error instanceof Error ? error.message : 'Unknown error'
    });
  }
};

// Helper: Search files in directory
function searchInDirectory(dir: string, query: string, recursive: boolean): any[] {
  const results: any[] = [];
  const files = fs.readdirSync(dir);
  
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stats = fs.statSync(fullPath);
    
    if (stats.isDirectory() && recursive) {
      results.push(...searchInDirectory(fullPath, query, recursive));
    } else if (stats.isFile() && file.toLowerCase().includes(query.toLowerCase())) {
      results.push({
        name: file,
        path: fullPath,
        size: stats.size,
        modifiedTime: stats.mtime
      });
    }
  }
  
  return results;
}

// Analyze message for intent and context
function analyzeMessage(message: string, config: any): any {
  const lowercaseMsg = message.toLowerCase();
  
  // Check for organization intent
  if (
    lowercaseMsg.includes('organize') || 
    lowercaseMsg.includes('sort') || 
    lowercaseMsg.includes('clean up') ||
    lowercaseMsg.includes('arrange') ||
    lowercaseMsg.includes('put in order')
  ) {
    // Extract directory context if any, otherwise use default
    let directory = extractDirectory(lowercaseMsg) || config.source_directory;
    
    return {
      intent: 'organize',
      responseText: `I'll help you organize files in ${directory}. Let me know if you want to start the process now.`,
      suggestedActions: ['Start organization', 'Change directory', 'Cancel'],
      context: { directory }
    };
  }
  
  // Check for search intent
  if (
    lowercaseMsg.includes('find') || 
    lowercaseMsg.includes('search') || 
    lowercaseMsg.includes('look for') ||
    lowercaseMsg.includes('locate')
  ) {
    // Extract what to search for
    const searchTerms = extractSearchTerms(lowercaseMsg);
    let directory = extractDirectory(lowercaseMsg) || config.source_directory;
    
    if (searchTerms) {
      return {
        intent: 'search',
        responseText: `I'll search for "${searchTerms}" in ${directory}. Would you like me to include subdirectories?`,
        suggestedActions: ['Search with subdirectories', 'Search this directory only', 'Cancel'],
        context: { searchTerms, directory }
      };
    } else {
      return {
        intent: 'clarify',
        responseText: `I'd be happy to help you search. What exactly are you looking for?`,
        suggestedActions: ['Search by name', 'Search by type', 'Cancel'],
      };
    }
  }
  
  // Check for help or information intent
  if (
    lowercaseMsg.includes('help') || 
    lowercaseMsg.includes('what can you do') || 
    lowercaseMsg.includes('how do you') ||
    lowercaseMsg.includes('capabilities')
  ) {
    return {
      intent: 'help',
      responseText: `I can help you organize and find files on your computer. For example, you can ask me to:
      
1. "Organize my downloads folder"
2. "Find all PDF files in my documents"
3. "Move images to my Pictures folder"
4. "Search for budget spreadsheets"

What would you like me to help you with today?`,
      suggestedActions: ['Organize files', 'Search files', 'Show my recent files']
    };
  }
  
  // Check for thanks or positive feedback
  if (
    lowercaseMsg.includes('thanks') || 
    lowercaseMsg.includes('thank you') || 
    lowercaseMsg.includes('awesome') ||
    lowercaseMsg.includes('great job')
  ) {
    return {
      intent: 'acknowledgment',
      responseText: `You're welcome! Is there anything else I can help you with?`,
      suggestedActions: ['Organize more files', 'Search for something', 'No, that's all']
    };
  }
  
  // Default response for unrecognized intents
  return {
    intent: 'unknown',
    responseText: `I'm your file organization assistant. I can help organize your files, search for specific items, or provide information about your storage. What would you like me to do?`,
    suggestedActions: ['Help me organize files', 'Search for files', 'What can you do?']
  };
}

// Extract directory from message
function extractDirectory(message: string): string | null {
  // Common directory patterns
  const directoryPatterns = [
    /in\s+([\/~\w\s.-]+)/i,
    /from\s+([\/~\w\s.-]+)/i,
    /at\s+([\/~\w\s.-]+)/i,
    /([\/~\w.-]+(?:\/\w+)+)/i // matches paths like /Users/name/Documents or ~/Downloads
  ];
  
  for (const pattern of directoryPatterns) {
    const match = message.match(pattern);
    if (match && match[1]) {
      let dir = match[1].trim();
      
      // Replace ~ with home directory
      if (dir.startsWith('~')) {
        dir = dir.replace('~', getHomeDir());
      }
      
      // Verify it could be a valid directory
      if (dir.includes('/') || dir.includes('\\')) {
        return dir;
      }
      
      // Check common directory names
      const commonDirs = ['downloads', 'documents', 'pictures', 'desktop', 'music'];
      if (commonDirs.some(commonDir => dir.toLowerCase().includes(commonDir))) {
        // Try to map to actual directory
        const homeDir = getHomeDir();
        const potentialDir = path.join(homeDir, dir);
        if (fs.existsSync(potentialDir)) {
          return potentialDir;
        }
        
        // For common known directories
        if (dir.toLowerCase().includes('downloads')) {
          return path.join(homeDir, 'Downloads');
        } else if (dir.toLowerCase().includes('documents')) {
          return path.join(homeDir, 'Documents');
        } else if (dir.toLowerCase().includes('pictures')) {
          return path.join(homeDir, 'Pictures');
        } else if (dir.toLowerCase().includes('desktop')) {
          return path.join(homeDir, 'Desktop');
        } else if (dir.toLowerCase().includes('music')) {
          return path.join(homeDir, 'Music');
        }
      }
    }
  }
  
  return null;
}

// Extract search terms from message
function extractSearchTerms(message: string): string | null {
  // Patterns for extracting search terms
  const searchPatterns = [
    /find\s+["']?([^"']+)["']?/i,
    /search\s+for\s+["']?([^"']+)["']?/i,
    /look\s+for\s+["']?([^"']+)["']?/i,
    /locate\s+["']?([^"']+)["']?/i,
    /files?\s+(?:named|called)\s+["']?([^"']+)["']?/i,
  ];
  
  for (const pattern of searchPatterns) {
    const match = message.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  return null;
} 