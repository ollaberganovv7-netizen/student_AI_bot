import os

filepath = r"handlers\documents.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's try to find a known corrupted string and recover it
test_str = "рџ“љ"
if test_str in content:
    try:
        recovered = test_str.encode("cp1251").decode("utf-8")
        print(f"Recovered: {recovered}")
    except Exception as e:
        print(f"Error recovering: {e}")
else:
    print("Test string not found.")
