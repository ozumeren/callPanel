#!/usr/bin/env python3
"""
Verification script to check if Call Center Panel is properly installed
"""
import sys
import os

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} NOT FOUND")
        return False

def check_imports():
    """Check if all required packages are installed"""
    print("\n🔍 Checking Python packages...")
    required_packages = [
        ('streamlit', 'Streamlit'),
        ('pandas', 'Pandas'),
        ('bcrypt', 'bcrypt'),
        ('openpyxl', 'openpyxl'),
        ('yaml', 'PyYAML')
    ]
    
    all_good = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"✅ {name} installed")
        except ImportError:
            print(f"❌ {name} NOT installed")
            all_good = False
    
    return all_good

def check_project_structure():
    """Check if all project files exist"""
    print("\n🔍 Checking project structure...")
    
    files_to_check = [
        ('Home.py', 'Main entry point'),
        ('pages/1_📊_Admin_Panel.py', 'Admin Panel'),
        ('pages/2_📞_Operator_Panel.py', 'Operator Panel'),
        ('services/database.py', 'Database service'),
        ('services/auth_service.py', 'Auth service'),
        ('services/excel_service.py', 'Excel service'),
        ('services/pool_service.py', 'Pool service'),
        ('utils/constants.py', 'Constants'),
        ('utils/helpers.py', 'Helpers'),
        ('.streamlit/config.toml', 'Streamlit config'),
        ('requirements.txt', 'Requirements'),
        ('README.md', 'README'),
        ('INSTALL.md', 'Installation guide'),
        ('test_customers.xlsx', 'Test data')
    ]
    
    all_exist = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def main():
    print("=" * 60)
    print("🚀 Call Center Panel - Installation Verification")
    print("=" * 60)
    
    # Check project structure
    structure_ok = check_project_structure()
    
    # Check imports
    imports_ok = check_imports()
    
    print("\n" + "=" * 60)
    if structure_ok and imports_ok:
        print("✅ All checks passed! Installation is complete.")
        print("\n📝 Next steps:")
        print("1. Activate virtual environment: source venv/bin/activate")
        print("2. Start application: streamlit run Home.py")
        print("3. Login with: admin / admin123")
        print("4. Upload test_customers.xlsx to test")
    else:
        print("❌ Some checks failed. Please review the errors above.")
        print("\n📝 To fix:")
        if not imports_ok:
            print("1. Activate venv: source venv/bin/activate")
            print("2. Install packages: pip install -r requirements.txt")
        if not structure_ok:
            print("3. Ensure you're in the correct directory")
    print("=" * 60)

if __name__ == "__main__":
    main()
