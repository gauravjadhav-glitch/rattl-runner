from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import subprocess
import tempfile
import os
import glob
import glob
import io
import json
import yaml
try:
    import runner
except ImportError:
    # If run as script vs module
    from . import runner

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestRequest(BaseModel):
    yaml_content: str

class FileSaveRequest(BaseModel):
    path: str
    content: str

class TerminalRequest(BaseModel):
    command: str

# --- Device & Run ---

@app.get("/devices")
def get_devices():
    try:
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        return {"output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/packages")
def get_packages():
    try:
        # Lists only 3rd party packages for better visibility, but can be changed to all
        result = subprocess.run(["adb", "shell", "pm", "list", "packages", "-3"], capture_output=True, text=True)
        packages = []
        for line in result.stdout.splitlines():
            if line.startswith("package:"):
                packages.append(line.replace("package:", "").strip())
        
        # If no 3rd party packages or if we want to also allow system apps optionally, 
        # we could have another call, but let's start with -3
        if not packages:
             result = subprocess.run(["adb", "shell", "pm", "list", "packages"], capture_output=True, text=True)
             for line in result.stdout.splitlines():
                if line.startswith("package:"):
                    packages.append(line.replace("package:", "").strip())
                    
        return {"packages": sorted(packages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RunStepRequest(BaseModel):
    step: dict

@app.post("/validate-yaml")
def validate_yaml(request: TestRequest):
    """Validate YAML syntax without running the test"""
    if not request.yaml_content:
        return {"valid": False, "error": "YAML content is empty"}
    
    try:
        # Try to parse the YAML
        docs = list(yaml.safe_load_all(request.yaml_content))
        
        # Basic structure validation
        if len(docs) == 0:
            return {"valid": False, "error": "YAML file is empty"}
        
        # Check if it has the expected structure (header + flow or just flow)
        header = docs[0] if len(docs) > 0 else {}
        flow = docs[1] if len(docs) > 1 else (docs[0] if isinstance(docs[0], list) else [])
        
        if not isinstance(flow, list):
            return {"valid": False, "error": "Test flow must be a list of steps (starting with '-')"}
        
        return {"valid": True, "message": f"Valid YAML with {len(flow)} steps"}
        
    except yaml.YAMLError as e:
        error_msg = str(e)
        line_num = None
        col_num = None
        
        # Extract line number if available
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            line_num = mark.line + 1
            col_num = mark.column + 1
            error_msg = f"YAML Syntax Error at line {line_num}, column {col_num}: {e.problem}"
        
        return {
            "valid": False, 
            "error": error_msg,
            "line": line_num,
            "column": col_num
        }
    except Exception as e:
        return {"valid": False, "error": f"Validation error: {str(e)}"}

@app.post("/run")
def run_test(request: TestRequest):
    if not request.yaml_content:
         raise HTTPException(status_code=400, detail="YAML content is empty")
    
    # Validate YAML before running
    try:
        yaml.safe_load_all(request.yaml_content)
    except yaml.YAMLError as e:
        error_msg = str(e)
        if hasattr(e, 'problem_mark'):
            mark = e.problem_mark
            error_msg = f"YAML Syntax Error at line {mark.line + 1}, column {mark.column + 1}: {e.problem}"
        raise HTTPException(status_code=400, detail=error_msg)

    return StreamingResponse(runner.run_yaml_custom(request.yaml_content), media_type="text/event-stream")

class RunFolderRequest(BaseModel):
    folder_path: str

@app.post("/run-folder")
def run_folder_endpoint(request: RunFolderRequest):
    full_path = get_safe_path(request.folder_path)
    return StreamingResponse(runner.run_folder_custom(full_path), media_type="text/event-stream")

@app.post("/run-step")
def run_step(request: RunStepRequest):
    try:
        print(f"Executing step: {request.step}")
        log = runner.run_test_step(request.step)
        return {"status": "success", "log": log}
    except Exception as e:
        print(f"Step execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- File System ---

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Revert: Point to the main test-flows directory in the project root
WORKSPACE_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "test-flows"))
if not os.path.exists(WORKSPACE_DIR):
    os.makedirs(WORKSPACE_DIR)

def get_safe_path(path):
    # Prevent directory traversal
    full_path = os.path.abspath(os.path.join(WORKSPACE_DIR, path))
    if not full_path.startswith(WORKSPACE_DIR):
        raise HTTPException(status_code=403, detail="Access denied")
    return full_path

@app.get("/files")
def list_files():
    try:
        files = []
        
        # 1. Include YAML files and folders from WORKSPACE_DIR
            
        # 2. Include YAML files and folders from WORKSPACE_DIR
        for root, dirs, filenames in os.walk(WORKSPACE_DIR):
             # Add directories
             for date_dir in dirs:
                 full_path = os.path.join(root, date_dir)
                 rel_path = os.path.relpath(full_path, start=WORKSPACE_DIR)
                 files.append({"name": rel_path, "path": rel_path})
                 
             # Add YAML files
             for filename in filenames:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, start=WORKSPACE_DIR)
                    files.append({"name": rel_path, "path": rel_path})
        
        # Sort by name (keeping start.sh at top or bottom)
        files.sort(key=lambda x: (x["path"] != "../start.sh", x["name"]))
        return {"files": files}
    except Exception as e:
        return {"files": [], "error": str(e)}

