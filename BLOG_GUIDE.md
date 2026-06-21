# Blog Tizim — Qo'llanma

Blog xususiyatini to'liq shaklda qo'shilgan! Quyida amaliy misol:

## ✅ Amalga Oshirilgan Xususiyatlar

### 1️⃣ Blog App Yaratildi
```
blog/
├── models.py           # BlogPost va BlogComment modellari
├── views.py            # Dashboard va public view'lar
├── forms.py            # Blog post va izoh formatlari
├── urls.py             # URL yo'llarі
├── admin.py            # Admin interfeysі
└── migrations/         # Database migratsiyalar
```

### 2️⃣ Blog Modellari

**BlogPost** — Blog postlarі:
- `business` — Biznesga bog'lash (ForeignKey)
- `title` — Sarlavha
- `slug` — URL-moslashtirilgan sarlavha (avtomatik)
- `content` — Mazmun (HTML yoki tekst)
- `excerpt` — Qisqa tavsif (ixtiyoriy)
- `featured_image` — Yulduz rasmi (ixtiyoriy)
- `is_published` — Foydalanuvchilarga ko'rsatish
- `views_count` — Ko'rish soni
- `created_at`, `updated_at` — Vaqt va'qlari

**BlogComment** — Izohlar:
- `post` — Blog postiga bog'lash
- `name` — Izoh qo'yuvchining ismi
- `email` — Email
- `content` — Izoh mazmuni
- `is_approved` — Tekshiruvdan o'tish holati

### 3️⃣ Dashboard Funksiyalari

📋 **Blog Ro'yxati** (`/dashboard/blog/`)
- Barcha blog postlarni ko'rish
- Nashr holati
- Ko'rish soni
- Tahrirlash / O'chirish tugmalari

✍️ **Yangi Blog Qo'shish** (`/dashboard/blog/create/`)
- Sarlavha
- Qisqa mazmun
- To'liq mazmun
- Rasmi
- Nashr holati

✏️ **Blog Tahrirlash** (`/dashboard/blog/<id>/edit/`)
- Barcha maydonlarni o'zgartirish

🗑️ **Blog O'chirish** (`/dashboard/blog/<id>/delete/`)

### 4️⃣ Foydalanuvchi Uchun Sahifalari

🔍 **Blog Ro'yxati** (`/<slug>/blog/`)
- Barcha nashr qilingan bloglarni ko'rish
- Kartalarda:
  - Rasmi
  - Sarlavha
  - Qisqa mazmun
  - Yaratilgan sana
  - Ko'rish soni
- Pagination (sahifa bo'ylab)

📖 **Blog Tafsilotlari** (`/<slug>/blog/<post_slug>/`)
- To'liq blog mazmuni
- Yulduz rasmi
- Meta ma'lumotlar (sana, ko'rish soni, izohlar soni)
- Izohlarni ko'rish
- Yangi izoh qo'shish
- Sidebar:
  - Biznes haqida
  - Bosh sahifaga havolasi

## 🛠️ Texnik Detalllar

### Database Migratsiyalar
```bash
python manage.py makemigrations blog
python manage.py migrate blog
```
✅ Muvaffaqiyatli qo'llanildi!

### Django Admin
Blog admin interface'iga kirish:
- `/admin/blog/blogpost/` — Blog postlar
- `/admin/blog/blogcomment/` — Izohlar

**Qo'shimcha funksiyalar:**
- Izohlarni tasdiqlash/rad etish
- Bulk operatsiyalar

## 🔌 URL Yo'llari

### Dashboard URLs
```python
/dashboard/blog/              # Blog ro'yxati
/dashboard/blog/create/       # Yangi blog qo'shish
/dashboard/blog/<id>/edit/    # Blog tahrirlash
/dashboard/blog/<id>/delete/  # Blog o'chirish
```

### Public URLs
```python
/<slug>/blog/                        # Blog ro'yxati
/<slug>/blog/<post_slug>/            # Blog tafsilotlari
```

## 📝 Shablonlar (Templates)

### Dashboard
- `templates/dashboard/blog/list.html` — Blog ro'yxati
- `templates/dashboard/blog/form.html` — Blog form

### Public
- `templates/public/blog_list.html` — Blog ro'yxati
- `templates/public/blog_detail.html` — Blog tafsilotlari

## 🎯 Foydalanish Misoli

### 1. Dashboard dan blog qo'shish
1. Dashboard ga kirib, sidebar'dan "Blog" ni bosing
2. "Yangi Post" tugmasini bosing
3. Sarlavha, mazmun, rasim qo'shing
4. "Saqlash" tugmasini bosing
5. Post nashr qilingan bo'lsa, foydalanuvchilarga ko'rinadi

### 2. Foydalanuvchi blog o'qiydi
1. Biznes sahifasiga kirib, "Blog" tugmasini bosing
2. Blog postlarini ko'radi
3. Postni bosib, tafsilotlarni o'qiydi
4. Izoh qo'shsa, admin tasdiqlagandan keyin ko'rinadi

## 🔐 Xavfsizlik

- **Dashboard** — Faqat login qilgan, o'z biznesi boshqaruvchisi ko'rishi mumkin
- **Izohlar** — Admin tasdiqlashdan keyin ko'rinadi (spam dan himoya)
- **Public** — Faqat nashr qilingan bloglar ko'rinadi
- CSRF — Barcha formalar CSRF tokeniga himoyalangan

## 📊 Admin Panel Funksiyalari

### Blog Post Admin
- **List display**: Sarlavha, biznes, nashr holati, ko'rish soni, yaratilgan sana
- **Search**: Sarlavha, mazmun, biznes nomi bo'ylab
- **Filter**: Nashr holati, biznes, sana bo'ylab
- **Inline izohlar**: Blog post'da izohlarni boshqarish

### Blog Comment Admin
- **Izohlarni tasdiqlash** (bulk action)
- **Izohlarni rad etish** (bulk action)
- **Izohlar ro'yxati**: Ismi, post, tasdiqlash holati

## 🚀 Keyingi Bosqichlar (Ixtiyoriy)

- [ ] Blog kategoriyalari qo'shish
- [ ] Tegi/tags qo'shish
- [ ] SEO optimizatsiya (meta tags)
- [ ] Blog RSS feed
- [ ] Social media share buttons
- [ ] Comment email notifications
- [ ] Blog search functionality

---

**Seroqat topilsa**, admin panel'dan `Settings` → `Blog` bo'limida sozlamalar o'zgartirilishi mumkin!
