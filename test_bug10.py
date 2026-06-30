import os
import json
with open('webapp/data/templates.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    path = data[0]['file_path']
    print('Path from JSON:', path)
    print('Exists relative:', os.path.exists(path))
