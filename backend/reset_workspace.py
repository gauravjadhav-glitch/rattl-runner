import os
import shutil

WORKSPACE_DIR = os.path.join(os.getcwd(), 'workspace')

if os.path.exists(WORKSPACE_DIR):
    try:
        shutil.rmtree(WORKSPACE_DIR)
        print(f"Removed {WORKSPACE_DIR}")
    except Exception as e:
        print(f"Error removing workspace: {e}")

os.makedirs(WORKSPACE_DIR, exist_ok=True)
print(f"Recreated empty {WORKSPACE_DIR}")
