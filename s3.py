import boto3
import os

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    region_name="us-east-1"
)

def download_file(bucket_name, s3_key, local_file_path):
    """Download file from S3 bucket to local path"""
    try:
        print(f"📥 Downloading '{s3_key}' from bucket '{bucket_name}'...")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        
        # Download the file
        s3.download_file(bucket_name, s3_key, local_file_path)
        
        # Check if file was downloaded successfully
        if os.path.exists(local_file_path):
            file_size = os.path.getsize(local_file_path)
            print(f"✅ Successfully downloaded to '{local_file_path}' (Size: {file_size} bytes)")
            return True
        else:
            print(f"❌ Download failed - file not found at '{local_file_path}'")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        return False

def download_all_files_from_prefix(bucket_name, prefix, local_base_dir="./downloads"):
    """Download all files from S3 bucket with specified prefix"""
    try:
        print(f"\n🔍 Finding all files in bucket '{bucket_name}' with prefix '{prefix}'...")
        
        # List all objects with the prefix
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' not in response:
            print(f"📭 No files found with prefix '{prefix}'")
            return []
        
        files = response['Contents']
        total_files = len(files)
        successful_downloads = []
        failed_downloads = []
        
        print(f"📁 Found {total_files} files to download...\n")
        
        for i, obj in enumerate(files, 1):
            s3_key = obj['Key']
            file_name = os.path.basename(s3_key)
            
            # Create local path maintaining directory structure
            relative_path = s3_key.replace(prefix, '').lstrip('/')
            local_path = os.path.join(local_base_dir, relative_path)
            
            print(f"[{i}/{total_files}] Processing: {file_name}")
            
            if download_file(bucket_name, s3_key, local_path):
                successful_downloads.append(s3_key)
            else:
                failed_downloads.append(s3_key)
            
            print()  # Empty line for better readability
        
        # Summary
        print(f"\n📊 Download Summary:")
        print(f"✅ Successful: {len(successful_downloads)}/{total_files}")
        print(f"❌ Failed: {len(failed_downloads)}/{total_files}")
        
        if failed_downloads:
            print(f"\n❌ Failed downloads:")
            for failed_file in failed_downloads:
                print(f"  - {failed_file}")
        
        return successful_downloads
        
    except Exception as e:
        print(f"❌ Error in batch download: {e}")
        return []

def get_all_files_list(bucket_name, prefix=""):
    """Get list of all files in bucket with prefix"""
    try:
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=prefix
        )
        
        if 'Contents' in response:
            files = []
            print(f"\n📁 Files in bucket '{bucket_name}' with prefix '{prefix}':")
            for obj in response['Contents']:
                file_info = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'modified': obj['LastModified']
                }
                files.append(file_info)
                print(f"  - {obj['Key']} (Size: {obj['Size']} bytes, Modified: {obj['LastModified']})")
            
            print(f"\nTotal files found: {len(files)}")
            return files
        else:
            print(f"\n📭 No files found in bucket '{bucket_name}' with prefix '{prefix}'")
            return []
            
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return []

