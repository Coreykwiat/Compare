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
                    rel_path = os.path.relpath(full_path, base_dir)
                    file_hash = sha256sum(full_path)
                    hashes[os.path.join(base_dir, rel_path)] = file_hash
                except Exception as e:
                    print(f"Failed hashing {full_path}: {e}")
    return hashes

def compare_dir_layout(dir1, dir2):
    def _get_all_files(base_dir):
        base_name = os.path.basename(os.path.normpath(base_dir))
        file_set = {}
        for dirpath, _, filenames in os.walk(base_dir):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(full_path, base_dir)
                path_with_base = os.path.join(base_name, relative_path)
                file_set[relative_path] = path_with_base
        return file_set

    files_dir1 = _get_all_files(dir1)
    files_dir2 = _get_all_files(dir2)

    set1 = set(files_dir1.keys())
    set2 = set(files_dir2.keys())

    only_in_dir1_keys = set1 - set2
    only_in_dir2_keys = set2 - set1

    only_in_dir1 = {files_dir1[k] for k in only_in_dir1_keys}
    only_in_dir2 = {files_dir2[k] for k in only_in_dir2_keys}

    # I'm lazy and didn't want to fix variables so  just strip what I need to. 

    if not only_in_dir1 and not only_in_dir2:
       print("\n- Directories Have Same Files")
    else:
       print("\nDifferences in Directories:\n")
       for filepath in sorted(only_in_dir1):
           trimmed = filepath.split("/", 1)[-1]
           print(f"{trimmed} is only in: {dir1}")
       for filepath in sorted(only_in_dir2):
           trimmed = filepath.split("/", 1)[-1]
           print(f"{trimmed} is only in: {dir2}")


    return only_in_dir1, only_in_dir2
    
        
def compare_hashes(hashes1, hashes2, dir1_diff, dir2_diff):
    mismatches = []
    all_keys = set(hashes1.values()).union(hashes2.values())

    for h in all_keys:
        files1 = [k for k, v in hashes1.items() if v == h]
        files2 = [k for k, v in hashes2.items() if v == h]

        files1_san = set(files1) - set(dir1_diff)
        files2_san = set(files2) - set(dir2_diff)

        if not files1_san or not files2_san:
            val1 = files1_san or {'File in Directory 2 Differs'}
            val2 = files2_san or {'File in Directory 1 Differs'}
            mismatches.append((val1, val2))
            
    filtered = []
    for pair in mismatches:
        if not (pair[0] == {'File in Directory 2 Differs'} and pair[1] == {'File in Directory 1 Differs'}):
            filtered.append(pair)

    return filtered




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

    dir1_diff, dir2_diff = compare_dir_layout(dir1, dir2)

    hashes1 = generate_file_hashes(dir1)
    hashes2 = generate_file_hashes(dir2)

    diffs = compare_hashes(hashes1, hashes2, dir1_diff, dir2_diff)


    # I'm lazy and didn't want to fix variables so  just strip what I need to. 

    if not diffs:
       print("\nNo differences found. Directories match.")
    else:
       print("\nDifferences found in the following files:\n")
       for f1, f2 in diffs:
           file_message = next(iter(f1)) if isinstance(f1, set) else f1
           directory_message = next(iter(f2)) if isinstance(f2, set) else f2

           if "File in Directory" in file_message and "File in Directory" not in directory_message:
               file_message, directory_message = directory_message, file_message

           trimmed_file_message = file_message.split("/", 1)[-1]
           trimmed_directory_message = directory_message.split("/", 1)[-1]
           print(f"- {trimmed_file_message} <=> {trimmed_directory_message}")



