# 🏥 MedBot UZ — Klinikalarga Telegram Navbat Tizimi

Klinikalarga Telegram bot orqali avtomatik navbat olish, eslatma yuborish va admin boshqaruvi.

---

## 📁 Loyiha tuzilmasi

```
medbot/
├── main.py                    # Asosiy fayl
├── config.py                  # Sozlamalar
├── requirements.txt           # Kutubxonalar
├── Procfile                   # Railway uchun
├── railway.toml               # Railway konfiguratsiya
├── .env.example               # Environment namuna
├── .gitignore
├── bot/
│   ├── handlers/
│   │   ├── common.py          # Start, menu handlerlari
│   │   ├── patient.py         # Navbat olish, ko'rish
│   │   └── admin.py           # Admin panel
│   ├── keyboards.py           # Tugmalar
│   └── scheduler.py           # Eslatmalar (avtomatik)
└── database/
    ├── db.py                  # Modellar, init
    └── queries.py             # Database so'rovlar
```

---

## 🚀 ISHGA TUSHIRISH (QADAMBA-QADAM)

### 1-QADAM: Telegram Botni yaratish

1. Telegramda **@BotFather** ga kiring
2. `/newbot` yuboring
3. Bot nomini kiriting: `MedCenter Navbat`
4. Username kiriting: `medcenter_navbat_bot`
5. **Token** ni nusxalab oling (ko'rinishi: `7123456789:AAHxxx...`)

---

### 2-QADAM: Sizning Telegram ID ingizni topish

1. Telegramda **@userinfobot** ga kiring
2. `/start` yuboring
3. **Id:** deb ko'rsatilgan raqamni nusxalab oling

---

### 3-QADAM: GitHub ga yuklash

```bash
# Git o'rnatilgan bo'lsa:
git init
git add .
git commit -m "first commit"

# GitHub da yangi repo yarating, keyin:
git remote add origin https://github.com/SIZNING_USERNAME/medbot.git
git push -u origin main
```

**GitHub hisobi yo'q bo'lsa:** github.com → Sign up → bepul hisob oching

---

### 4-QADAM: Railway.app da Deploy

1. **railway.app** ga kiring → **GitHub bilan kiring** (bepul)
2. **"New Project"** tugmasini bosing
3. **"Deploy from GitHub repo"** → medbot reponi tanlang
4. **"Add Variables"** bo'limiga o'ting va quyidagilarni kiriting:

```
BOT_TOKEN          = 7123456789:AAHxxx_sizning_tokeningiz
CLINIC_NAME        = MedCenter Klinikasi
CLINIC_ADDRESS     = Toshkent sh., Yunusobod, 5-mavze, 12-uy
CLINIC_PHONE       = +998 71 123 45 67
ADMIN_IDS          = 123456789
WORK_START         = 09:00
WORK_END           = 18:00
SLOT_DURATION      = 30
```

5. **PostgreSQL qo'shish:**
   - "New" → "Database" → "PostgreSQL" bosing
   - Railway `DATABASE_URL` ni avtomatik qo'shadi

6. **Deploy** tugmasini bosing → 2-3 daqiqada bot ishlaydi! ✅

---

### 5-QADAM: Botni sinab ko'rish

1. Telegramda bot username ni qidiring
2. `/start` yuboring
3. Admin panel uchun `/admin` yuboring (faqat ADMIN_IDS da bo'lganlar)

---

## ⚙️ KONFIGURATSIYA

### Shifokorlarni boshqarish

Bot ishga tushganda 4 ta default shifokor qo'shiladi.
Admin panel orqali (`/admin` → Shifokorlar):
- ✅/❌ Faollashtirish/O'chirish
- ➕ Yangi shifokor qo'shish

### Ish kunlari

`work_days` da raqamlar: `1`=Dushanba, `2`=Seshanba, ... `7`=Yakshanba
Default: `1,2,3,4,5` (Dush-Juma)

---

## 📊 BOT IMKONIYATLARI

### Mijoz uchun:
- ✅ Shifokorni tanlash
- ✅ Bo'sh kunlar va vaqtlarni ko'rish
- ✅ Navbat olish
- ✅ Navbatlarini ko'rish
- ✅ Navbatni bekor qilish
- ✅ 24 soat va 1 soat oldin eslatma olish

### Admin uchun:
- 📊 Statistika (jami, bugungi, bekor qilingan)
- 📋 Bugungi navbatlar ro'yxati
- 👨‍⚕️ Shifokorlarni boshqarish
- 📢 Barcha mijozlarga xabar yuborish

---

## 🔧 LOCAL TEST QILISH (ixtiyoriy)

```bash
# Python 3.10+ kerak
pip install -r requirements.txt

# .env fayl yarating
cp .env.example .env
# .env faylni to'ldiring (BOT_TOKEN va ADMIN_IDS majburiy)

# Ishga tushirish
python main.py
```

---

## 💰 NARX REJALARI (Klinikalarga sotish uchun)

| Tarif    | Narx    | Imkoniyatlar                           |
|----------|---------|----------------------------------------|
| Starter  | $30/oy  | 1 shifokor, navbat + eslatma           |
| Pro      | $60/oy  | 5 shifokor, statistika                 |
| Klinika  | $100/oy | Cheklovsiz, broadcast, premium support |

---

## 📞 Muammo bo'lsa

Kodni ishlatishda muammo bo'lsa:
1. Railway loglarini tekshiring (Deployments → Logs)
2. `.env` dagi BOT_TOKEN to'g'ri ekanligini tekshiring
3. ADMIN_IDS sizning Telegram ID ingiz ekanligini tekshiring