def create_folder_summary_json(bucket_name, base_prefix="XC_Recordings/"):
    """Create JSON summary of folder structure with file counts"""
    import json
    from collections import defaultdict
    
    try:
        print(f"\n🔍 Creating folder summary for '{base_prefix}' in bucket '{bucket_name}'...")
        
        # Get all objects with the base prefix
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=base_prefix
        )
        
        if 'Contents' not in response:
            print(f"📭 No files found with prefix '{base_prefix}'")
            return {}
        
        # Build folder structure
        folder_structure = defaultdict(lambda: {'files': [], 'subfolders': defaultdict(dict), 'file_count': 0})
        
        for obj in response['Contents']:
            key = obj['Key']
            # Remove base prefix to get relative path
            relative_path = key.replace(base_prefix, '').lstrip('/')
            
            if not relative_path:  # Skip if empty
                continue
                
            path_parts = relative_path.split('/')
            
            # Build nested structure
            current_level = folder_structure
            current_path = ""
            
            for i, part in enumerate(path_parts):
                current_path = f"{current_path}/{part}" if current_path else part
                
                if i == len(path_parts) - 1:  # This is a file
                    # Find the parent folder
                    parent_path = '/'.join(path_parts[:-1]) if len(path_parts) > 1 else 'root'
                    
                    # Navigate to parent folder
                    temp_level = folder_structure
                    if parent_path != 'root':
                        for folder in path_parts[:-1]:
                            temp_level = temp_level[folder]['subfolders']
                    
                    # Add file info
                    file_info = {
                        'name': part,
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat()
                    }
                    
                    if parent_path == 'root':
                        folder_structure['root']['files'].append(file_info)
                        folder_structure['root']['file_count'] += 1
                    else:
                        parent_folder = path_parts[-2]
                        temp_parent = folder_structure
                        for folder in path_parts[:-2]:
                            temp_parent = temp_parent[folder]['subfolders']
                        temp_parent[parent_folder]['files'].append(file_info)
                        temp_parent[parent_folder]['file_count'] += 1
                else:  # This is a folder
                    if part not in current_level:
                        current_level[part] = {'files': [], 'subfolders': defaultdict(dict), 'file_count': 0}
                    current_level = current_level[part]['subfolders']
        
        # Convert to regular dict and calculate totals
        def convert_and_count(d):
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    converted_subfolders = convert_and_count(value.get('subfolders', {}))
                    total_files = value.get('file_count', 0)
                    
                    # Add subfolder file counts
                    for subfolder in converted_subfolders.values():
                        total_files += subfolder.get('total_files', 0)
                    
                    result[key] = {
                        'files': value.get('files', []),
                        'file_count': value.get('file_count', 0),
                        'total_files': total_files,
                        'subfolders': converted_subfolders
                    }
            return result
        
        final_structure = convert_and_count(folder_structure)
        
        # Create summary
        summary = {
            'bucket': bucket_name,
            'base_path': base_prefix,
            'generated_at': obj['LastModified'].isoformat() if 'obj' in locals() else None,
            'structure': final_structure
        }
        
        # Save to JSON file
        json_filename = f"folder_summary_{bucket_name.replace('-', '_')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Folder summary saved to '{json_filename}'")
        
        # Print summary
        def print_structure(structure, indent=0):
            for folder_name, folder_data in structure.items():
                spaces = "  " * indent
                file_count = folder_data.get('file_count', 0)
                total_files = folder_data.get('total_files', 0)
                print(f"{spaces}📁 {folder_name}/ (Files: {file_count}, Total: {total_files})")
                
                # Print files in this folder
                for file_info in folder_data.get('files', []):
                    print(f"{spaces}  📄 {file_info['name']} ({file_info['size']} bytes)")
                
                # Print subfolders
                if folder_data.get('subfolders'):
                    print_structure(folder_data['subfolders'], indent + 1)
        
        print(f"\n📊 Folder Structure Summary:")
        print_structure(final_structure)
        
        return summary
        
    except Exception as e:
        print(f"❌ Error creating folder summary: {e}")
        return {}

