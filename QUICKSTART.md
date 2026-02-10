# 🚀 Quick Start Guide

## Uygulamayı Başlat (3 Adım)

### 1️⃣ Terminali Aç ve Proje Dizinine Git
```bash
cd /Users/marquis/Desktop/callPanel
```

### 2️⃣ Uygulamayı Başlat
```bash
./start.sh
```

Veya manuel:
```bash
source venv/bin/activate
streamlit run Home.py
```

### 3️⃣ Tarayıcıda Aç
Otomatik açılacak: **http://localhost:8501**

---

## 🔐 İlk Giriş

**Admin Kullanıcısı:**
- Kullanıcı Adı: `admin`
- Şifre: `admin123`

---

## 📤 İlk Excel Yükleme (Test)

1. Admin olarak giriş yap
2. **Excel Yükle** sekmesine git
3. `sample_customers.xlsx` dosyasını yükle (8 test müşteri)
4. Sonuçları gör: 8 başarılı import

---

## 👥 İlk Operatör Oluşturma

1. **Operatör Yönetimi** sekmesine git
2. Formu doldur:
   ```
   Kullanıcı Adı: operator1
   E-posta: operator1@test.com
   Ad Soyad: Test Operatör
   Şifre: pass123
   ```
3. **➕ Operatör Ekle** butonuna bas

---

## 📞 İlk Arama (Operatör)

1. **Çıkış Yap**
2. Operatör olarak giriş yap (`operator1` / `pass123`)
3. **🎯 Müşteri Çek** butonuna bas
4. Müşteri bilgilerini gör
5. Not yaz: "Test arama"
6. **✅ Ulaşıldı** butonuna bas
7. İstatistikleri kontrol et

---

## 📊 Dashboard Kontrol

1. Admin olarak tekrar giriş yap
2. **Dashboard** sekmesine git
3. İstatistikleri gör:
   - Toplam: 8 müşteri
   - Beklemede: 7
   - Tamamlanan: 1
   - Operatör performansı

---

## ✅ Hepsi Bu Kadar!

Artık sistem kullanıma hazır. Kendi Excel dosyanızı yükleyerek başlayabilirsiniz.

### Excel Format Örneği:

| Ad | Soyad | Kullanıcı Kodu | Telefon Numarası |
|----|-------|----------------|------------------|
| Ahmet | Yılmaz | USR001 | 05321234567 |
| Mehmet | Demir | USR002 | 05331234568 |

---

## 📚 Daha Fazla Bilgi

- **Detaylı kullanım:** `USAGE.md`
- **Teknik detaylar:** `IMPLEMENTATION_SUMMARY.md`
- **Genel bilgi:** `README.md`

---

## 🆘 Sorun mu Var?

### Uygulama Açılmıyor:
```bash
# Virtual environment'ı aktifleştir
source venv/bin/activate

# Bağımlılıkları kontrol et
pip list

# Tekrar dene
streamlit run Home.py
```

### Port Zaten Kullanılıyor:
```bash
# Farklı port kullan
streamlit run Home.py --server.port=8502
```

### Veritabanı Hatası:
```bash
# Veritabanını sıfırla (DİKKAT: Tüm veri silinir!)
rm data/call_panel.db
streamlit run Home.py
```

---

## 🎯 Başarılı Kurulum Testi

1. ✅ Tarayıcıda sayfa açıldı
2. ✅ Admin girişi yapıldı
3. ✅ Excel yüklendi
4. ✅ Operatör oluşturuldu
5. ✅ Operatör müşteri çekti
6. ✅ Arama kaydedildi
7. ✅ İstatistikler görüldü

Tüm adımlar tamamsa, sistem hazır! 🎉
