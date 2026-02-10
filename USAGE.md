# Call Center Panel - Kullanım Kılavuzu

## Hızlı Başlangıç

### 1. Uygulamayı Başlat
```bash
cd /Users/marquis/Desktop/callPanel
./start.sh
```

Veya manuel olarak:
```bash
source venv/bin/activate
streamlit run Home.py
```

Tarayıcıda otomatik olarak açılacak: **http://localhost:8501**

### 2. İlk Giriş (Admin)
- **Kullanıcı Adı:** `admin`
- **Şifre:** `admin123`

---

## Admin İşlemleri

### Excel ile Müşteri Yükleme

1. **Excel Yükle** sekmesine git
2. Excel dosyası hazırla (örnek: `sample_customers.xlsx`)
3. Dosyayı sürükle-bırak veya seç
4. **📥 Yükle ve İşle** butonuna bas
5. Sonuçları gözden geçir

**Excel Format Kuralları:**
- Kolon isimleri: `Ad`, `Soyad`, `Kullanıcı Kodu`, `Telefon Numarası`
- Kullanıcı Kodu benzersiz olmalı
- Boş satır olmamalı

### Operatör Ekleme

1. **Operatör Yönetimi** sekmesine git
2. Formu doldur:
   - Kullanıcı Adı (benzersiz)
   - E-posta
   - Ad Soyad
   - Şifre
3. **➕ Operatör Ekle** butonuna bas

### Dashboard İzleme

**Genel İstatistikler:**
- Toplam Müşteri
- Havuzda Bekleyen
- Bugünkü Aramalar
- Tamamlanan
- Ulaşılamayan
- Şu An Atanmış

**Operatör Performansı Tablosu:**
- Her operatörün bugünkü arama sayısı
- Ulaşılan müşteri sayısı
- Şu anda aradığı müşteri

### Takılı Müşterileri Serbest Bırakma

10 dakikadan uzun atanmış kalmış müşterileri havuza geri döndür:
1. Dashboard'da **🔄 Takılı Müşterileri Serbest Bırak** butonuna bas
2. Kaç müşterinin serbest bırakıldığını gör

---

## Operatör İşlemleri

### Müşteri Çekme ve Arama

1. Giriş yap (kullanıcı adı/şifre)
2. **🎯 Müşteri Çek** butonuna bas
3. Müşteri bilgileri ekranda görünür:
   - Ad
   - Soyad
   - Kullanıcı Kodu
   - Telefon Numarası
   - Arama Denemesi (varsa)

### Arama Yapma

1. Müşteriyi ara
2. **📝 Notlar** alanına görüşme notlarını yaz
   - Bonus teklifleri
   - Müşteri yanıtları
   - Geri dönüş tarihi
3. Arama sonucunu seç:

**Durum Butonları:**

- **✅ Ulaşıldı**: Müşteri görüşme yaptı, tamamlandı olarak işaretlenir
- **📵 Telefonu Açmadı**: Müşteri tekrar havuza döner (maks 3 deneme)
- **🚫 Meşgule Attı**: Müşteri tekrar havuza döner (maks 3 deneme)
- **⏳ Meşgul**: Hat meşgul, müşteri tekrar havuza döner (maks 3 deneme)

### İstatistikler

Ana ekranda bugünkü performansını gör:
- **Toplam Arama**: Bugün yaptığın toplam arama sayısı
- **Ulaşılan**: Başarılı görüşme sayısı
- **Başarı Oranı**: Ulaşılan / Toplam Arama yüzdesi

---

## Müşteri Havuz Sistemi

### Nasıl Çalışır?

1. **Müşteri Çekme**:
   - Operatör "Müşteri Çek" butonuna basar
   - Sistem havuzdan bir müşteri çeker ve operatöre atar
   - Müşteri durumu "atandı" olur

2. **Arama Sonuçları**:
   - **Ulaşıldı** → Müşteri "tamamlandı" olur, bir daha aranmaz
   - **Açmadı/Meşgul/Red** → Müşteri havuza döner, deneme sayısı +1

3. **Maksimum Deneme**:
   - Her müşteri en fazla 3 kez aranır
   - 3 denemede ulaşılamazsa "ulaşılamadı" olur

4. **Önceliklendirme**:
   - Havuzdaki müşteriler FIFO (ilk giren ilk çıkar) sırasıyla çekilir
   - Priority alanı ile öncelik verilebilir (gelecek özellik)

### Thread Safety

Sistem, aynı anda birden fazla operatörün aynı müşteriyi çekmesini engeller:
- SQLite veritabanı kilitleme
- Python threading.Lock kullanımı
- Atomik UPDATE operasyonları

---

## Veritabanı Bilgileri

**Konum:** `data/call_panel.db`

### Tablolar:

1. **users**: Kullanıcılar (admin, operatörler)
2. **customers**: Müşteri listesi
3. **call_logs**: Tüm arama kayıtları
4. **excel_uploads**: Excel yükleme geçmişi

### Yedekleme:

```bash
# Manuel yedekleme
cp data/call_panel.db backups/call_panel_$(date +%Y%m%d).db

# Otomatik yedekleme (crontab)
0 2 * * * cd /Users/marquis/Desktop/callPanel && cp data/call_panel.db backups/call_panel_$(date +%Y%m%d).db
```

---

## Sık Karşılaşılan Sorunlar

### "Havuzda müşteri yok"
- Admin panelinden Excel dosyası yüklendiğinden emin ol
- Dashboard'dan "Beklemede" müşteri olup olmadığını kontrol et
- Tüm müşteriler tamamlanmış veya ulaşılamadı olabilir

### "Kullanıcı adı veya şifre hatalı"
- Kullanıcı adını doğru yazdığından emin ol (büyük/küçük harf duyarlı)
- Admin: `admin` / `admin123`

### Müşteri Takıldı (10dk+)
- Admin panelinden "Takılı Müşterileri Serbest Bırak" butonunu kullan
- Operatör logout yapmadan tarayıcıyı kapatmışsa bu olabilir

### Excel Yükleme Hatası
- Excel kolonlarının doğru isimde olduğundan emin ol
- Kullanıcı Kodu'nun benzersiz olduğunu kontrol et
- Boş satır olmamalı

---

## Performans ve Limitler

### Ölçek:
- **Önerilen**: 1-10 operatör
- **Maksimum**: 50 concurrent operatör (SQLite limiti)
- **Müşteri Sayısı**: Sınır yok (test edildi: 100,000+ kayıt)

### Optimizasyonlar:
- Database indexleri optimize edildi
- Thread-safe pooling sistemi
- Efficient SQL queries

---

## Güvenlik

- ✅ Şifreler bcrypt ile hashlenmiş
- ✅ SQL injection koruması
- ✅ Role-based access control (RBAC)
- ✅ Session yönetimi
- ⚠️ Production'da HTTPS kullan (reverse proxy)

---

## Destek

Sorun bildirmek için:
- GitHub Issues: (proje reposu)
- Email: admin@callpanel.com
