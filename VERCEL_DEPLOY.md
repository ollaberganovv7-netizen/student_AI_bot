# 🚀 Vercel Deploy Guide

WebApp'ni GitHub Pages'dan Vercel'ga ko'chirish bo'yicha qo'llanma.

## 1️⃣ Vercel'ga ro'yxatdan o'tish

1. https://vercel.com/signup ga o'ting
2. **Continue with GitHub** ni bosing
3. Ruxsat bering — Vercel sizning repo'laringizga kirishi kerak

## 2️⃣ Loyihani import qilish

1. Dashboard → **Add New → Project**
2. Repo'ni tanlang: `student_bot`
3. **Configure Project** sahifasi:

```
Framework Preset:    Other
Root Directory:      webapp        ← MUHIM!
Build Command:       (bo'sh qoldiring)
Output Directory:    .              ← bitta nuqta
Install Command:     (bo'sh qoldiring)
```

4. **Deploy** ni bosing → 10 soniya kuting

## 3️⃣ URL'ni nusxa olish

Deploy tugagach, URL beradi, masalan:
```
https://student-bot-webapp.vercel.app
```

Yoki:
```
https://student-bot-arslon.vercel.app
```

## 4️⃣ `.env` faylga qo'shish

Loyiha papkasidagi `.env` faylga yozing (yoki almashtiring):

```bash
# Eski qiymatni almashtiring
WEBAPP_URL=https://student-bot-webapp.vercel.app/
```

⚠️ **MUHIM:** URL oxirida `/` bo'lishi shart!

## 5️⃣ Bot'ni qayta ishga tushirish

```bash
python3 bot.py
```

WebApp endi Vercel'dan yuklanadi.

## 6️⃣ Keyingi o'zgarishlar

Endi WebApp'da bironta o'zgartirish kiritsangiz:

```bash
git add webapp/
git commit -m "Update webapp"
git push
```

✅ **10 soniyada Vercel avtomatik yangilaydi!** Bot'ni qayta ishga tushirish kerak emas.

## 🎯 Qo'shimcha (ixtiyoriy)

### Custom domain qo'shish

Vercel'da:
1. Project → Settings → Domains
2. Domain qo'shing: `webapp.arslon.uz` (sotib olingan domain)
3. DNS sozlamalarini Vercel ko'rsatadi

### Preview deployments

Har bir branch yoki PR uchun alohida URL beradi.
Yangi feature'ni test qilish oson:
```bash
git checkout -b new-feature
# o'zgartirishlar...
git push origin new-feature
```
Vercel beradi: `student-bot-webapp-git-new-feature.vercel.app`

### Tezroq deploy

`vercel.json` allaqachon webapp/ ichida qo'shilgan — keshlash va headerlar to'g'ri sozlangan.

## ❓ Muammolar

**WebApp ochilmaydi?**
- `.env` fayldagi URL oxirida `/` borligini tekshiring
- Bot'ni qayta ishga tushiring
- URL'ni brauzerda ochib tekshiring (Vercel beradigan link)

**404 xatolik?**
- Root Directory'ni `webapp` deb belgilaganingizni tekshiring (ildiz emas!)

**SSL muammosi?**
- Vercel avtomatik HTTPS beradi — qo'shimcha sozlash kerak emas
