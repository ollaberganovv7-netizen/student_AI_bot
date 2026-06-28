import os

filepath = r"handlers\documents.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

try:
    content = content.lstrip('\ufeff')
    raw_bytes = content.encode("cp1251", errors="ignore")
    recovered = raw_bytes.decode("utf-8")
    
    with open(r"handlers\documents_recovered.py", "w", encoding="utf-8") as f:
        f.write(recovered)
    print("Successfully recovered documents.py!")
except Exception as e:
    print(f"Failed: {e}")
