import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('            "▸ 📝 <b>Tezis / Maqola</b>  ─  <code>{tezis_price}+</code>\\n"\n', '')
content = content.replace('            "▸ 📗 <b>Uslubiy ishlanma</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"\n', '            "\\n"\n')

content = content.replace('            "▸ 📝 <b>Тезис / Статья</b>  ─  <code>{tezis_price}+</code>\\n"\n', '')
content = content.replace('            "▸ 📗 <b>Метод. пособие</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"\n', '            "\\n"\n')

content = content.replace('            "▸ 📝 <b>Thesis / Article</b>  ─  <code>{tezis_price}+</code>\\n"\n', '')
content = content.replace('            "▸ 📗 <b>Methodical guide</b>  ─  <code>{uslubiy_price}+</code>\\n\\n"\n', '            "\\n"\n')

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.write(content)

print("Removed lines successfully")
