#!/usr/bin/env python3
"""
Reset database to fix schema issues
"""

import os
from app import app, db

def reset_database():
    print("🔄 Resetting database to fix schema issues...")
    
    # Remove existing database file (for SQLite)
    db_path = 'freefire_diamonds.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Old database removed")
    
    try:
        with app.app_context():
            # Create all tables with updated schema
            db.create_all()
            print("✅ New database created with updated schema")
            
            # Create sample data
            from app import create_sample_data
            create_sample_data()
            print("✅ Sample data created")
            
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
            print("\n✅ Database fixed! You can now add payment methods.")
        else:
            print("\n💥 Reset failed. Please check the errors above.")
    else:
        print("❌ Reset cancelled.")
