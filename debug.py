import codecs

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    lines = f.readlines()

print(repr(''.join(lines[592:602])))
