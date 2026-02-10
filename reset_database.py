#!/usr/bin/env python3
"""
Database Reset Script
Deletes existing database and creates a fresh one with admin user
"""

import os
import sys
from services.database import init_database, DB_PATH

def reset_database():
    """Reset database to initial state"""

    # Check if database exists
    if os.path.exists(DB_PATH):
        print(f"🗑️  Mevcut database siliniyor: {DB_PATH}")
        os.remove(DB_PATH)
        print("✅ Database silindi!")
    else:
        print(f"ℹ️  Database bulunamadı: {DB_PATH}")

    # Create fresh database
    print("🔨 Yeni database oluşturuluyor...")
    init_database()
    print("✅ Yeni database oluşturuldu!")

    print("\n" + "="*50)
    print("🎉 Database başarıyla sıfırlandı!")
    print("="*50)
    print("\n📝 Varsayılan Giriş Bilgileri:")
    print("   Kullanıcı: admin")
    print("   Şifre: admin123")
    print("\n⚠️  İlk girişten sonra şifreyi değiştirmeyi unutmayın!")
    print("\n🚀 Uygulamayı başlatmak için:")
    print("   streamlit run Home.py")

if __name__ == "__main__":
    # Confirmation prompt
    print("\n" + "="*50)
    print("⚠️  DİKKAT: DATABASE SIFIRLAMA")
    print("="*50)
    print("Bu işlem:")
    print("  • Tüm müşteri kayıtlarını")
    print("  • Tüm arama loglarını")
    print("  • Tüm operatörleri")
    print("  • Tüm CSV yükleme kayıtlarını")
    print("  • Tüm reactivation kayıtlarını")
    print("\nKALICI OLARAK SİLECEK!")
    print("="*50)

    response = input("\nDevam etmek istiyor musunuz? (evet/hayir): ").strip().lower()

    if response in ['evet', 'e', 'yes', 'y']:
        reset_database()
    else:
        print("❌ İşlem iptal edildi.")
        sys.exit(0)
