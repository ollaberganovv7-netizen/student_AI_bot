import codecs

with codecs.open('handlers/admin.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Tabriklaymiz! To'lovingiz tasdiqlandi" in line:
        lines[i] = "                f\"🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi.</b>\\n\\n\"\n"
    elif "Balansingizga <b>{payment.amount:,} so'm</b> qo'shildi" in line:
        lines[i] = "                f\"💰 Balansingizga <b>{payment.amount:,} so'm</b> qo'shildi.\\n\\n\"\n"
    elif "<b>Balansingiz yetarli!</b>" in line:
        lines[i] = "                f\"✅ <b>Balansingiz yetarli!</b>\\n\"\n"
    elif "Endi <b>" in line and "Yaratish</b> tugmasini bosing" in line:
        lines[i] = "                f\"Endi <b>✅ Yaratish</b> tugmasini bosing!\"\n"
    elif "Admin tomonidan balansingiz to'ldirildi" in line:
        lines[i] = "                    f\"🎉 <b>Tabriklaymiz! Admin tomonidan balansingiz to'ldirildi.</b>\\n\\n\"\n"
    elif "Balansingizga <b>{amount:,} so'm</b> qo'shildi" in line:
        lines[i] = "                    f\"💰 Balansingizga <b>{amount:,} so'm</b> qo'shildi.\\n\"\n"
    elif line.strip() == '"':
        # Remove empty lines left over from previous script
        lines[i] = ""

with codecs.open('handlers/admin.py', 'w', 'utf-8') as f:
    f.writelines([l for l in lines if l != "\n" or not lines[lines.index(l)-1].endswith('tasdiqlandi.</b>\n')])

