from app import app, db
import os

print("🔧 Starting complete database reset...")

with app.app_context():
    # Force drop all tables
    print("🗑️  Dropping all tables...")
    db.drop_all()
    
    # Create all tables with current schema
    print("🔄 Creating all tables...")
    db.create_all()
    
    # Create sample data
    print("📦 Creating sample data...")
    from app import create_sample_data
    create_sample_data()
    
    print("✅ Database reset complete!")
    
    # Verify the schema was created correctly
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    
    print("\n📊 Database Schema Verification:")
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")
    
    if 'payment_methods' in tables:
        columns = inspector.get_columns('payment_methods')
        print("\nPayment Methods Columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
