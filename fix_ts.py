import os
import sys

path = os.path.join(r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot', 'services', 'pptx_service.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('_smart_classify_textboxes(shapes["other"], ts)', '_smart_classify_textboxes(shapes["other"], title_slide)')
content = content.replace('_add_image(ts, slide_images[0], prs, "center")', '_add_image(title_slide, slide_images[0], prs, "center")')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed ts -> title_slide in pptx_service.py')
