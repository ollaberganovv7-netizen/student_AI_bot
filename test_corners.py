with open(r"handlers\documents.py", "rb") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if b"HUJJAT" in line:
        print(f"Line {i}: {line}")
        print(f"Line {i+1}: {lines[i+1]}")
    if b"Standart" in line and b"HUJJAT" not in line:
        pass
        
for i, line in enumerate(lines):
    if b"yetishmayapti" in line.lower() or b"cheyni" in line.lower() or b"1-karta" in line.lower():
        # Maybe check around here for the bottom border
        pass
        
for i, line in enumerate(lines):
    if b"f\"" in line and b"\\n\"" in line and b"__" not in line and b"==" not in line and b"**" not in line and i > 580 and i < 620:
        print(f"Line {i}: {line}")
