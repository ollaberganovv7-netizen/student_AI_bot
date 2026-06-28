import os
import glob
import re

def fix_mojibake_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find potential mojibake words:
    # Most UTF-8 emojis when decoded as CP1251 consist of characters like:
    # р, џ, в, п, ё, Џ, ”, Ђ, љ, Њ, Ќ, Ћ, Џ, etc.
    # We will look for sequences of characters that are entirely within the CP1251 upper range (0x80 - 0xFF)
    # Actually, let's just find any sequence of characters where each char's ord() is > 127
    # Wait, some CP1251 characters map to normal characters like ' (quote) or spaces.
    
    # A safer approach: Look for literal known mojibake substrings.
    # But since there are many, let's write a regex that matches 2 or more characters 
    # where at least one is a Cyrillic letter or specific CP1251 symbol commonly seen in emojis.
    
    # Let's collect ALL unique non-ASCII characters currently in the file.
    # If a sequence of non-ASCII characters can be encoded to cp1251 and decoded to utf-8 successfully,
    # and the result is an emoji or symbol, we replace it!
    
    def replacer(match):
        s = match.group(0)
        try:
            # Try to reverse the CP1251 mojibake
            raw_bytes = s.encode("cp1251")
            recovered = raw_bytes.decode("utf-8")
            # If it decodes successfully to something shorter (like 1-2 emojis), it's likely mojibake
            if len(recovered) < len(s):
                return recovered
        except:
            pass
        return s

    # Pattern: match sequences of 2 or more characters that are NOT basic ASCII
    # (i.e., characters with ord > 127)
    pattern = re.compile(r'[^\x00-\x7F]{2,}')
    
    new_content = pattern.sub(replacer, content)
    
    # Also, we have "™пёЏ" in the screenshot. 
    # "™" is U+2122, which is 0x99 in CP1251. 
    # "п" is U+043F, which is 0xEF in CP1251.
    # "ё" is U+0451, which is 0xB8 in CP1251.
    # "Џ" is U+040F, which is 0x8F in CP1251.
    # Let's ensure our regex catches "™пёЏ". ™ is > 127, so it will!

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed mojibake dynamically in {filepath}")

for folder in ["handlers", "keyboards", "services", "utils"]:
    for filepath in glob.glob(f"{folder}/*.py"):
        fix_mojibake_in_file(filepath)
        
print("Mojibake auto-fix complete.")
