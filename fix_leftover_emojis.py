import glob

replacements = {
    "⚠️\xa0пёЏ": "⚠️",
    "⚠️™пёЏ": "⚙️",
    "⚠️\u00a0пёЏ": "⚠️", # Just in case
}

for filepath in glob.glob("handlers/*.py") + glob.glob("keyboards/*.py"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    original = content
    for bad, good in replacements.items():
        content = content.replace(bad, good)
        
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed leftover emojis in {filepath}")
