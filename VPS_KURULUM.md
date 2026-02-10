# 🚀 VPS'e Kurulum Rehberi

## 📋 Gereksinimler

### VPS Özellikleri:
- **İşletim Sistemi:** Ubuntu 20.04+ veya Debian 11+
- **RAM:** Minimum 1 GB (2 GB önerilir)
- **Disk:** 10 GB
- **Python:** 3.8 veya üzeri
- **İnternet:** Açık portlar (8501 veya 80/443)

### Neler Gerekli:
- ✅ VPS IP adresi
- ✅ SSH erişimi
- ✅ Root veya sudo yetkisi

---

## 🔧 Adım 1: VPS'e Bağlan

```bash
# SSH ile bağlan
ssh root@VPS_IP_ADRESI

# Örnek:
ssh root@185.123.45.67
```

**İlk giriş şifresi:** VPS sağlayıcınızdan gelir (email)

---

## 🔒 Adım 2: Güvenlik Güncellemeleri

```bash
# Paketleri güncelle
apt update && apt upgrade -y

# Gerekli araçları yükle
apt install -y python3 python3-pip python3-venv git nano curl
```

---

## 👤 Adım 3: Uygulama Kullanıcısı Oluştur

```bash
# Yeni kullanıcı oluştur (güvenlik için root kullanma)
useradd -m -s /bin/bash callpanel

# Şifre belirle
passwd callpanel

# Sudo yetkisi ver
usermod -aG sudo callpanel

# Kullanıcıya geç
su - callpanel
```

---

## 📦 Adım 4: Uygulamayı Yükle

### Seçenek A: Git ile (Önerilen)

```bash
# Proje dizini oluştur
cd ~
git clone https://github.com/KULLANICI_ADINIZ/callPanel.git
cd callPanel
```

### Seçenek B: SCP ile (Git yoksa)

**Kendi bilgisayarınızda:**
```bash
# VPS'e dosyaları gönder
cd /Users/marquis/Desktop
scp -r callPanel callpanel@VPS_IP:~/
```

**VPS'de:**
```bash
cd ~/callPanel
```

---

## 🐍 Adım 5: Python Ortamını Hazırla

```bash
# Virtual environment oluştur
python3 -m venv venv

# Aktifleştir
source venv/bin/activate

# Bağımlılıkları yükle
pip install --upgrade pip
pip install -r requirements.txt
```

**Beklenen süre:** 2-3 dakika

---

## ✅ Adım 6: İlk Test

```bash
# Veritabanını başlat
streamlit run Home.py --server.port 8501 --server.address 0.0.0.0

# Tarayıcıda aç:
# http://VPS_IP:8501
```

**Ctrl+C** ile durdur.

✅ Çalışıyorsa bir sonraki adıma geç!

---

## 🔥 Adım 7: Firewall Ayarları

```bash
# UFW yükle (yoksa)
sudo apt install -y ufw

# SSH'ı aç (KENDİNİ KILITLEME!)
sudo ufw allow 22/tcp

# Streamlit portunu aç
sudo ufw allow 8501/tcp

# Firewall'ı aktifleştir
sudo ufw enable

# Durumu kontrol et
sudo ufw status
```

**Çıktı:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
8501/tcp                   ALLOW       Anywhere
```

---

## 🔄 Adım 8: Systemd Servisi (Otomatik Başlatma)

### 8.1: Servis Dosyası Oluştur

```bash
sudo nano /etc/systemd/system/callpanel.service
```

### 8.2: İçeriği Yapıştır

```ini
[Unit]
Description=Call Center Panel - Streamlit Application
After=network.target

[Service]
Type=simple
User=callpanel
WorkingDirectory=/home/callpanel/callPanel
Environment="PATH=/home/callpanel/callPanel/venv/bin"
ExecStart=/home/callpanel/callPanel/venv/bin/streamlit run Home.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

Restart=always
RestartSec=10

StandardOutput=append:/home/callpanel/callPanel/logs/app.log
StandardError=append:/home/callpanel/callPanel/logs/error.log

[Install]
WantedBy=multi-user.target
```

**Kaydet:** `Ctrl+O` → Enter → `Ctrl+X`

### 8.3: Log Dizini Oluştur

```bash
mkdir -p ~/callPanel/logs
```

### 8.4: Servisi Başlat

```bash
# Systemd'yi yenile
sudo systemctl daemon-reload

# Servisi başlat
sudo systemctl start callpanel

# Otomatik başlatmayı aktifleştir
sudo systemctl enable callpanel

