# ⚡ VPS Hızlı Başvuru Kartı

## 🚀 Tek Komut Kurulum

```bash
# Root olarak çalıştır
curl -sSL https://raw.githubusercontent.com/KULLANICI/callPanel/main/install.sh | bash
```

---

## 📋 Temel Komutlar

### Servisi Yönet
```bash
sudo systemctl start callpanel      # Başlat
sudo systemctl stop callpanel       # Durdur
sudo systemctl restart callpanel    # Yeniden başlat
sudo systemctl status callpanel     # Durum
```

### Log İzle
```bash
tail -f ~/callPanel/logs/app.log    # Uygulama logu
tail -f ~/callPanel/logs/error.log  # Hata logu
sudo journalctl -u callpanel -f     # Systemd logu
```

### Güncelleme
```bash
cd ~/callPanel
git pull origin main
sudo systemctl restart callpanel
```

---

## 🔧 Sorun Giderme

### Uygulama Çalışmıyor?
```bash
# 1. Log kontrol
tail -n 50 ~/callPanel/logs/error.log

# 2. Servis durumu
sudo systemctl status callpanel

# 3. Manuel test
cd ~/callPanel && source venv/bin/activate
streamlit run Home.py
```

### Port Açık mı?
```bash
sudo ufw status                     # Firewall
sudo netstat -tlnp | grep 8501     # Port dinleme
curl http://localhost:8501         # Local test
```

### Veritabanı Sorunu?
```bash
ls -lh ~/callPanel/data/call_panel.db       # Dosya var mı?
chmod 644 ~/callPanel/data/call_panel.db    # Yetki düzelt
sudo systemctl restart callpanel            # Yeniden başlat
```

---

## 💾 Yedekleme

### Manuel Yedek
```bash
# Veritabanı yedeği
cp ~/callPanel/data/call_panel.db ~/backups/backup_$(date +%Y%m%d).db

# Tüm uygulama
tar -czf ~/backups/callpanel_$(date +%Y%m%d).tar.gz ~/callPanel
```

### Otomatik Yedek (Crontab)
```bash
crontab -e

# Her gün 02:00'de yedek al
0 2 * * * cp ~/callPanel/data/call_panel.db ~/backups/backup_$(date +%Y%m%d).db

# 7 günden eski yedekleri sil
0 3 * * * find ~/backups -name "backup_*.db" -mtime +7 -delete
```

---

## 🌐 Domain + SSL

### Nginx Kontrol
```bash
sudo nginx -t                       # Yapılandırma test
sudo systemctl restart nginx        # Yeniden başlat
sudo systemctl status nginx         # Durum
```

### SSL Yenileme
```bash
sudo certbot renew                  # Manuel yenile
sudo certbot renew --dry-run        # Test et
sudo certbot certificates           # Durumu gör
```

---

## 📊 Sistem İzleme

### Kaynak Kullanımı
```bash
htop                                # Genel sistem
df -h                               # Disk
free -h                             # RAM
ps aux | grep streamlit             # Uygulama
```

### Veritabanı
```bash
du -h ~/callPanel/data/call_panel.db        # Boyut
sqlite3 ~/callPanel/data/call_panel.db      # Komut satırı

# Örnek sorgular:
SELECT COUNT(*) FROM customers;             # Müşteri sayısı
SELECT COUNT(*) FROM call_logs;             # Arama sayısı
SELECT COUNT(*) FROM users;                 # Kullanıcı sayısı
```

---

## 🔐 Güvenlik

### Firewall
```bash
sudo ufw status                     # Durum
sudo ufw allow 8501/tcp            # Port aç
sudo ufw delete allow 8501/tcp     # Port kapat
sudo ufw reload                    # Yenile
```

### SSH
```bash
ssh callpanel@VPS_IP               # Bağlan
ssh-copy-id callpanel@VPS_IP       # Key ekle
```

---

## 🎯 Yapılandırma Dosyaları

| Dosya | Konum |
|-------|-------|
| Systemd servis | `/etc/systemd/system/callpanel.service` |
| Nginx config | `/etc/nginx/sites-available/callpanel` |
| Uygulama ayarları | `~/callPanel/utils/config.py` |
| Streamlit config | `~/callPanel/.streamlit/config.toml` |

---

## 📞 Acil Durum

### Tüm Sistemi Yeniden Başlat
```bash
sudo reboot
# 2 dakika bekle, servis otomatik başlar
```

### Veritabanını Sıfırla
```bash
cd ~/callPanel
rm data/call_panel.db
source venv/bin/activate
python -c "from services.database import init_database; init_database()"
sudo systemctl restart callpanel
```

### Uygulamayı Sıfırdan Kur
```bash
sudo systemctl stop callpanel
sudo systemctl disable callpanel
rm -rf ~/callPanel
# Kuruluma baştan başla
```

---

## 📱 Erişim Bilgileri

### HTTP (Direkt)
```
http://VPS_IP:8501
```

### HTTPS (Nginx + Domain)
```
https://callpanel.sirketiniz.com
```

### Varsayılan Giriş
```
Kullanıcı: admin
Şifre: admin123
```

⚠️ **ÖNEMLİ:** İlk giriş sonrası şifreyi DEĞİŞTİR!

---

## 🆘 Yardım

| Konu | Dosya |
|------|-------|
| Detaylı kurulum | `VPS_KURULUM.md` |
| Kullanım | `USAGE.md` |
| Özellikler | `README.md` |
| Değişiklikler | `CHANGELOG.md` |

---

## ✅ Kontrol Listesi

Kurulum sonrası kontrol:
- [ ] Uygulama çalışıyor: `sudo systemctl status callpanel`
- [ ] Loglar temiz: `tail ~/callPanel/logs/error.log`
- [ ] Erişilebiliyor: `curl http://localhost:8501`
- [ ] Giriş yapılıyor: Tarayıcıda test et
- [ ] Otomatik başlatma: `sudo systemctl is-enabled callpanel`
- [ ] Firewall açık: `sudo ufw status | grep 8501`
- [ ] Yedek sistemi çalışıyor: `ls ~/backups`

Tümü ✅ ise kurulum BAŞARILI! 🎉
