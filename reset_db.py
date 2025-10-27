#!/usr/bin/env python3
"""
Reset database and start fresh with Naira prices
"""

import os
import sys

def reset_database():
    print("🔄 Resetting database...")
    
    db_path = 'freefire_diamonds.db'
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Old database removed")
    else:
        print("ℹ️  No existing database found")
    
    try:
        # Recreate database using app
        from app import app, db
        with app.app_context():
            db.create_all()
            print("✅ New database created with updated schema")
            
            # Create sample data
            from app import create_sample_data
            create_sample_data()
            print("✅ Sample data created with Naira prices")
            
        print("\n🎉 Database reset completed successfully!")
        print("🚀 You can now run: python app.py")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("⚠️  WARNING: This will delete all existing data!")
    confirmation = input("Type 'YES' to continue: ")
    
    if confirmation == 'YES':
        success = reset_database()
        if success:
            print("\n✅ Ready to go! Your app now has Naira prices.")
        else:
            print("\n💥 Reset failed. Please check the errors above.")
    else:
        print("❌ Reset cancelled.")
