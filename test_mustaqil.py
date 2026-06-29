import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.docx_service import generate_docx_from_template

def main():
    topic = "Sun'iy intellektning ta'lim sohasidagi o'rni va kelajagi"
    subject = "Axborot texnologiyalari"
    author = "Shuhratbek Otaboyev"
    fakultet = "Kompyuter injiniringi"
    specialty = "Dasturiy injiniring"
    reviewer = "Doc. Abdullayev K."
    university = "TOSHKENT AXBOROT TEXNOLOGIYALARI UNIVERSITETI"
    
    plan = """KIRISH

I BOB. Sun'iy intellekt va ta'lim: nazariy asoslar
1.1. Sun'iy intellekt tushunchasi va uning ta'limdagi mohiyati
1.2. Xorijiy va mahalliy olimlarning sun'iy intellekt haqidagi qarashlari

II BOB. Sun'iy intellektning ta'limda qo'llanilishi: amaliy tahlil
2.1. O'zbekiston ta'lim tizimida sun'iy intellekt holati va muammolari
2.2. Sun'iy intellektni ta'limga joriy etishning samarali yo'llari

XULOSA VA TAKLIFLAR

FOYDALANILGAN ADABIYOTLAR"""

    final_text = """# KIRISH

Mustaqil ishning dolzarbligi: Bugungi kunda sun'iy intellekt ta'lim sohasiga misli ko'rilmagan o'zgarishlarni olib kirmoqda. 
Maqsadi: Oliy ta'lim talablariga mos ravishda chuqur tahlil olib borish.
Vazifalari: Muammolarni aniqlash, ularni yechish va kelajakdagi takliflarni berish.
Obyekti: O'zbekiston oliy ta'lim tizimi.

# I BOB. Sun'iy intellekt va ta'lim: nazariy asoslar

Ushbu bobda nazariy tushunchalar batafsil muhokama qilinadi. Talabaning shaxsiy yondashuvi shuni ko'rsatadiki, an'anaviy ta'lim metodlari asta-sekin o'z o'rnini gibrid texnologiyalarga bo'shatmoqda.

# 1.1. Sun'iy intellekt tushunchasi va uning ta'limdagi mohiyati

1-matn qismi bu yerda yoziladi.
2-matn qismi bu yerda yoziladi.

# 1.2. Xorijiy va mahalliy olimlarning sun'iy intellekt haqidagi qarashlari

[1] manbada ta'kidlanishicha, ta'lim muassasalarining 40% dan ortig'i kelasi 5 yilda AI elementlarini qo'shadi.

# II BOB. Sun'iy intellektning ta'limda qo'llanilishi: amaliy tahlil

Amaliy qism. O'zbekistonda xususan oxirgi 3 yilda...

# 2.1. O'zbekiston ta'lim tizimida sun'iy intellekt holati va muammolari

Tahlillar va statistikalar.

# 2.2. Sun'iy intellektni ta'limga joriy etishning samarali yo'llari

| Yechim turi | Kutilayotgan natija | Muddat |
|-------------|---------------------|--------|
| Infratuzilma | Maktablarda smart doskalar | 2 yil |
| Kadrlarni qayta tayyorlash | O'qituvchilarning AI savodxonligi | 1 yil |

# XULOSA VA TAKLIFLAR

Xulosa shuki, biz orqada qolmasligimiz kerak.
Takliflar: 
1. Maxsus platformalar yaratish.
2. Dasturlarni milliy tilga moslashtirish.

# FOYDALANILGAN ADABIYOTLAR RO'YXATI

[1] Karimov A.K. Ta'limda innovatsiyalar. — T.: Fan, 2023. — 250 b.
[2] Samuelson P. AI in Modern Schooling. — Cambridge, 2024. — 300 p.
[3] Xo'jayev N.R. Raqamli pedagogika. — T.: Sharq, 2022. — 180 b.
"""

    print("Generating DOCX...")
    docx_bytes = generate_docx_from_template(
        topic=topic,
        content=final_text,
        author=author,
        plan=plan,
        subject=subject,
        reviewer=reviewer,
        university=university,
        fakultet=fakultet,
        specialty=specialty,
        doc_type="mustaqil",
        num_pages=15
    )
    
    save_path = r"C:\Users\Шухрат\Desktop\Mustaqil_ish_Namuna.docx"
    with open(save_path, "wb") as f:
        f.write(docx_bytes)
        
    print(f"Done! File saved as {save_path}")

if __name__ == "__main__":
    main()
