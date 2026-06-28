import glob

def find_leftovers():
    for filepath in glob.glob("handlers/*.py") + glob.glob("keyboards/*.py"):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # We know that \u26a0\ufe0f\u2122\u043f\u0451\u040f is the literal string "⚠️™пёЏ"
        # and \u26a0\u043f\u0451\u040f is the literal string "⚠️пёЏ"
        
        if "⚠️™пёЏ" in content or "⚠️пёЏ" in content:
            print(f"Found in {filepath}")

find_leftovers()
