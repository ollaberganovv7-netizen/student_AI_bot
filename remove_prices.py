import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

replacements = [
    (' <i>PPTX</i>  ─  <code>{pres_price}+</code>', ''),
    (' <i>DOCX</i>  ─  <code>{essay_price}+</code>', ''),
    ('  ─  <code>{must_price}+</code>', ''),
    ('  ─  <code>{kurs_price}+</code>', ''),
    ('  ─  <code>{quiz_price}+</code>', ''),
    ('  ─  <code>{diplom_price}+</code>', '')
]

for old, new in replacements:
    content = content.replace(old, new)

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Removed prices and extensions from welcome message in i18n.py")
