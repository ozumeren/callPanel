# Call Center Panel - Streamlit Implementation

Lightweight çağrı merkezi yönetim paneli. 1-10 operatörlük küçük ekipler için SQLite + Streamlit ile basit ve hızlı çözüm.

## Özellikler

- ✅ Admin ve Operatör rol yönetimi
- ✅ Excel ile toplu müşteri yükleme
- ✅ Thread-safe müşteri havuz sistemi
- ✅ Otomatik yeniden deneme (maks 3 kez)
- ✅ Gerçek zamanlı istatistikler
- ✅ Türkçe arayüz

## Kurulum

### 1. Virtual Environment Oluştur
```bash
cd /Users/marquis/Desktop/callPanel
python3 -m venv venv
source venv/bin/activate
```

### 2. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 3. Uygulamayı Başlat
```bash
streamlit run Home.py
```

Tarayıcınızda otomatik olarak açılacak: http://localhost:8501

## İlk Giriş

**Admin Kullanıcısı:**
- Kullanıcı Adı: `admin`
- Şifre: `admin123`

## Excel Formatı

Excel dosyanız şu kolonları içermelidir:

| Ad | Soyad | Kullanıcı Kodu | Telefon Numarası |
|----|-------|----------------|------------------|
| Ahmet | Yılmaz | USR001 | 05321234567 |
| Mehmet | Demir | USR002 | 05331234568 |

## İş Akışı

### Admin Tarafı:
1. Giriş yap (admin/admin123)
2. **Excel Yükle** sekmesinden müşteri listesi yükle
3. **Dashboard** sekmesinden performansı izle
4. **Operatör Yönetimi** sekmesinden yeni operatör ekle

### Operatör Tarafı:
1. Giriş yap (kullanıcı adı/şifre)
2. **🎯 Müşteri Çek** butonuna bas
3. Müşteriyi ara ve notları yaz
4. Arama durumunu seç:
   - **✅ Ulaşıldı**: Müşteri tamamlandı
   - **📵 Telefonu Açmadı**: Tekrar havuza döner
   - **🚫 Meşgule Attı**: Tekrar havuza döner
   - **⏳ Meşgul**: Tekrar havuza döner

## Önemli Notlar

- Müşteriler en fazla 3 kez aranabilir
- 10 dakikadan uzun atanmış müşteriler otomatik serbest bırakılabilir
- Her arama kaydedilir ve istatistiklerde görünür
- Operatörler sadece kendi aramalarını görebilir
- Admin tüm sistemi görebilir

## Proje Yapısı

```
callPanel/
├── Home.py                    # Giriş sayfası
├── pages/
│   ├── 1_📊_Admin_Panel.py   # Admin paneli
│   └── 2_📞_Operator_Panel.py # Operatör paneli
├── services/
│   ├── database.py            # Veritabanı işlemleri
│   ├── auth_service.py        # Kimlik doğrulama
│   ├── excel_service.py       # Excel import
│   └── pool_service.py        # Müşteri havuzu (kritik)
├── utils/
│   ├── constants.py           # Sabitler
│   └── helpers.py             # Yardımcı fonksiyonlar
├── data/
│   └── call_panel.db          # SQLite veritabanı
└── .streamlit/
    └── config.toml            # Streamlit yapılandırması
```

## Veritabanı

SQLite veritabanı `data/call_panel.db` konumunda otomatik oluşturulur.

### Tablolar:
- `users`: Admin ve operatör kullanıcıları
- `customers`: Müşteri listesi
- `call_logs`: Arama kayıtları
- `excel_uploads`: Excel yükleme geçmişi

## Güvenlik

- Şifreler bcrypt ile hashlenir
- SQL injection koruması (parameterized queries)
- Role-based access control (RBAC)
- Session-based authentication

## Deployment

### Streamlit Cloud (Ücretsiz)
1. GitHub'a push et
2. https://share.streamlit.io adresine git
3. Repository'yi bağla

### Docker
```bash
docker build -t callpanel .
docker run -p 8501:8501 -v $(pwd)/data:/app/data callpanel
```

## Yedekleme

Veritabanını düzenli yedekleyin:
```bash
cp data/call_panel.db backups/call_panel_$(date +%Y%m%d).db
```

## Lisans

MIT License

## Destek

Sorular için: admin@callpanel.com