def create_complete_folder_summary(bucket_name, base_prefix="XC_Recordings/"):
    """Create complete folder structure summary for all years, months and days"""
    import json
    from collections import defaultdict
    
    try:
        print(f"\n🔍 Creating complete folder summary for '{base_prefix}' in bucket '{bucket_name}'...")
        
        # Get all objects with the base prefix
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix=base_prefix
        )
        
        folder_structure = defaultdict(lambda: {'file_count': 0, 'subfolders': defaultdict(dict)})
        total_objects = 0
        
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                total_objects += 1
                key = obj['Key']
                # Remove base prefix to get relative path
                relative_path = key.replace(base_prefix, '').lstrip('/')
                
                if not relative_path:  # Skip if empty
                    continue
                    
                path_parts = relative_path.split('/')
                
                # Navigate through folder structure and count files
                current_level = folder_structure
                
                for i, part in enumerate(path_parts):
                    if i == len(path_parts) - 1:  # This is a file
                        # Count file in the parent folder
                        if len(path_parts) == 1:  # File in root
                            folder_structure['root']['file_count'] += 1
                        else:
                            # Navigate to parent folder and increment count
                            temp_level = folder_structure
                            for folder in path_parts[:-1]:
                                if folder not in temp_level:
                                    temp_level[folder] = {'file_count': 0, 'subfolders': defaultdict(dict)}
                                temp_level = temp_level[folder]['subfolders']
                            
                            # Get parent folder name
                            parent_folder = path_parts[-2]
                            parent_level = folder_structure
                            for folder in path_parts[:-2]:
                                parent_level = parent_level[folder]['subfolders']
                            parent_level[parent_folder]['file_count'] += 1
                    else:  # This is a folder
                        if part not in current_level:
                            current_level[part] = {'file_count': 0, 'subfolders': defaultdict(dict)}
                        current_level = current_level[part]['subfolders']
        
        if total_objects == 0:
            print(f"📭 No files found with prefix '{base_prefix}'")
            return {}
        
        # Convert to regular dict and calculate totals
        def convert_and_count(d):
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    converted_subfolders = convert_and_count(value.get('subfolders', {}))
                    direct_files = value.get('file_count', 0)
                    total_files = direct_files
                    
                    # Add subfolder file counts
                    for subfolder in converted_subfolders.values():
                        total_files += subfolder.get('total_files', 0)
                    
                    result[key] = {
                        'file_count': direct_files,
                        'total_files': total_files,
                        'subfolders': converted_subfolders
                    }
            return result
        
        final_structure = convert_and_count(folder_structure)
        
        # Create summary
        summary = {
            'bucket': bucket_name,
            'base_path': base_prefix,
            'generated_at': None,
            'total_objects_processed': total_objects,
            'structure': final_structure
        }
        
        # Save to JSON file
        json_filename = f"complete_folder_summary_{bucket_name.replace('-', '_')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Complete folder summary saved to '{json_filename}'")
        print(f"📊 Total objects processed: {total_objects}")
        
        # Print summary
        def print_structure(structure, indent=0):
            for folder_name, folder_data in sorted(structure.items()):
                spaces = "  " * indent
                file_count = folder_data.get('file_count', 0)
                total_files = folder_data.get('total_files', 0)
                print(f"{spaces}📁 {folder_name}/ (Direct: {file_count}, Total: {total_files})")
                
                # Print subfolders
                if folder_data.get('subfolders'):
                    print_structure(folder_data['subfolders'], indent + 1)
        
        print(f"\n📊 Complete Folder Structure:")
        print_structure(final_structure)
        
        return summary
        
    except Exception as e:
        print(f"❌ Error creating complete folder summary: {e}")
        return {}