# Durumu kontrol et
sudo systemctl status callpanel
```

**Beklenen çıktı:**
```
● callpanel.service - Call Center Panel
   Loaded: loaded (/etc/systemd/system/callpanel.service)
   Active: active (running) since Mon 2026-02-10 12:00:00 UTC
```

---

## 📊 Adım 9: Log Kontrolü

```bash
# Canlı log izle
tail -f ~/callPanel/logs/app.log

# Hata logları
tail -f ~/callPanel/logs/error.log

# Systemd logları
sudo journalctl -u callpanel -f
```

**Ctrl+C** ile çık.

---

## 🌐 Adım 10: Erişim Test Et

Tarayıcıda aç:
```
http://VPS_IP_ADRESI:8501
```

Örnek:
```
http://185.123.45.67:8501
```

**Giriş yap:**
- Kullanıcı: `admin`
- Şifre: `admin123`

---

## 🎯 OPSIYONEL: Domain + HTTPS (Nginx)

### Neden?
- ✅ `https://callpanel.sirketiniz.com` gibi güzel URL
- ✅ Ücretsiz SSL sertifikası
- ✅ Port 8501 yerine 443 (HTTPS)

### Adım 1: Domain Ayarla

Domain sağlayıcınızda (GoDaddy, Namecheap, vb.):
```
A Record:
  Name: callpanel
  Value: VPS_IP_ADRESI
  TTL: 3600
```

**Bekleme:** 5-30 dakika (DNS yayılması)

### Adım 2: Nginx Yükle

```bash
sudo apt install -y nginx
```

### Adım 3: Nginx Yapılandırması

```bash
sudo nano /etc/nginx/sites-available/callpanel
```

**İçeriği yapıştır:**
```nginx
server {
    listen 80;
    server_name callpanel.sirketiniz.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

**Değiştir:** `callpanel.sirketiniz.com` → Kendi domaininiz

### Adım 4: Nginx'i Aktifleştir

```bash
# Sembolik link oluştur
sudo ln -s /etc/nginx/sites-available/callpanel /etc/nginx/sites-enabled/

# Nginx'i test et
sudo nginx -t

# Nginx'i başlat
sudo systemctl restart nginx

