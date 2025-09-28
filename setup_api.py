#!/usr/bin/env python
"""
Automated setup script for MoneyManager API integration
Run this script to easily configure your API keys
"""

import os
import sys

def main():
    print("🚀 MONEYMANAGER API SETUP")
    print("=" * 50)
    print("This script will help you configure real market data APIs")
    print()
    
    # Check if .env exists
    env_file = '.env'
    template_file = '.env_template'
    
    if not os.path.exists(template_file):
        print("❌ .env_template not found!")
        return
    
    # Copy template if .env doesn't exist
    if not os.path.exists(env_file):
        print("📋 Creating .env file from template...")
        with open(template_file, 'r') as template:
            with open(env_file, 'w') as env:
                env.write(template.read())
        print("✅ .env file created!")
    else:
        print("✅ .env file already exists")
    
    print()
    print("🔑 API KEY CONFIGURATION")
    print("-" * 30)
    
    # Get user input for API keys
    api_keys = {}
    
    print("\n1. ALPHA VANTAGE (RECOMMENDED - FREE)")
    print("   Get your free key from: https://www.alphavantage.co/support/#api-key")
    alpha_key = input("   Enter your Alpha Vantage API key (or press Enter to skip): ").strip()
    if alpha_key:
        api_keys['ALPHA_VANTAGE_API_KEY'] = alpha_key
    
    print("\n2. TWELVE DATA (OPTIONAL)")
    print("   Get key from: https://twelvedata.com/")
    twelve_key = input("   Enter your Twelve Data API key (or press Enter to skip): ").strip()
    if twelve_key:
        api_keys['TWELVE_DATA_API_KEY'] = twelve_key
    
    print("\n3. IEX CLOUD (OPTIONAL)")
    print("   Get key from: https://iexcloud.io/")
    iex_key = input("   Enter your IEX Cloud API key (or press Enter to skip): ").strip()
    if iex_key:
        api_keys['IEX_CLOUD_API_KEY'] = iex_key
    
    # Update .env file
    if api_keys:
        print("\n📝 Updating .env file...")
        update_env_file(env_file, api_keys)
        print("✅ API keys configured!")
    else:
        print("\n⚠️  No API keys provided - system will use fallback data")
    
    print("\n🧪 TESTING CONFIGURATION...")
    test_setup()
    
    print("\n🎉 SETUP COMPLETE!")
    print("=" * 50)
    print("Next steps:")
    print("1. Run: python manage.py migrate")
    print("2. Run: python manage.py runserver")
    print("3. Go to: http://127.0.0.1:8000/portfolios/")
    print("4. Create your first portfolio with real market data!")


def update_env_file(env_file, api_keys):
    """Update .env file with new API keys"""
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    with open(env_file, 'w') as f:
        for line in lines:
            updated = False
            for key, value in api_keys.items():
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                    updated = True
                    break
            
            if not updated:
                f.write(line)


def test_setup():
    """Test if Django can load the configuration"""
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moneymanager.settings.local')
        django.setup()
        
        from django.conf import settings
        
        # Check if API settings are loaded
        if hasattr(settings, 'API_SETTINGS'):
            alpha_key = settings.API_SETTINGS.get('ALPHA_VANTAGE_API_KEY', '')
            if alpha_key and alpha_key != 'your_alpha_vantage_key_here':
                print("✅ Django configuration loaded successfully!")
                return True
        
        print("⚠️  Configuration loaded but no API keys detected")
        return False
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("Please check the error and try again")