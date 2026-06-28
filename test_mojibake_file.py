with open(r"handlers\documents.py", "r", encoding="utf-8") as f:
    content = f.read()

with open("mojibake_test.txt", "w", encoding="utf-8") as f:
    f.write(f"Is 'в”Ђ' in content? {'в”Ђ' in content}\n")
    f.write(f"Is '─' in content? {'─' in content}\n")

    try:
        raw_bytes = content.encode("cp1251")
        fixed = raw_bytes.decode("utf-8")
        f.write("CP1251 reversal successful!\n")
    except Exception as e:
        f.write(f"CP1251 reversal failed: {e}\n")
