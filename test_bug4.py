import os
base = r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot'
template_path = 'templates/classic.pptx'
full = os.path.join(base, template_path)
print('Path:', full)
print('Exists:', os.path.exists(full))
