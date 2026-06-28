import os

filepaths = [r"handlers\documents.py", r"handlers\presentation.py"]

replacements = {
    "рџ“љ": "📚",
    "рџ“„": "📄",
    "вњ…": "✅",
    "рџљЂ": "🚀",
    "вќЊ": "❌",
    "вЌЊ": "❌",
    "вљ": "⚠️",
    "в”Ђ": "─",
    "рџ’°": "💰",
    "рџ“ќ": "📝",
    "рџ“‚": "📂",
    "рџ”Ќ": "🔍",
    "рџ“·": "📷",
    "вќ“": "❓",
    "рџ“€": "📜",
    "рџЊђ": "🌐",
    "рџ’і": "💳",
    "г…¤": " ",
    "Р РµС„РµСЂР°С‚": "Referat"
}

for filepath in filepaths:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    for bad, good in replacements.items():
        content = content.replace(bad, good)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Fixed emojis properly in {filepath}")
