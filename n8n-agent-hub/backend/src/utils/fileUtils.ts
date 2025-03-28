import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';

/**
 * Get the user's home directory in a cross-platform way
 */
export const getHomeDir = (): string => {
  return process.env.HOME || process.env.USERPROFILE || '/tmp';
};

/**
 * Get file stats with appropriate error handling
 */
export const getFileStats = (filePath: string): Promise<fs.Stats | null> => {
  return new Promise((resolve) => {
    fs.stat(filePath, (err, stats) => {
      if (err) {
        resolve(null);
      } else {
        resolve(stats);
      }
    });
  });
};

/**
 * List files in a directory
 */
export const listFilesInDirectory = async (
  directory: string,
  options: { 
    includeHidden?: boolean,
    recursive?: boolean,
    maxDepth?: number,
    filter?: (filename: string) => boolean
  } = {}
): Promise<string[]> => {
  const { 
    includeHidden = false, 
    recursive = false,
    maxDepth = 1,
    filter = () => true
  } = options;
  
  if (!fs.existsSync(directory)) {
    return [];
  }
  
  const files = await fs.promises.readdir(directory);
  let result: string[] = [];
  
  for (const file of files) {
    // Skip hidden files unless explicitly requested
    if (!includeHidden && file.startsWith('.')) {
      continue;
    }
    
    const fullPath = path.join(directory, file);
    const stats = await getFileStats(fullPath);
    
    if (!stats) continue;
    
    if (stats.isDirectory() && recursive && maxDepth > 0) {
      const subDirFiles = await listFilesInDirectory(fullPath, {
        includeHidden,
        recursive,
        maxDepth: maxDepth - 1,
        filter
      });
      
      result = result.concat(subDirFiles.map(f => path.join(file, f)));
    } else if (stats.isFile() && filter(file)) {
      result.push(file);
    }
  }
  
  return result;
};

/**
 * Get file extension safely (returns lowercase extension without the dot)
 */
export const getFileExtension = (filename: string): string => {
  const ext = path.extname(filename).toLowerCase();
  return ext.startsWith('.') ? ext.substring(1) : ext;
};

/**
 * Returns the file size in a human-readable format
 */
export const getHumanReadableSize = (bytes: number): string => {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
};

/**
 * Check if a file is a specific type based on extension
 */
export const isFileType = (filename: string, types: string[]): boolean => {
  const ext = getFileExtension(filename);
  return types.includes(ext);
};

/**
 * Create directory recursively
 */
export const createDirectory = async (dirPath: string): Promise<boolean> => {
  try {
    await fs.promises.mkdir(dirPath, { recursive: true });
    return true;
  } catch (error) {
    console.error(`Error creating directory ${dirPath}:`, error);
    return false;
  }
};

/**
 * Move file safely (handles cases like cross-device moves)
 */
export const moveFile = async (
  sourcePath: string,
  targetPath: string,
  options: { overwrite?: boolean } = {}
): Promise<boolean> => {
  const { overwrite = false } = options;
  
  try {
    // Check if target exists
    if (fs.existsSync(targetPath) && !overwrite) {
      return false;
    }
    
    // Try rename (fastest method), but it can fail for cross-device moves
    try {
      await fs.promises.rename(sourcePath, targetPath);
      return true;
    } catch (error) {
      // If rename fails, try copy+delete method
      await fs.promises.copyFile(sourcePath, targetPath);
      await fs.promises.unlink(sourcePath);
      return true;
    }
  } catch (error) {
    console.error(`Error moving file from ${sourcePath} to ${targetPath}:`, error);
    return false;
  }
};

/**
 * Execute a shell command asynchronously
 */
export const executeCommand = (command: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        reject(error);
      } else {
        resolve(stdout || stderr);
      }
    });
  });
};

/**
 * Check if GitHub CLI is available
 */
export const isGitHubCLIAvailable = async (): Promise<boolean> => {
  try {
    await executeCommand('gh --version');
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Check if a path is writable
 */
export const isPathWritable = async (dirPath: string): Promise<boolean> => {
  try {
    const testFile = path.join(dirPath, `.test-${Date.now()}`);
    await fs.promises.writeFile(testFile, 'test');
    await fs.promises.unlink(testFile);
    return true;
  } catch (error) {
    return false;
  }
}; 