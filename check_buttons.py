import codecs
with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '"buttons": {' in line:
        for j in range(i, i+30):
            print(lines[j].strip())
        break
