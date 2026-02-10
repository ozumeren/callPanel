# 📞 Call Center Panel - Quick Reference Card

## 🚀 Start Application
```bash
cd /Users/marquis/Desktop/callPanel
source venv/bin/activate
streamlit run Home.py
```
Access: http://localhost:8501

## 🔐 Login
- **Admin**: admin / admin123
- **Operator**: (create in Admin Panel)

## 📊 Admin Panel

### Excel Upload
1. Go to **"📤 Excel Yükle"** tab
2. Upload .xlsx file with columns:
   - Ad
   - Soyad
   - Kullanıcı Kodu
   - Telefon Numarası
3. Click **"📥 Yükle ve İşle"**

### Dashboard
- View statistics
- Monitor operator performance
- Release stale assignments: **"🔄 Takılı Müşterileri Serbest Bırak"**

### Create Operator
1. Go to **"👥 Operatör Yönetimi"** tab
2. Fill form (username, email, name, password)
3. Click **"➕ Operatör Ekle"**

## 📞 Operator Panel

### Pull Customer
1. Click **"🎯 Müşteri Çek"**
2. Customer assigned automatically

### Log Call
1. View customer info
2. Add notes
3. Select status:
   - **✅ Ulaşıldı** → Complete
   - **📵 Telefonu Açmadı** → Retry
   - **🚫 Meşgule Attı** → Retry
   - **⏳ Meşgul** → Retry

## 🗂️ Files
- **Home.py**: Login page
- **pages/1_📊_Admin_Panel.py**: Admin
- **pages/2_📞_Operator_Panel.py**: Operator
- **data/call_panel.db**: Database
- **test_customers.xlsx**: Sample data

## 🔧 Common Commands
```bash
# Stop app
Ctrl+C

# Different port
streamlit run Home.py --server.port 8502

# Reset database
rm data/call_panel.db
streamlit run Home.py

# Backup database
cp data/call_panel.db backups/backup_$(date +%Y%m%d).db

# Verify installation
python verify_installation.py
```

## 📋 Status Flow
```
pending → assigned → completed (if reached)
                  → unreachable (after 3 attempts)
```

## 🐛 Troubleshooting
| Problem | Solution |
|---------|----------|
| Port in use | `streamlit run Home.py --server.port 8502` |
| Import fails | Check column names (exact match) |
| No customer | Admin: Release stale assignments |
| DB locked | Restart Streamlit |

## 📚 Documentation
- **START_HERE.md**: First-time setup
- **README.md**: Full docs
- **QUICKSTART.md**: Installation
- **USAGE.md**: Usage guide

---
**Support**: Check README.md or code comments
