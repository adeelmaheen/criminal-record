#!/usr/bin/env python
"""
Debug script to test scraper setup without actually scraping data.
This helps identify configuration issues before running the full scraper.
"""

import os
import sys
import django
from pathlib import Path

# Add the Django project root to the Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crimrec.settings')
django.setup()

from dotenv import load_dotenv
load_dotenv()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['ECLERKS_EMAIL', 'ECLERKS_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"  ❌ {var}: Not set")
        else:
            print(f"  ✅ {var}: {'*' * len(value)}")
    
    if missing_vars:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with your credentials.")
        return False
    
    print("✅ All required environment variables are set!")
    return True

def test_chrome_driver():
    """Test Chrome driver initialization"""
    print("\n🔍 Testing Chrome driver initialization...")
    
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.chrome.options import Options
        
        print("  ✅ Selenium and undetected_chromedriver imported successfully")
        
        # Test basic Chrome options
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        print("  ✅ Chrome options configured")
        
        # Try to initialize driver (this may take a moment)
        print("  🔄 Initializing Chrome driver (this may take a moment)...")
        driver = uc.Chrome(options=options, version_main=None)
        
        print("  ✅ Chrome driver initialized successfully!")
        
        # Test basic functionality
        driver.get("https://www.google.com")
        title = driver.title
        print(f"  ✅ Successfully navigated to Google (title: {title[:50]}...)")
        
        driver.quit()
        print("  ✅ Chrome driver closed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chrome driver error: {str(e)}")
        print("  💡 Try installing/updating Chrome browser")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from django.db import connection
        from scraper.models import CriminalRecord
        
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        
        print("  ✅ Database connection successful")
        
        # Test model queries
        count = CriminalRecord.objects.count()
        print(f"  ✅ Current records in database: {count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {str(e)}")
        print("  💡 Try running: python manage.py migrate")
        return False

def test_scraper_initialization():
    """Test scraper class initialization"""
    print("\n🔍 Testing scraper initialization...")
    
    try:
        from scraper.scrapers import EClerksScraper
        
        # Test with headless mode to avoid opening browser
        scraper = EClerksScraper(headless=True)
        print("  ✅ EClerksScraper initialized successfully")
        
        # Test credentials
        print(f"  ✅ Email configured: {scraper.login_email[:5]}{'*' * 10}")
        print(f"  ✅ Password configured: {'*' * 10}")
        
        # Clean up
        scraper.quit()
        print("  ✅ Scraper cleaned up successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Scraper initialization error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Criminal Records Scraper - Debug Test\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Database Connection", test_database_connection),
        ("Chrome Driver", test_chrome_driver),
        ("Scraper Initialization", test_scraper_initialization),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ Unexpected error in {test_name}: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    print("="*50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Your scraper should work correctly.")
        print("You can now run: python manage.py run_scraper --max-pages 1")
    else:
        print("⚠️  Some tests failed. Please fix the issues above before running the scraper.")
    
    print("="*50)

if __name__ == "__main__":
    main() 