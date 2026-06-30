import os
import sys

config_path = os.path.join(r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot', 'config.py')
with open(config_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"templates/classic.pptx"', '"templates/power point/classic.pptx"')
content = content.replace('"templates/modern.pptx"', '"templates/modern/beige-minimalism.pptx"')
content = content.replace('"templates/power point/test.pptx"', '"templates/power point/1.pptx"')

with open(config_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated config.py')
