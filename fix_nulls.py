import os

filepaths = [r"handlers\documents.py", r"handlers\presentation.py"]

for filepath in filepaths:
    with open(filepath, "rb") as f:
        raw = f.read()
    
    # Check if it looks like UTF-16 (every other byte is 0)
    # If the file is 103KB, it has \x00 bytes. We can just decode it from utf-16le!
    # Wait, if Python read it as utf-8, it would have read the \x00 as literal characters!
    # Let's decode it properly.
    if b'\x00' in raw:
        try:
            # Maybe it was saved as UTF-8 but containing literal \x00 chars
            content = raw.decode("utf-8").replace("\x00", "")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed null bytes in {filepath}")
        except Exception as e:
            print(f"Failed to fix {filepath}: {e}")
