"""
Copy all files from development folder to RohaTax folder
"""
import os
import shutil
from pathlib import Path

# Source and destination folders
DEV_FOLDER = r"C:\Users\user\Desktop\절대 관리\v2 최적화버전 10-13 2시14분 모튤분리전"
DEST_FOLDER = r"C:\Users\user\Desktop\RohaTax"

# Exclude patterns
EXCLUDE_FOLDERS = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env'}
EXCLUDE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.log', '.tmp', '.bak'}

def should_copy(path):
    """Check if file/folder should be copied"""
    if path.name.startswith('.'):
        return False
    
    if path.name in EXCLUDE_FOLDERS:
        return False
    
    if path.is_file() and path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return False
    
    return True

def copy_files(src, dst):
    """Copy files and folders recursively"""
    copied_count = 0
    skipped_count = 0
    
    print(f"\nCopying from: {src}")
    print(f"Copying to: {dst}\n")
    
    # Create destination if it doesn't exist
    os.makedirs(dst, exist_ok=True)
    
    # Walk through source directory
    for root, dirs, files in os.walk(src):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if should_copy(Path(root) / d)]
        
        # Get relative path
        rel_path = os.path.relpath(root, src)
        dest_dir = os.path.join(dst, rel_path)
        
        # Create destination directory
        if rel_path != '.':
            os.makedirs(dest_dir, exist_ok=True)
        
        # Copy files
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dest_dir, file)
            
            if should_copy(Path(src_file)):
                try:
                    shutil.copy2(src_file, dst_file)
                    copied_count += 1
                    if copied_count % 10 == 0:
                        print(f"Copied {copied_count} files...")
                except Exception as e:
                    print(f"Error copying {src_file}: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
    
    print(f"\nCompleted!")
    print(f"Files copied: {copied_count}")
    print(f"Files skipped: {skipped_count}")
    return copied_count

if __name__ == "__main__":
    print("=" * 60)
    print("RohaTax File Copy Script")
    print("=" * 60)
    
    # Verify source exists
    if not os.path.exists(DEV_FOLDER):
        print(f"ERROR: Source folder does not exist: {DEV_FOLDER}")
        input("\nPress Enter to exit...")
        exit(1)
    
    # Ask for confirmation
    print(f"\nSource: {DEV_FOLDER}")
    print(f"Destination: {DEST_FOLDER}")
    print("\nThis will copy all files to RohaTax folder.")
    response = input("Continue? (y/n): ")
    
    if response.lower() != 'y':
        print("Cancelled.")
        input("\nPress Enter to exit...")
        exit(0)
    
    try:
        copied = copy_files(DEV_FOLDER, DEST_FOLDER)
        
        if copied > 0:
            print("\n" + "=" * 60)
            print("SUCCESS: Files copied successfully!")
            print(f"Copied {copied} files to {DEST_FOLDER}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("WARNING: No files were copied!")
            print("=" * 60)
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
    
    input("\nPress Enter to exit...")