class FileCreate(BaseModel):
    path: str
    type: str  # "file" or "folder"

@app.post("/files")
def create_item(request: FileCreate):
    try:
        print(f"Creating item: {request.path} ({request.type})")
        full_path = get_safe_path(request.path)
        if request.type == "folder":
            os.makedirs(full_path, exist_ok=True)
        else:
            parent = os.path.dirname(full_path)
            os.makedirs(parent, exist_ok=True)
            if not os.path.exists(full_path):
                with open(full_path, 'w') as f:
                    pass
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file")
def read_file(path: str):
    try:
        full_path = get_safe_path(path)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="File not found")
        with open(full_path, "r") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FileUpdate(BaseModel):
    path: str
    content: str

@app.put("/file")
def update_file(request: FileUpdate):
    try:
        print(f"Updating file: {request.path}")
        full_path = get_safe_path(request.path)
        with open(full_path, "w") as f:
            f.write(request.content)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class FileMove(BaseModel):
    old_path: str
    new_path: str

@app.patch("/file")
def move_file(request: FileMove):
    try:
        old_full = get_safe_path(request.old_path)
        new_full = get_safe_path(request.new_path)
        
        if not os.path.exists(old_full):
            raise HTTPException(status_code=404, detail="Source file not found")
        if os.path.exists(new_full):
             raise HTTPException(status_code=400, detail="Destination already exists")
             
        os.rename(old_full, new_full)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/file")
def delete_file(path: str):
    try:
        full_path = get_safe_path(path)
        if not os.path.exists(full_path):
             raise HTTPException(status_code=404, detail="Item not found")
        
        if os.path.isdir(full_path):
            import shutil
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hierarchy")
def get_hierarchy():
    try:
        # Use the improved hierarchy logic from runner.py
        # This handles native ADB dump + normalization to Maestro format
        data = runner.get_hierarchy()
        if data:
            return {"output": json.dumps(data)}
        return {"output": "{\"children\":[]}", "error": "Failed to fetch hierarchy"}
    except Exception as e:
        print(f"Hierarchy exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/device_info")
