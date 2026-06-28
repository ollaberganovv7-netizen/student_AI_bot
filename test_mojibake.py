with open(r"handlers\documents.py", "r", encoding="utf-8") as f:
    content = f.read()

print("Is 'в”Ђ' in content?", "в”Ђ" in content)
print("Is '─' in content?", "─" in content)

# Try properly reversing the cp1251 mojibake
try:
    raw_bytes = content.encode("cp1251")
    fixed = raw_bytes.decode("utf-8")
    print("CP1251 reversal successful!")
except Exception as e:
    print(f"CP1251 reversal failed: {e}")
