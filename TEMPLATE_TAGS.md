# 🏷️ Shablon Belgilari (Template Tags)

Bot endi shablonlardagi `{{tag}}` belgilari orqali matnni aniq joyiga qo'yadi.
Bu sizga internetdan **istalgan PPTX shablonni** yuklab, qo'lda belgilab,
botda ishlatish imkonini beradi.

## ✨ Nima uchun teglar kerak?

**Tegsiz** (eski usul):
- AI taxminan tushunadi qaysi blok title, qaysi body
- Lorem ipsum, "ЗАГОЛОВОК" matnlari shaklan qoladi
- Ba'zi bloklar bo'sh qoladi

**Teglar bilan** (yangi usul):
- ✅ 100% aniq joyga matn tushadi
- ✅ Lorem ipsum o'rniga real matn
- ✅ Suv belgilari (`{{remove}}`) o'chiriladi
- ✅ Bir nechta matn bloklari aniq farqlanadi (`{{body_1}}`, `{{body_2}}`)

## 🎯 Mavjud teglar

### Asosiy:
| Teg | Vazifasi |
|---|---|
| `{{title}}` | Slayd sarlavhasi |
| `{{subtitle}}` | Pastki sarlavha (titul slaydda) |
| `{{author}}` | Muallif ismi |
| `{{topic}}` | Taqdimot mavzusi (titulda) |
| `{{date}}` | Bugungi sana |

