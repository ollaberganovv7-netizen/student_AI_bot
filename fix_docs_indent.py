import codecs

with codecs.open('handlers/documents.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i in range(670, min(700, len(lines))):
    if "is_admin = db_user.id in ADMIN_IDS" in lines[i] and not lines[i].startswith("    "):
        # This is the broken block!
        lines[i-1] = "                f\"<i>Reja yoki ma'lumotlarni o'zgartirish uchun tugmalardan foydalaning.</i>\"\\n            )\\n"
        for j in range(i, i+16):
            lines[j] = ""
        print(f"Fixed broken block at line {i}!")
        break

with codecs.open('handlers/documents.py', 'w', 'utf-8') as f:
    f.writelines(lines)
