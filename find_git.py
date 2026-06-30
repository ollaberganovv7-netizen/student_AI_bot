import os
import subprocess

def find_git():
    for root, dirs, files in os.walk('C:\\'):
        if 'git.exe' in files:
            path = os.path.join(root, 'git.exe')
            if 'cmd' in path.lower() or 'bin' in path.lower():
                return path
    return None

git_path = find_git()
if git_path:
    print(f"FOUND: {git_path}")
else:
    print("NOT_FOUND")
