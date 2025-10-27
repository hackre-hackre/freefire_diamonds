#!/usr/bin/env python3
"""
Safe migration script to add Naira prices to diamond packages
"""

import sqlite3
import os
import sys

def safe_migration():
    print("🔄 Starting safe migration for Naira prices...")
    
    db_path = 'freefire_diamonds.db'
    
    if not os.path.exists(db_path):
        print("❌ Database not found. Please run the app first to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Checking current database structure...")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Found tables: {[table[0] for table in tables]}")
        
        if 'diamond_packages' not in [table[0] for table in tables]:
            print("❌ diamond_packages table not found!")
            return False
        
        # Check diamond_packages structure
        cursor.execute("PRAGMA table_info(diamond_packages)")
        columns = cursor.fetchall()
        print("📦 Current diamond_packages columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Safely add Naira columns if they don't exist
        column_names = [col[1] for col in columns]
        
        if 'price_ngn' not in column_names:
            print("➕ Adding price_ngn column...")
            cursor.execute("ALTER TABLE diamond_packages ADD COLUMN price_ngn REAL DEFAULT 0")
            print("✅ Added price_ngn column")
        else:
            print("✅ price_ngn column already exists")
        
        if 'original_price_ngn' not in column_names:
            print("➕ Adding original_price_ngn column...")
            cursor.execute("ALTER TABLE diamond_packages ADD COLUMN original_price_ngn REAL DEFAULT 0")
            print("✅ Added original_price_ngn column")
        else:
            print("✅ original_price_ngn column already exists")
        
        # Update prices with Naira values (1 USD = 1500 NGN)
        exchange_rate = 1500
        print(f"💱 Converting prices using exchange rate: 1 USD = {exchange_rate} NGN")
        
        cursor.execute("SELECT id, name, price, original_price FROM diamond_packages")
        packages = cursor.fetchall()
        
        print(f"📦 Updating {len(packages)} packages with Naira prices...")
        
        updated_count = 0
        for package_id, name, price, original_price in packages:
            price_ngn = price * exchange_rate
            original_price_ngn = original_price * exchange_rate
            
            cursor.execute(
                "UPDATE diamond_packages SET price_ngn = ?, original_price_ngn = ? WHERE id = ?",
                (price_ngn, original_price_ngn, package_id)
            )
            updated_count += 1
            print(f"   ✅ {name}: ${price} → ₦{price_ngn:,.0f}")
        
        # Verify the updates
        cursor.execute("SELECT id, name, price, price_ngn, original_price, original_price_ngn FROM diamond_packages")
        updated_packages = cursor.fetchall()
        
        print("\n🔍 Verification of updated packages:")
        for pkg_id, pkg_name, usd_price, ngn_price, usd_original, ngn_original in updated_packages:
            print(f"   📊 {pkg_name}:")
            print(f"      Current: ${usd_price} / ₦{ngn_price:,.0f}")
            print(f"      Original: ${usd_original} / ₦{ngn_original:,.0f}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 Migration completed successfully! Updated {updated_count} packages.")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = safe_migration()
    if success:
        print("\n🚀 You can now run your app with Naira prices!")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
