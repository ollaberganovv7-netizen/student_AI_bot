with open(r"handlers\documents.py", "r", encoding="utf-8") as f:
    s = f.read()

# Let's see the first 40 characters
print("Original:")
print(repr(s[:40]))

# Try taking every second character starting from index 1
recovered = s[1::2]
print("Recovered:")
print(repr(recovered[:20]))
