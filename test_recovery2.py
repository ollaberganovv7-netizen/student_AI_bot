import os

filepath = r"handlers\documents.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

try:
    # Reverse the corruption: 
    # 1. encode to cp1251 to get back the raw bytes that PowerShell read
    # 2. decode as utf-8 to get the real strings
    raw_bytes = content.encode("cp1251")
    recovered = raw_bytes.decode("utf-8")
    
    with open("handlers\documents_recovered.py", "w", encoding="utf-8") as f:
        f.write(recovered)
    print("Successfully recovered documents.py!")
except Exception as e:
    print(f"Failed: {e}")
