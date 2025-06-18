import os
import sys
import hashlib
import zipfile
import tempfile
import shutil


def sha256sum(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_zip_recursive(src_dir):
    temp_dir = tempfile.mkdtemp()
    for root, _, files in os.walk(src_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, src_dir)
            if zipfile.is_zipfile(full_path):
                with zipfile.ZipFile(full_path, 'r') as zip_ref:
                    extract_to = os.path.join(temp_dir, rel_path + "_unzipped")
                    zip_ref.extractall(extract_to)
    return temp_dir

def generate_file_hashes(directory):
    hashes = {}
    extracted_dir = extract_zip_recursive(directory)
    search_dirs = [directory, extracted_dir]

    for base_dir in search_dirs:
        for root, _, files in os.walk(base_dir):
            for file in files:
                full_path = os.path.join(root, file)
                try:
                    rel_path = os.path.relpath(full_path)
                    file_hash = sha256sum(full_path)
                    hashes[os.path.join(file)] = file_hash
                except Exception as e:
                    print(f"Failed hashing {full_path}: {e}")
    return hashes

def compare_dir_layout(dir1, dir2):
    unique_dirs = []
    def _get_all_files(base_dir):
        file_set = set()
        for dirpath, _, filenames in os.walk(base_dir):
            for filename in filenames:
                relative_path = os.path.relpath(os.path.join(dirpath, filename), base_dir)
                file_set.add(relative_path)
        return file_set

    files_dir1 = _get_all_files(dir1)
    files_dir2 = _get_all_files(dir2)

    only_in_dir1 = files_dir1 - files_dir2
    only_in_dir2 = files_dir2 - files_dir1
    unique_dirs = only_in_dir1.union(only_in_dir2)

    for filepath in sorted(only_in_dir1):
        print(f"{filepath} is only in: {dir1}")

    for filepath in sorted(only_in_dir2):
        print(f"{filepath} is only in: {dir2}")
    return unique_dirs
   
    
        
def compare_hashes(hashes1, hashes2):
    mismatches = []
    all_keys = set(hashes1.values()).union(hashes2.values())
    for h in all_keys:
        files1 = [k for k,v in hashes1.items() if v == h]
        files2 = [k for k,v in hashes2.items() if v == h]
        if not files1 or not files2:
            mismatches.append((files1 or ('File Differs From Original'), files2 or ('File Differs From Original')))
    return mismatches

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_dirs.py <directory1> <directory2>")
        sys.exit(1)

    dir1, dir2 = sys.argv[1], sys.argv[2]

    if os.path.exists(dir1) == False and os.path.exists(dir2) == False:
        print("Error: Both directories do not exist. Please ensure you are working in the correct directory")
        sys.exit(1)

    if os.path.exists(dir1) == False:
        print("Error: The first directory does not exist")
        sys.exit(1)

    if os.path.exists(dir2) == False:
        print("Error: The second directory does not exist")
        sys.exit(1)

    print("Generating file hashes...")
    hashes1 = generate_file_hashes(dir1)
    hashes2 = generate_file_hashes(dir2)

    print("Comparing hashes...")
    diffs = compare_hashes(hashes1, hashes2)

    san = compare_dir_layout(dir1,dir2)



    if not diffs:
        print("No differences found. Directories match.")
    else:
        print("Differences found in the following files:")
        for f1, f2 in diffs:
            print(f"- {f1} <=> {f2}")
        print("\nFollowing files are present in one directory but not the other:")
        ### Moved compare_dir_layout up to store in the sanitization (san) variable to then run against diffs for matches. Based on how we decide to do that we'll move these print statements around ###
