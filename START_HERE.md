# 🚀 Call Center Panel - Quick Start

## ✅ Installation Complete!

All files and dependencies have been successfully installed.

## 📋 What You Have

- **Admin Panel**: Manage customers, upload Excel files, view statistics
- **Operator Panel**: Pull customers, make calls, log results
- **Database**: SQLite with automatic setup
- **Sample Data**: 8 test customers ready to import
- **Security**: Bcrypt password hashing, role-based access

## 🎯 How to Start (3 Steps)

### 1. Open Terminal and Navigate to Project
```bash
cd /Users/marquis/Desktop/callPanel
```

### 2. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 3. Start the Application
```bash
streamlit run Home.py
```

The app will automatically open in your browser at: **http://localhost:8501**

## 🔐 Login Credentials

**Admin Account** (already created):
- Username: `admin`
- Password: `admin123`

## 📊 Test the Admin Panel

1. Login with admin credentials
2. Click the **"📤 Excel Yükle"** tab
3. Upload `test_customers.xlsx` (8 sample customers)
4. See import success: "✅ 8 başarılı"
5. View stats in **"📈 Dashboard"** tab

## 👥 Create Your First Operator

1. Still in Admin Panel, click **"👥 Operatör Yönetimi"** tab
2. Fill in the form:
   - Username: `operator1`
   - Email: `operator1@test.com`
   - Full Name: `Test Operatör`
   - Password: `test123`
3. Click **"➕ Operatör Ekle"**
4. Success! You'll see the new operator in the list

## 📞 Test the Operator Panel

1. Click **"🚪 Çıkış Yap"** to logout from admin
2. Login with:
   - Username: `operator1`
   - Password: `test123`
3. Click the big **"🎯 Müşteri Çek"** button
4. You'll see a customer assigned with:
   - Name
   - Surname
   - User Code
   - Phone Number
5. Type some notes in the text area
6. Click one of the status buttons:
   - **✅ Ulaşıldı**: Call successful (customer marked complete)
   - **📵 Telefonu Açmadı**: No answer (returns to pool)
   - **🚫 Meşgule Attı**: Declined (returns to pool)
   - **⏳ Meşgul**: Busy (returns to pool)

## 🔄 Test Re-queuing Feature

1. Pull a customer
2. Click **"📵 Telefonu Açmadı"**
3. Pull again - same customer with "**1/3**" attempts shown
4. Click **"📵 Telefonu Açmadı"** again
5. Pull again - same customer with "**2/3**" attempts
6. Click **"📵 Telefonu Açmadı"** one more time
7. Pull again - different customer (previous one now "unreachable")

## 📈 View Your Statistics

- Operator Panel shows:
  - Total calls today
  - Successful calls today
  - Success rate percentage
  
- Admin Panel shows:
  - Total customers
  - Pending in pool
  - Completed
  - Unreachable
  - Currently assigned
  - Per-operator performance

## 📁 Project Files

```
callPanel/
├── Home.py                       ← Start here (Login page)
├── pages/
│   ├── 1_📊_Admin_Panel.py      ← Admin dashboard
│   └── 2_📞_Operator_Panel.py   ← Operator interface
├── services/                     ← Backend logic
├── utils/                        ← Helper functions
├── data/
│   └── call_panel.db            ← Database (auto-created on first run)
├── test_customers.xlsx           ← Sample data for testing
└── README.md                     ← Full documentation
```

## 🛠️ Useful Commands

**Stop the app:**
```
Press Ctrl+C in the terminal
```

**Restart with a different port:**
```bash
streamlit run Home.py --server.port 8502
```

**Reset the database (fresh start):**
```bash
rm data/call_panel.db
streamlit run Home.py
# Database recreates automatically with admin user
```

**Backup the database:**
```bash
cp data/call_panel.db data/backup_$(date +%Y%m%d).db
```

## 📖 Documentation

- **QUICKSTART.md**: Quick installation guide
- **README.md**: Full feature documentation
- **USAGE.md**: Detailed usage instructions
- **IMPLEMENTATION_SUMMARY.md**: Technical details

## 🔧 Troubleshooting

**App won't start:**
- Make sure venv is activated: `source venv/bin/activate`
- Check Python version: `python --version` (should be 3.8+)

**Port 8501 already in use:**
- Use different port: `streamlit run Home.py --server.port 8502`

**Excel upload fails:**
- Check columns: Ad, Soyad, Kullanıcı Kodu, Telefon Numarası
- Ensure unique user codes

**Customer not appearing in pool:**
- Check if already assigned to someone
- Admin: Click "🔄 Takılı Müşterileri Serbest Bırak"

## 🎉 You're Ready!

The system is fully functional and ready for production use.

**Next Steps:**
1. Replace test_customers.xlsx with your real customer data
2. Create actual operator accounts
3. Start making calls!

**For deployment to a server, see README.md "Deployment" section.**

---

## ⚡ Quick Reference Card

| Task | Command |
|------|---------|
| Start app | `source venv/bin/activate && streamlit run Home.py` |
| Stop app | `Ctrl+C` |
| Admin login | admin / admin123 |
| Test operator | operator1 / test123 |
| Test data | test_customers.xlsx |
| Backup DB | `cp data/call_panel.db backups/` |
| Reset DB | `rm data/call_panel.db` |

---

**Questions? Check README.md or the code comments!**

✅ **Status: Ready for Production**
