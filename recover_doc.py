import os

filepath = r"handlers\documents.py"
with open(filepath, "r", encoding="utf-8") as f:
    s = f.read()

recovered = s[1::2]

with open(filepath, "w", encoding="utf-8") as f:
    f.write(recovered)
print(f"Recovered {filepath}!")
