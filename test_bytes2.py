with open(r"handlers\documents.py", "rb") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if b"Narx:" in line:
        print(f"Line {i}: {line}")
        print(f"Line {i-1}: {lines[i-1]}")
        print(f"Line {i+1}: {lines[i+1]}")
        break
