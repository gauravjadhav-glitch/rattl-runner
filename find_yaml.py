
import os

target = "AddremoveCart.yaml"
search_root = "/Users/kalyanibadgujar/maestro-runner"
print(f"Searching for {target} in {search_root}...")

found = False
for root, dirs, files in os.walk(search_root):
    if target in files:
        print(f"FOUND: {os.path.join(root, target)}")
        found = True

if not found:
    print("File not found in the specified directory tree.")
    # Print a few found files to verify visibility
    print("\nSample files found:")
    count = 0
    for root, dirs, files in os.walk(search_root):
        for f in files:
            print(os.path.join(root, f))
            count += 1
            if count > 10: break
        if count > 10: break
