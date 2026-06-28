# 🎓 Student Bot — O'quv yordamchi Telegram Bot

AI yordamida akademik materiallar yaratuvchi Telegram bot.

---

## 📦 Loyiha tuzilmasi

```
student_bot/
├── bot.py                  ← Asosiy kirish nuqtasi
├── config.py               ← Sozlamalar va narxlar
├── .env                    ← Maxfiy kalitlar
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── database/
│   ├── models.py           ← SQLAlchemy modellari
│   └── db.py               ← DB yordamchi funksiyalar
├── handlers/
│   ├── start.py            ← /start, menyu
│   ├── presentation.py     ← Taqdimot yaratish
│   ├── documents.py        ← Barcha hujjat xizmatlari
│   ├── payment.py          ← To'lov tizimi
│   └── admin.py            ← Admin panel
├── services/
│   ├── ai_service.py       ← OpenAI API
│   ├── pptx_service.py     ← PPTX yaratish
│   └── docx_service.py     ← DOCX yaratish
├── keyboards/
│   ├── main_kb.py
│   ├── presentation_kb.py
│   └── admin_kb.py
├── middlewares/
│   └── register.py         ← Auto-register middleware
└── utils/
    └── helpers.py
```

---

## ⚙️ O'rnatish va ishga tushirish

### 1. Репозиторийни klonlash

```bash
git clone <repo_url>
cd student_bot
```

### 2. Virtual muhit yaratish

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Kutubxonalar o'rnatish

```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
ADMIN_IDS=123456789,987654321
CARD_NUMBER=8600 0000 0000 0000
CARD_HOLDER=Ism Familiya
DATABASE_URL=sqlite+aiosqlite:///./student_bot.db
```

> **BOT_TOKEN** olish: [@BotFather](https://t.me/BotFather) → `/newbot`  
> **OPENAI_API_KEY** olish: [platform.openai.com](https://platform.openai.com)  
> **ADMIN_IDS**: o'z Telegram ID'ingiz ([@userinfobot](https://t.me/userinfobot) orqali bilib olish mumkin)

### 5. Botni ishga tushirish

```bash
python bot.py
```

---

## 🐳 Docker orqali ishga tushirish

```bash
# Image qurish va ishga tushirish
docker-compose up -d --build

# Loglarni ko'rish
docker-compose logs -f

# To'xtatish
docker-compose down
```

---

## 💰 Narxlarni o'zgartirish

`config.py` faylida `PRICING` lug'atini tahrirlang:

```python
PRICING = {
    "presentation_10": 3000,   # 10 ta slaydli taqdimot
    "presentation_15": 16000,  # 15 ta slaydli taqdimot
    "essay": 5000,
    "article": 5000,
    "report": 8000,
    "thesis": 8000,
    "resume": 5000,
    "glossary": 4000,
    "tech_map": 6000,
    "coursework": 12000,
    "keys": 4000,
}
```

---

## 🛡️ Admin panel

Botda `/admin` buyrug'ini yuboring (faqat ADMIN_IDS ro'yxatidagi foydalanuvchilar uchun).

**Admin imkoniyatlari:**
- 💳 Kutayotgan to'lovlarni ko'rish va tasdiqlash/rad etish
- 📊 Statistikani ko'rish
- 📢 Barcha foydalanuvchilarga xabar yuborish
- 💰 Narxlarni ko'rish
- 📋 So'nggi so'rovlarni ko'rish

---

## 🔄 Foydalanuvchi yo'li

### Taqdimot:
1. `/start` → Asosiy menyu
2. 📊 Taqdimot yaratish
3. Til tanlash (O'zbek / Rus / Ingliz)
4. Slayd soni (10 yoki 15)
5. Dizayn uslubi (Klassik / Zamonaviy)
6. Mavzu kiritish
7. ✅ PPTX fayl yuboriladi

### Hujjatlar (Referat, Kurs ishi va h.k.):
1. Xizmatni tanlash
2. Mavzuni kiritish
3. Qo'shimcha ma'lumot (ixtiyoriy) yoki `/skip`
4. ✅ DOCX fayl yuboriladi

### To'lov:
1. 💳 To'lov qilish → Paket tanlash
2. Ko'rsatilgan karta raqamiga o'tkazish
3. 📸 Chek rasmini yuborish
4. Admin tasdiqlagach → Premium aktivlashadi ✅

---

## 📊 Ma'lumotlar bazasi sxemasi

### `users`
| Ustun | Turi | Ta'rif |
|-------|------|--------|
| id | BIGINT PK | Telegram user ID |
| username | TEXT | @username |
| full_name | TEXT | To'liq ism |
| free_used | BOOLEAN | Bepul sinov ishlatildimi |
| is_premium | BOOLEAN | Premium faolmi |
| premium_expires | DATETIME | Premium tugash sanasi |
| created_at | DATETIME | Ro'yxatdan o'tish sanasi |

### `payments`
| Ustun | Turi | Ta'rif |
|-------|------|--------|
| id | INT PK | Auto-increment |
| user_id | BIGINT FK | Foydalanuvchi ID |
| amount | INT | Summa (UZS) |
| package | TEXT | Paket nomi |
| screenshot_file_id | TEXT | Telegram fayl ID |
| status | TEXT | pending/approved/rejected |
| created_at | DATETIME | Yuborilgan sana |

### `requests`
| Ustun | Turi | Ta'rif |
|-------|------|--------|
| id | INT PK | Auto-increment |
| user_id | BIGINT FK | Foydalanuvchi ID |
| service_type | TEXT | presentation/essay/... |
| topic | TEXT | Mavzu |
| options | JSON | Qo'shimcha parametrlar |
| created_at | DATETIME | So'rov sanasi |

---

## 🚀 Production uchun maslahatlar

1. **PostgreSQL** ishlatish: `DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname`
2. **Redis** saqlash: `MemoryStorage` o'rniga `RedisStorage` ishlatish
3. **Webhook** rejimida ishlatish (polling o'rniga) — tezroq va samarali
4. **Systemd** xizmati sifatida ro'yxatga olish

```ini
# /etc/systemd/system/student_bot.service
[Unit]
Description=Student Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/student_bot
ExecStart=/home/ubuntu/student_bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable student_bot
sudo systemctl start student_bot
sudo systemctl status student_bot
```

---

## 📞 Texnik yordam

Bot ishlab chiqildi: **AI Student Bot Team**  
Savol va muammolar uchun admin bilan bog'laning.