def get_device_info():
    try:
        # Get screen resolution
        res_proc = subprocess.run(["adb", "shell", "wm", "size"], capture_output=True, text=True)
        # Get screen density
        den_proc = subprocess.run(["adb", "shell", "wm", "density"], capture_output=True, text=True)
        
        # Get device model
        model_proc = subprocess.run(["adb", "shell", "getprop", "ro.product.model"], capture_output=True, text=True)
        
        # Parse resolution smartly
        res_out = res_proc.stdout.strip()
        import re
        size_val = res_out
        
        # Check Override first
        m_over = re.search(r"Override size:\s*(\d+x\d+)", res_out)
        if m_over:
            size_val = m_over.group(1)
        else:
             m_phys = re.search(r"Physical size:\s*(\d+x\d+)", res_out)
             if m_phys:
                 size_val = m_phys.group(1)
        
        return {
            "size": size_val,
            "density": den_proc.stdout.strip(),
            "model": model_proc.stdout.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Screen Mirroring ---

@app.get("/screenshot")
def get_screenshot():
    # Capture screenshot via adb and return as image/png
    
    # Method 1: exec-out (Fastest)
    try:
        result = subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True, timeout=3)
        if result.returncode == 0 and len(result.stdout) > 1000 and result.stdout.startswith(b'\x89PNG'):
             return Response(content=result.stdout, media_type="image/png")
    except Exception as e:
        print(f"[SCREENSHOT] Method 1 failed: {e}")

    # Method 2: shell screencap -p (Direct Stream)
    try:
        shell_res = subprocess.run(["adb", "shell", "screencap", "-p"], capture_output=True, timeout=5)
        if shell_res.returncode == 0 and len(shell_res.stdout) > 1000 and shell_res.stdout.startswith(b'\x89PNG'):
             return Response(content=shell_res.stdout, media_type="image/png")
    except Exception as e:
        print(f"[SCREENSHOT] Method 2 failed: {e}")

    # Method 3: File-based Fallback (Most robust)
    try:
        print("[SCREENSHOT] Using file-based fallback...")
        subprocess.run(["adb", "shell", "screencap", "-p", "/data/local/tmp/ratl_screen.png"], check=True, timeout=7)
        cat_res = subprocess.run(["adb", "exec-out", "cat", "/data/local/tmp/ratl_screen.png"], capture_output=True, timeout=5)
        
        if cat_res.returncode == 0 and len(cat_res.stdout) > 100:
             return Response(content=cat_res.stdout, media_type="image/png")
    except Exception as e:
        print(f"[SCREENSHOT] Method 3 failed: {e}")
            
    # If all failed
    raise HTTPException(status_code=503, detail="Screenshot failed with all methods")
            


# --- Terminal (Stateful & Streaming) ---

# Global TERMINAL_CWD to maintain state between requests
# We force it to the project root (one level up from the backend folder)
TERMINAL_CWD = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@app.post("/terminal")
async def terminal_command(request: TerminalRequest):
    global TERMINAL_CWD
    
    # Ensure it's initialized (safety check)
    if 'TERMINAL_CWD' not in globals() or not TERMINAL_CWD:
        TERMINAL_CWD = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    cmd = request.command.strip()
    if not cmd:
        return {"output": "", "exit_code": 0, "cwd": TERMINAL_CWD}

    # Handle 'cd' separately to maintain state
    if cmd.startswith("cd "):
        target = cmd[3:].strip()
        if not target or target == "~":
            target = os.path.expanduser("~")
        
        # Resolve target path
        new_path = os.path.abspath(os.path.join(TERMINAL_CWD, target))
        if os.path.isdir(new_path):
            TERMINAL_CWD = new_path
            return {"output": f"Changed directory to {TERMINAL_CWD}", "exit_code": 0, "cwd": TERMINAL_CWD}
        else:
            return {"output": f"cd: no such file or directory: {target}", "exit_code": 1, "cwd": TERMINAL_CWD}

    async def run_command_stream(command):
        global TERMINAL_CWD
        try:
            # Smart Path Handling: If user types 'script.sh' and it exists in CWD, prepend './'
            parts = command.split()
            if parts and not parts[0].startswith("./") and not parts[0].startswith("/") and not parts[0].startswith(".."):
                script_path = os.path.join(TERMINAL_CWD, parts[0])
                if os.path.isfile(script_path) and os.access(script_path, os.X_OK):
                    command = "./" + command
                    yield f"data: [INFO] Automatically prepended './' for local executable\n\n"

            # Use shell to support scripts, piping, etc.
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=TERMINAL_CWD,
                bufsize=1,
                universal_newlines=True
            )

            # Read output line by line and yield it
            for line in process.stdout:
                # Remove trailing newline as frontend addLog adds its own or handles lines
                # But keep internal structure
                yield f"data: {line.rstrip()}\n\n"
            
            process.wait()
            yield f"data: [DONE] EXIT_CODE: {process.returncode}\n\n"
            yield f"data: [CWD] {TERMINAL_CWD}\n\n"
            
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(run_command_stream(cmd), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