# Firewall'da HTTP/HTTPS aç
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Adım 5: SSL Sertifikası (Let's Encrypt - ÜCRETSİZ)

```bash
# Certbot yükle
sudo apt install -y certbot python3-certbot-nginx

# SSL al (otomatik yapılandırma)
sudo certbot --nginx -d callpanel.sirketiniz.com
```

**Sorular:**
1. Email: `admin@sirketiniz.com` (bildirimlere)
2. Terms: `A` (Agree)
3. Redirect HTTP → HTTPS: `2` (Evet)

### Adım 6: Otomatik Yenileme

```bash
# Test et
sudo certbot renew --dry-run
```

✅ Başarılıysa, sertifika otomatik yenilenecek!

### Adım 7: Erişim

Artık şu adresten erişebilirsiniz:
```
https://callpanel.sirketiniz.com
```

Port 8501'e gerek yok! 🎉

---

## 🔧 Servis Yönetimi

### Durumu Kontrol Et
```bash
sudo systemctl status callpanel
```

### Yeniden Başlat
```bash
sudo systemctl restart callpanel
```

### Durdur
```bash
sudo systemctl stop callpanel
```

### Başlat
```bash
sudo systemctl start callpanel
```

### Logları İzle
```bash
# Canlı log
tail -f ~/callPanel/logs/app.log

# Son 50 satır
tail -n 50 ~/callPanel/logs/app.log

# Hata logları
tail -f ~/callPanel/logs/error.log
```

---

## 📤 Güncelleme (Kod Değiştiğinde)

### Git ile:
```bash
cd ~/callPanel
git pull origin main
sudo systemctl restart callpanel
```

### SCP ile:
```bash
# Kendi bilgisayarınızda:
scp -r /Users/marquis/Desktop/callPanel/* callpanel@VPS_IP:~/callPanel/

# VPS'de:
sudo systemctl restart callpanel
```

---

## 💾 Yedekleme

### Veritabanı Yedeği

```bash
# Manuel yedek
cp ~/callPanel/data/call_panel.db ~/backups/call_panel_$(date +%Y%m%d).db

# Otomatik yedek (her gün 02:00)
crontab -e

# Ekle:
0 2 * * * cp ~/callPanel/data/call_panel.db ~/backups/call_panel_$(date +%Y%m%d).db
```

### Eski Yedekleri Temizle

```bash
# 7 günden eski yedekleri sil
find ~/backups -name "call_panel_*.db" -mtime +7 -delete
```

---

## 🐛 Sorun Giderme

### 1. Uygulama Başlamıyor

```bash
# Logları kontrol et
tail -f ~/callPanel/logs/error.log

# Servis durumu
sudo systemctl status callpanel

# Manuel başlat (test)
cd ~/callPanel
source venv/bin/activate
streamlit run Home.py
```

### 2. Port Erişilemiyor

```bash
# Firewall kontrol
sudo ufw status

# Port dinleme kontrolü
sudo netstat -tlnp | grep 8501

# Servisi yeniden başlat
sudo systemctl restart callpanel
```

### 3. Veritabanı Hatası

```bash
# Dosya var mı?
ls -lh ~/callPanel/data/call_panel.db

# Yetki kontrolü
chmod 644 ~/callPanel/data/call_panel.db

# Yeniden başlat
sudo systemctl restart callpanel
```

### 4. Nginx Hatası

```bash
# Nginx durumu
sudo systemctl status nginx

# Yapılandırma testi
sudo nginx -t

# Loglar
sudo tail -f /var/log/nginx/error.log
```

### 5. SSL Sertifikası Sorunu

```bash
# Certbot durumu
sudo certbot certificates

# Yenileme testi
sudo certbot renew --dry-run

# Manuel yenileme
sudo certbot renew
```

---

## 🔐 Güvenlik Önerileri

### 1. Admin Şifresini Değiştir

**SQLite komut satırında:**
```bash
sqlite3 ~/callPanel/data/call_panel.db
```

```sql
-- Şifre hash'i oluştur (Python)
-- python3 -c "from bcrypt import hashpw, gensalt; print(hashpw('YeniSifre123'.encode(), gensalt()).decode())"

-- Sonucu kullan:
UPDATE users
SET password_hash = 'BURAYA_HASH_KOYUN'
WHERE username = 'admin';

.exit
```

### 2. SSH Key ile Giriş

```bash
# Kendi bilgisayarınızda:
ssh-keygen -t rsa

# Public key'i VPS'e gönder
ssh-copy-id callpanel@VPS_IP

# Artık şifresiz girebilirsin
ssh callpanel@VPS_IP
```

### 3. SSH Şifre Girişini Kapat

```bash
# VPS'de:
sudo nano /etc/ssh/sshd_config

# Değiştir:
PasswordAuthentication no

# Kaydet ve SSH'ı yeniden başlat
sudo systemctl restart sshd
```

### 4. Fail2ban (Brute Force Koruması)

```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📊 Performans İzleme

### Sistem Kaynakları

```bash
# Anlık kaynak kullanımı
htop

# Disk kullanımı
df -h

# RAM kullanımı
free -h

# Uygulama kaynak kullanımı
ps aux | grep streamlit
```

### Veritabanı Boyutu

```bash
du -h ~/callPanel/data/call_panel.db
```

---

## 🎯 Hızlı Başvuru

### Temel Komutlar

| İşlem | Komut |
|-------|-------|
| Servisi başlat | `sudo systemctl start callpanel` |
| Servisi durdur | `sudo systemctl stop callpanel` |
| Servisi yeniden başlat | `sudo systemctl restart callpanel` |
| Durum kontrol | `sudo systemctl status callpanel` |
| Log izle | `tail -f ~/callPanel/logs/app.log` |
| Veritabanı yedeği | `cp ~/callPanel/data/call_panel.db ~/backup.db` |
| Güncelle | `git pull && sudo systemctl restart callpanel` |

### Önemli Dosyalar

| Dosya | Konum |
|-------|-------|
| Uygulama | `/home/callpanel/callPanel/` |
| Veritabanı | `/home/callpanel/callPanel/data/call_panel.db` |
| Loglar | `/home/callpanel/callPanel/logs/` |
| Servis | `/etc/systemd/system/callpanel.service` |
| Nginx | `/etc/nginx/sites-available/callpanel` |

---

## ✅ Kurulum Tamamlandı!

Artık Call Center Panel VPS'de çalışıyor!

**Erişim:**
- HTTP: `http://VPS_IP:8501`
- HTTPS (Nginx): `https://callpanel.sirketiniz.com`

**Giriş:**
- Kullanıcı: `admin`
- Şifre: `admin123` (DEĞİŞTİR!)

**Destek:**
- README.md
- USAGE.md
- CHANGELOG.md

🎉 **Başarılar!**
