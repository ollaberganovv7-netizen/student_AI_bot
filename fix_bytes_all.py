import os
import glob

replacements = {
    b'\xd0\xb2\xe2\x80\x9d\xd0\x83': b'\xe2\x94\x80',  # в”Ѓ -> ─
    b'\xd0\xb2\xd0\x82\xe2\x80\x9d': b'\xe2\x80\x94',  # вЂ” -> —
    b'\xd0\xb2\xe2\x80\x9d\xd0\x82': b'\xe2\x94\x80',  # в”Ђ -> ─
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
            print(f"Fixed byte sequences in {filepath}")
