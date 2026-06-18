import os

def generate_codebase_map_markdown(start_path=".", max_depth=2):
    map_content = []
    map_content.append("# OpenSlap Codebase Map\n\n")
    map_content.append("Esta é uma representação da estrutura de diretórios e arquivos do projeto OpenSlap.\n\n")

    for root, dirs, files in os.walk(start_path):
        # Calculate current depth relative to start_path
        relative_path = os.path.relpath(root, start_path)
        
        if relative_path == ".":
            current_depth = 0
        else:
            current_depth = relative_path.count(os.sep) + 1

        if current_depth > max_depth:
            # If current directory is deeper than max_depth, skip it and its children
            dirs[:] = [] # This prunes the search
            continue

        # Indentation for current level
        indent = "  " * current_depth
        
        # Add the directory entry itself, unless it's the start_path
        if root != start_path:
            dir_name = os.path.basename(root)
            map_content.append(f"{indent}- {dir_name}/\n")

        # Add files in the current directory
        file_indent = "  " * (current_depth + 1)
        for f in sorted(files):
            # Exclude common temporary or irrelevant files for a codebase map
            if f.endswith(('.pyc', '.sqlite3-journal', '.DS_Store', '.log', '.swp', '.tmp')):
                continue
            map_content.append(f"{file_indent}- {f}\n")
        
        # Prune subdirectories if we are at max_depth to prevent going deeper
        if current_depth >= max_depth:
            dirs[:] = [] # Prevent further recursion

    return "".join(map_content)

markdown_output = generate_codebase_map_markdown(start_path=".", max_depth=2)
