import os, sys
sys.path.append(r'C:\Users\Шухрат\Desktop\Новая папка\student_AI_bot')
import services.pptx_service as p
print('File:', p.__file__)
base = os.path.dirname(os.path.dirname(os.path.abspath(p.__file__)))
print('Base:', base)
