# 🎉 Geri Dönenler (Reactivation) Özelliği - Test Rehberi

## Özellik Açıklaması

Bu özellik, **pasif müşterilerin (30+ gün yatırım yok) tekrar aktif hale gelip gelmediğini** takip eder.

**Amaç:** Operatörlerin aradığı pasif müşteriler tekrar yatırım yapmaya başladı mı? → **Success tracking**

## Nasıl Çalışır?

1. **Hafta 1:** İlk CSV yüklenir → Pasif müşteriler havuza eklenir
2. **Operatörler:** Pasif müşterileri arar, notlar alır
3. **Hafta 2:** Yeni CSV yüklenir → Sistem otomatik olarak kontrol eder:
   - Eski CSV'de pasif miydi? (30+ gün yatırım yok)
   - Yeni CSV'de aktif mi? (son 30 günde yatırım var)
   - Operatörler tarafından aranmış mı?
4. **Eğer hepsi evet ise** → "Geri Dönenler" listesine eklenir!

## Test Adımları

### 1. Veritabanını Temizle (İsteğe Bağlı)

```bash
cd /Users/marquis/Desktop/callPanel
rm data/call_panel.db
```

### 2. Uygulamayı Başlat

```bash
source venv/bin/activate
streamlit run Home.py
```

### 3. İlk CSV'yi Yükle (Hafta 1)

1. Admin olarak giriş yap: `admin` / `admin123`
2. **"📤 Dosya Yükle"** tab → **"📄 CSV"** seç
3. `sample_csv_import_week1.csv` dosyasını yükle
4. **"📥 CSV Yükle ve İşle"** tıkla

**Beklenen Sonuç:**
- ✅ USR1001: Import (pasif - 2025-11-15)
- ✅ USR1002: Import (pasif - 2025-10-20)
- ❌ USR1003: Atlandı (sıfır yatırım)
- ❌ USR1004: Atlandı (aktif - 2026-02-08)
- ✅ USR1005: Import (pasif - 2025-09-05)
- ✅ USR1006: Import (pasif - 2025-10-10)

### 4. Test Operatörü Oluştur

1. **"👥 Operatör Yönetimi"** tab
2. Yeni operatör ekle:
   - Kullanıcı Adı: `test_op`
   - E-posta: `test@test.com`
   - Ad Soyad: `Test Operatör`
   - Şifre: `test123`
3. Çıkış yap, `test_op` / `test123` ile giriş yap

### 5. Müşterileri Ara (Operatör Olarak)

1. **"🎯 Müşteri Çek"** tıkla → Örnek: Ahmet Yılmaz (USR1001)
2. Notlar yaz: "100 TL bonus teklif edildi, olumlu karşılandı"
3. **"✅ Ulaşıldı"** tıkla
4. Tekrar "Müşteri Çek" → Mehmet Demir (USR1002)
5. Notlar: "200 TL bonus teklif edildi"
6. **"✅ Ulaşıldı"** tıkla
7. Tekrar "Müşteri Çek" → Ali Şahin (USR1005)
8. Notlar: "Geri dönüş bekliyor"
9. **"📵 Telefonu Açmadı"** tıkla

### 6. Admin Olarak Giriş Yap

Çıkış yap → `admin` / `admin123` ile giriş yap

### 7. İkinci CSV'yi Yükle (Hafta 2)

1. **"📤 Dosya Yükle"** tab → **"📄 CSV"** seç
2. `sample_csv_import_week2.csv` dosyasını yükle
3. **"📥 CSV Yükle ve İşle"** tıkla

**Beklenen Sonuç:**

**Karşılaştırma:**
- **USR1001 (Ahmet Yılmaz):**
  - Eski: 2025-11-15 (pasif)
  - Yeni: 2026-02-09 (aktif) ✅
  - Aranmış: Evet ✅
  - **→ REACTIVATION!** 🎉

- **USR1002 (Mehmet Demir):**
  - Eski: 2025-10-20 (pasif)
  - Yeni: 2026-02-08 (aktif) ✅
  - Aranmış: Evet ✅
  - **→ REACTIVATION!** 🎉

- **USR1005 (Ali Şahin):**
  - Eski: 2025-09-05 (pasif)
  - Yeni: 2026-02-07 (aktif) ✅
  - Aranmış: Evet ✅
  - **→ REACTIVATION!** 🎉

- **USR1006 (Zeynep Aydın):**
  - Eski: 2025-10-10 (pasif)
  - Yeni: 2026-02-09 (aktif) ✅
  - Aranmış: HAYIR ❌
  - **→ Geri dönen ama aranmamış**

