with open(r"handlers\documents.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for i in range(35, 46):
        print(f"{i+1}: {lines[i].strip()}")
