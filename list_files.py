
import os

with open('file_list.txt', 'w') as f:
    for root, dirs, files in os.walk('.'):
        # Skip venv and node_modules to keep it small
        if 'venv' in dirs:
            dirs.remove('venv')
        if 'node_modules' in dirs:
            dirs.remove('node_modules')
            
        for file in files:
            f.write(os.path.join(root, file) + '\n')
