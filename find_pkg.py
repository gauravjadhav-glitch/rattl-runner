
import os

target = "package.json"
search_root = "/Users/kalyanibadgujar/maestro-runner/maestro-runner"
print(f"Searching for {target} in {search_root}...")

found = False
for root, dirs, files in os.walk(search_root):
    if target in files:
        print(f"FOUND: {os.path.join(root, target)}")
        found = True

if not found:
    print("package.json not found in the project.")
