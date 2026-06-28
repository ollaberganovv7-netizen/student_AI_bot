import glob

def find_leftovers():
    for filepath in glob.glob("handlers/*.py") + glob.glob("keyboards/*.py"):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        import re
        matches = set(re.findall(r'.{1}пёЏ', content))
        if matches:
            print(f"In {filepath}: {matches}")

find_leftovers()