**CSV Upload Sonucunda Görmeli:**
```
🎉 3 müşteri pasiften aktife döndü ve daha önce aranmıştı!
Bu müşterileri '🎉 Geri Dönenler' tab'ında görebilirsiniz.
```

### 8. Geri Dönenler Tab'ını Kontrol Et

1. **"🎉 Geri Dönenler"** tab'ına git
2. Göreceksin:
   - **Ahmet Yılmaz (USR1001)**
     - Eski Tarih: 2025-11-15
     - Yeni Tarih: 2026-02-09
     - Toplam Arama: 1
     - Son Durum: reached
     - Notlar: "100 TL bonus teklif edildi, olumlu karşılandı"
     - Operatör: Test Operatör

   - **Mehmet Demir (USR1002)**
     - Eski Tarih: 2025-10-20
     - Yeni Tarih: 2026-02-08
     - Toplam Arama: 1
     - Son Durum: reached
     - Notlar: "200 TL bonus teklif edildi"
     - Operatör: Test Operatör

   - **Ali Şahin (USR1005)**
     - Eski Tarih: 2025-09-05
     - Yeni Tarih: 2026-02-07
     - Toplam Arama: 1
     - Son Durum: no_answer
     - Notlar: "Geri dönüş bekliyor"
     - Operatör: Test Operatör

### 9. Filtreleme Testi

**Operatör Filtresi:**
- "Test Operatör" seç → 3 kayıt görünmeli

**Tarih Filtresi:**
- "Son 7 Gün" seç → 3 kayıt görünmeli
- "Tümü" seç → 3 kayıt görünmeli

**CSV Export:**
- "📥 CSV Olarak İndir" tıkla
- İndirilen dosyayı Excel'de aç ve kontrol et

## Gerçek Kullanım Senaryosu

### Hafta 1 (Pazartesi):
```bash
# Admin CSV yükler
- 500 pasif müşteri import edilir
```

### Hafta 1 (Salı-Cuma):
```bash
# Operatörler çalışır
- 500 müşteriden 300'ü aranır
- 150'si ulaşıldı
- 100'ü telefonu açmadı
- 50'si meşgule attı
```

### Hafta 2 (Pazartesi):
```bash
# Admin yeni CSV yükler
- Sistem otomatik kontrol eder
- Örnek: 15 müşteri pasiften aktife dönmüş
- Bunlardan 12'si aranmıştı
- "Geri Dönenler" tab'ında 12 kayıt görünür
```

### Hafta 2 (Toplantı):
```bash
# Yönetici raporlar:
"Geçen hafta 300 pasif müşteriyi aradık.
Bu hafta 12'si tekrar yatırım yapmaya başladı.
Başarı oranı: %4

En başarılı operatör: Ahmet (5 geri dönen)
En etkili notlar: Bonus teklifleri"
```

## Önemli Notlar

1. **CUSTOMER_CODE sabit kalmalı** - Bu ID ile müşteriler eşleşir
2. **Her CSV yeni tarihleri içermeli** - Sistem yeni CSV'deki tarihleri referans alır
3. **30 gün kuralı:**
   - Eski tarih 30+ gün önceyse → pasif
   - Yeni tarih 30 gün içindeyse → aktif
4. **Sadece aranmış müşteriler** "Geri Dönenler"e eklenir
5. **Her CSV yüklemede** reactivation kontrolü otomatik yapılır

## VPS'te Kullanım

```bash
# VPS'e bağlan
ssh callpanel@your-vps-ip

# CSV dosyasını yükle (WinSCP, FileZilla, vb. ile)
# Veya wget ile:
cd ~/callPanel
wget https://your-server.com/weekly_data.csv

# Streamlit arayüzünden yükle
# http://your-vps-ip:8501
```

## Sorun Giderme

**Reactivation tespit edilmedi:**
- CSV formatı doğru mu? (Pipe-delimited: `|`)
- LAST_DEPOSIT_TRANSACTION_DATE kolonu var mı?
- CUSTOMER_CODE eşleşiyor mu?
- Müşteri daha önce aranmış mı? (call_logs tablosunu kontrol et)

**Tarihler yanlış:**
- Tarih formatı: `YYYY-MM-DD HH:MM:SS` veya `YYYY-MM-DD`
- Pandas parse edebilmeli

**Database kontrol:**
```bash
sqlite3 ~/callPanel/data/call_panel.db

SELECT * FROM reactivations;
SELECT * FROM call_logs WHERE customer_id = 1;
.exit
```

## Başarılar!

Bu özellik sayesinde operatör performansını ve arama stratejilerinin etkinliğini ölçebilirsiniz! 📊🎉