### Matn bloklari:
| Teg | Vazifasi |
|---|---|
| `{{body}}` | Asosiy matn (yagona blok) |
| `{{body_1}}` | 1-blok matn (bir nechta blok bo'lganda) |
| `{{body_2}}` | 2-blok matn |
| `{{body_3}}` | 3-blok matn |
| `{{point_1}}` | 1-punkt sarlavhasi (infografika uchun) |
| `{{point_2}}` | 2-punkt sarlavhasi |

### Maxsus:
| Teg | Vazifasi |
|---|---|
| `{{image}}` | Rasm uchun joy |
| `{{image_1}}`, `{{image_2}}` | Bir nechta rasm |
| `{{remove}}` | **Bu shape'ni butunlay o'chirish** (suv belgilari!) |

## 📝 Qanday belgilash kerak

### Qadam 1: Shablon yuklab oling
- [Slidesgo.com](https://slidesgo.com/) — bepul, sifatli
- [Slidescarnival.com](https://www.slidescarnival.com/) — bepul
- [presentation-creation.ru](https://presentation-creation.ru) — bepul ru/en

### Qadam 2: PowerPoint / Keynote'da oching
PPTX faylni 2 marta bosib oching.

### Qadam 3: Har slaydda matnni belgilang

**Misol 1: Titul slayd**
```
[Sarlavha bloki]:    "Your Title Here"   →  Yozish: {{title}}
[Pastki sarlavha]:   "Subtitle"          →  Yozish: {{subtitle}}
[Muallif]:           "John Smith"        →  Yozish: {{author}}
```

**Misol 2: Reja / Mundarija**
```
[Sarlavha]:  "Reja"           →  Yozish: Reja  (statik, qoldiring)
[Ro'yxat]:   "1. Lorem..."    →  Yozish: {{body}}
```

**Misol 3: Inson tanasi (matn + rasm)**
```
[Sarlavha]:        "Lorem ipsum..."     →  Yozish: {{title}}
[Asosiy matn]:     "Body text..."       →  Yozish: {{body}}
[Rasm joyi]:       (image placeholder)  →  Yozish: {{image}}
```

**Misol 4: 4 ta qadam (infografika)**
```
[Sarlavha]:        "Title Here"     →  Yozish: {{title}}
[1-qadam nomi]:    "ШАГ 1"          →  Yozish: {{point_1}}
[1-qadam matni]:   "Lorem ipsum..."  →  Yozish: {{body_1}}
[2-qadam nomi]:    "ШАГ 2"          →  Yozish: {{point_2}}
[2-qadam matni]:   "Lorem ipsum..."  →  Yozish: {{body_2}}
[3-qadam nomi]:    "ШАГ 3"          →  Yozish: {{point_3}}
[3-qadam matni]:   "Lorem ipsum..."  →  Yozish: {{body_3}}
[4-qadam nomi]:    "ШАГ 4"          →  Yozish: {{point_4}}
[4-qadam matni]:   "Lorem ipsum..."  →  Yozish: {{body_4}}
```

**Misol 5: Suv belgilarini o'chirish** ⭐
```
[Footer]: "Шаблоны презентаций с сайта presentation-creation.ru"
   →  Yozish: {{remove}}
```
**E'tibor:** `{{remove}}` yozilgan shape **butunlay o'chiriladi**!

### Qadam 4: Saqlash va joylashtirish

1. PPTX'ni saqlang
2. Faylni `templates/{Kategoriya}/` papkasiga ko'chiring
   - Masalan: `templates/Medicine/anatomy.pptx`
3. Slayd preview rasmini tayyorlang (PowerPoint'dan eksport qiling)
4. PNG'ni `webapp/static/previews/{Kategoriya}/` papkasiga ko'ching
   - Bir xil nom: `templates/Medicine/anatomy.pptx` → `webapp/static/previews/Medicine/anatomy.png`
5. JSON'ni yangilang:
   ```bash
   python3 scripts/sync_templates.py
   ```
6. WebApp'ni Vercel'ga push qiling:
   ```bash
   cd webapp && git add . && git commit -m "Add new template" && git push
   ```

## ⏱️ Qancha vaqt ketadi?

| Shablon murakkabligi | Vaqt |
|---|---|
| Oddiy (5-7 slayd) | 2-3 daqiqa |
| O'rtacha (10-12 slayd) | 5-7 daqiqa |
| Murakkab (20+ slayd, infografika) | 10-15 daqiqa |

## 🚨 Diqqat:

1. **Belgi yagona shape'da bo'lsin:** `{{title}}` deb yozsangiz, shape'da BOSHQA matn qolmasin (oldingi matnni butunlay o'chiring).

2. **Statik matn qoldirishingiz mumkin:** Agar slaydda "Reja" yoki "Xulosa" so'zi statik bo'lsa va o'zgarmasligi kerak bo'lsa — teg qo'ymang, faqat statik matn qoldiring.

3. **`{{remove}}` ehtiyot bo'lib ishlating:** U shape'ni BUTUNLAY yo'q qiladi. Faqat suv belgilari, kreditlar uchun.

4. **Tegsiz shablonlar ham ishlaydi:** Eski shablonlaringiz buzilmaydi — bot avtomatik aniqlash rejimida (eski usul) ishlaydi.

5. **Aralash ham mumkin:** Bitta shablonda ba'zi shape'lar tegli, ba'zilari tegsiz bo'lishi mumkin. Tegli — aniq, tegsiz — heuristic.

## 📚 Yana misollar

### O'rtacha murakkablikdagi anatomiya shabloni:

```
─── Slayd 1 (Titul) ──────────────────
Sarlavha:        {{title}}
Pastki:          {{subtitle}}
Footer logo:     {{remove}}

─── Slayd 2 (Reja) ───────────────────
Sarlavha:        "Reja"  (statik)
Ro'yxat:         {{body}}
Footer:          {{remove}}

─── Slayd 3 (Kirish) ─────────────────
Sarlavha:        "Kirish"  (statik)
Asosiy matn:     {{body}}
Footer:          {{remove}}

─── Slayd 4 (Anatomiya 1) ────────────
Sarlavha:        {{title}}
Chap matn:       {{body_1}}
Rasm joyi:       {{image}}
Footer:          {{remove}}

─── Slayd 5 (Anatomiya 2) ────────────
Sarlavha:        {{title}}
1-blok:          {{body_1}}
2-blok:          {{body_2}}
3-blok:          {{body_3}}
Cifra "1":       {{remove}}  (yoki {{point_1}})
Cifra "2":       {{remove}}
Cifra "3":       {{remove}}
Footer:          {{remove}}

─── Slayd 6 (Xulosa) ─────────────────
Sarlavha:        "Xulosa"  (statik)
Asosiy matn:     {{body}}
Footer:          {{remove}}
```

## ❓ Muammolar

**Matn ishlamayapti?**
- `{{tag}}` ichida BO'SH joy bo'lmasin: `{{title}}` ✅, `{{ title }}` ❌
- Yagona shape ichida bo'lsin (eski matn qoldirmang)
- `python3 scripts/sync_templates.py` ni qaytadan ishga tushiring

**Rasm o'rnatilmayapti?**
- `{{image}}` faqat **picture placeholder** ichida ishlaydi
- Oddiy text frame'ga `{{image}}` yozish ishlamaydi

**Bot tayyorlagan PPTX'da hali ham Lorem ipsum bor?**
- Shu shape'ga teg qo'shilmagan, demak. Belgilang!
