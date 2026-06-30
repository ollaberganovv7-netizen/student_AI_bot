import os
template_path = r'templates\classic.pptx'
print('Exists cwd:', os.path.exists(os.path.join(os.getcwd(), template_path)))
