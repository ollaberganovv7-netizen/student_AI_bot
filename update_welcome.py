import codecs

with codecs.open('utils/i18n.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "🎓 <b>STUDENT AI</b>" in line:
        lines[i] = "            \"       🎓 <b>STUDENT AI</b>\\n\"\n"
    elif "<i>Akademik AI yordamchi</i>" in line:
        lines[i] = "            \"   <i>Akademik AI yordamchi</i>\\n\"\n"
    elif "<i>Академический AI ассистент</i>" in line:
        lines[i] = "            \"  <i>Академический AI ассистент</i>\\n\"\n"
    elif "<i>Academic AI Assistant</i>" in line:
        lines[i] = "            \"    <i>Academic AI Assistant</i>\\n\"\n"
    elif "Salom, <b>{name}</b>! 👋" in line:
        lines[i] = "            \"       Salom, <b>{name}</b>! 👋\\n\\n\"\n"
    elif "Привет, <b>{name}</b>! 👋" in line:
        lines[i] = "            \"       Привет, <b>{name}</b>! 👋\\n\\n\"\n"
    elif "Hello, <b>{name}</b>! 👋" in line:
        lines[i] = "            \"       Hello, <b>{name}</b>! 👋\\n\\n\"\n"
    elif "<b>{balance}</b>" in line and "so'm" not in line:
        # Avoid replacing in 'account' block if any
        if "  <b>{balance}</b>\\n" in line or "<b>{balance}</b>" in line:
            lines[i] = "            \"         <b>{balance}</b>\\n\"\n"
    elif "Xizmatni tanlang:" in line or "Выберите услугу:" in line or "Choose a service:" in line:
        lines[i] = ""
    # remove the extra newline added because we removed the last line
    elif "└ 🔄 24/7 ishlaymiz\\n\\n\"" in line:
        lines[i] = "            \"└ 🔄 24/7 ishlaymiz\\n\"\n"
    elif "└ 🔄 Работаем 24/7\\n\\n\"" in line:
        lines[i] = "            \"└ 🔄 Работаем 24/7\\n\"\n"
    elif "└ 🔄 Available 24/7\\n\\n\"" in line:
        lines[i] = "            \"└ 🔄 Available 24/7\\n\"\n"

with codecs.open('utils/i18n.py', 'w', 'utf-8') as f:
    f.writelines([l for l in lines if l != ""])