def create_folders_only_summary(bucket_name, base_prefix="XC_Recordings/"):
    """Create simplified folder structure summary without individual file details"""
    import json
    from collections import defaultdict
    
    try:
        print(f"\n🔍 Creating folders-only summary for '{base_prefix}' in bucket '{bucket_name}'...")
        
        # Get all objects with the base prefix
        response = s3.list_objects_v2(
            Bucket=bucket_name,
            Prefix=base_prefix
        )
        
        if 'Contents' not in response:
            print(f"📭 No files found with prefix '{base_prefix}'")
            return {}
        
        # Build folder structure (without storing individual files)
        folder_structure = defaultdict(lambda: {'file_count': 0, 'subfolders': defaultdict(dict)})
        
        for obj in response['Contents']:
            key = obj['Key']
            # Remove base prefix to get relative path
            relative_path = key.replace(base_prefix, '').lstrip('/')
            
            if not relative_path:  # Skip if empty
                continue
                
            path_parts = relative_path.split('/')
            
            # Navigate through folder structure and count files
            current_level = folder_structure
            
            for i, part in enumerate(path_parts):
                if i == len(path_parts) - 1:  # This is a file
                    # Count file in the parent folder
                    if len(path_parts) == 1:  # File in root
                        folder_structure['root']['file_count'] += 1
                    else:
                        # Navigate to parent folder and increment count
                        temp_level = folder_structure
                        for folder in path_parts[:-1]:
                            if folder not in temp_level:
                                temp_level[folder] = {'file_count': 0, 'subfolders': defaultdict(dict)}
                            temp_level = temp_level[folder]['subfolders']
                        
                        # Get parent folder name
                        parent_folder = path_parts[-2]
                        parent_level = folder_structure
                        for folder in path_parts[:-2]:
                            parent_level = parent_level[folder]['subfolders']
                        parent_level[parent_folder]['file_count'] += 1
                else:  # This is a folder
                    if part not in current_level:
                        current_level[part] = {'file_count': 0, 'subfolders': defaultdict(dict)}
                    current_level = current_level[part]['subfolders']
        
        # Convert to regular dict and calculate totals
        def convert_and_count(d):
            result = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    converted_subfolders = convert_and_count(value.get('subfolders', {}))
                    direct_files = value.get('file_count', 0)
                    total_files = direct_files
                    
                    # Add subfolder file counts
                    for subfolder in converted_subfolders.values():
                        total_files += subfolder.get('total_files', 0)
                    
                    result[key] = {
                        'file_count': direct_files,
                        'total_files': total_files,
                        'subfolders': converted_subfolders
                    }
            return result
        
        final_structure = convert_and_count(folder_structure)
        
        # Create summary
        summary = {
            'bucket': bucket_name,
            'base_path': base_prefix,
            'generated_at': response['Contents'][0]['LastModified'].isoformat() if response['Contents'] else None,
            'structure': final_structure
        }
        
        # Save to JSON file
        json_filename = f"folders_only_summary_{bucket_name.replace('-', '_')}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✅ Folders-only summary saved to '{json_filename}'")
        
        # Print summary
        def print_structure(structure, indent=0):
            for folder_name, folder_data in structure.items():
                spaces = "  " * indent
                file_count = folder_data.get('file_count', 0)
                total_files = folder_data.get('total_files', 0)
                print(f"{spaces}📁 {folder_name}/ (Direct files: {file_count}, Total files: {total_files})")
                
                # Print subfolders
                if folder_data.get('subfolders'):
                    print_structure(folder_data['subfolders'], indent + 1)
        
        print(f"\n📊 Folders Structure (Files count only):")
        print_structure(final_structure)
        
        return summary
        
    except Exception as e:
        print(f"❌ Error creating folders summary: {e}")
        return {}

if __name__ == "__main__":
    bucket_name = "combined-client-data"
    base_prefix = "c_25884/XC_Recordings/"
    
    # Example 1: Create complete folder summary (all years, months, days)
    print("\n=== Creating Complete Folder Summary (All Years/Months/Days) ===")
    create_complete_folder_summary(bucket_name, base_prefix)
    
    # Example 2: Create folders-only summary (without file details)
    print("\n=== Creating Folders-Only Summary ===")
    # create_folders_only_summary(bucket_name, base_prefix)
    
    # Example 3: Create detailed folder summary JSON
    print("\n=== Creating Detailed Folder Summary JSON ===")
    # create_folder_summary_json(bucket_name, base_prefix)
    
    # Example 4: List files in a specific path
    print("\n=== Listing Files ===")
    # files = get_all_files_list(bucket_name, "c_25884/XC_Recordings/2024/03/26/")
    # print(f"Found {len(files)} files")
    
    # Example 5: Download all files from a prefix
    print("\n=== Batch Download ===")
    # download_all_files_from_prefix(bucket_name, "c_25884/XC_Recordings/2024/03/26/", "./downloads/")
    
    # Example 6: Download single file
    print("\n=== Single File Download ===")
    s3_file_path = "c_25884/XC_Recordings/2025/01/02/20250102_10003900m16s_7066911383_SC_A-AtefAhmadAbdelaty.mp3"
    local_file_path = "./downloads/20250102_10003900m16s_7066911383_SC_A-AtefAhmadAbdelaty.mp3"
    # download_file(bucket_name, s3_file_path, local_file_path)
