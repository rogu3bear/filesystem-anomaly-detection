import os
import shutil

# Define the directory to organize
DIRECTORY_TO_ORGANIZE = './'

# Function to organize files by extension
def organize_files_by_extension(directory):
    # List all files in the directory
    for filename in os.listdir(directory):
        # Get the file extension
        file_extension = os.path.splitext(filename)[1][1:]
        if file_extension:  # If there is an extension
            # Create a directory for the extension if it doesn't exist
            extension_dir = os.path.join(directory, file_extension)
            if not os.path.exists(extension_dir):
                os.makedirs(extension_dir)
            # Move the file into the extension directory
            shutil.move(os.path.join(directory, filename), os.path.join(extension_dir, filename))

# Run the organization function
organize_files_by_extension(DIRECTORY_TO_ORGANIZE) 