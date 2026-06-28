import os
import glob

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original = content
    # Common broken utf-8 in win-1251
    replacements = {
        '❌': '❌',
        '❌': '❌',
        '✅': '✅',
        '⚠️': '⚠️',
        '─': '─',
        '': ''
    }
    for bad, good in replacements.items():
        content = content.replace(bad, good)
        
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filepath}")

for filepath in glob.glob('handlers/*.py'):
    fix_file(filepath)
for filepath in glob.glob('*.py'):
    fix_file(filepath)
