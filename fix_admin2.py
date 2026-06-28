import re
with open('handlers/admin.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'\@router\.message\(Command\(\"zero\"\)\).*?await message\.answer\(\"❌ Noto\'g\'ri ID formati\.\"\)\r?\n'

parts = re.split(pattern, text, flags=re.DOTALL)
matches = re.findall(pattern, text, flags=re.DOTALL)

if len(parts) > 1:
    new_text = parts[0] + matches[0] + '    )\n\n'.join(parts[1:])
    with open('handlers/admin.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print('Fixed with regex!')
else:
    print('Not found')
