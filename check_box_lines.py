import glob

for folder in ["handlers", "keyboards"]:
    for filepath in glob.glob(f"{folder}/*.py"):
        with open(filepath, "rb") as f:
            content = f.read()
        
        # Look for \xd0\xb2\xe2\x80\x9d which corresponds to "в”"
        if b"\xd0\xb2\xe2\x80\x9d" in content:
            print(f"Found 'в”' in {filepath}!")
