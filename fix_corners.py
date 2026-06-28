import os
import glob

replacements = {
    b'\xd0\xb2\xe2\x80\x9d\xd0\x8a': b'\xe2\x94\x8c',  # в”Њ -> ┌
    b'\xd0\xb2\xe2\x80\x9d\xd1\x92': b'\xe2\x94\x90',  # в”ђ -> ┐
    b'\xd0\xb2\xe2\x80\x9d\xe2\x80\x9d': b'\xe2\x94\x94',  # в”” -> └
    b'\xd0\xb2\xe2\x80\x9d\xc2\x98': b'\xe2\x94\x98',  # в” -> ┘
}

for folder in ["handlers", "keyboards"]:
    for filepath in glob.glob(f"{folder}/*.py"):
        with open(filepath, "rb") as f:
            content = f.read()
        
        original_content = content
        for bad, good in replacements.items():
            content = content.replace(bad, good)
            
        if content != original_content:
            with open(filepath, "wb") as f:
                f.write(content)
            print(f"Fixed corner byte sequences in {filepath}")
