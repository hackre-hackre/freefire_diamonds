# setup.py
from app import app, db
from models import User, DiamondPackage
from werkzeug.security import generate_password_hash
from cryptography.fernet import Fernet
import base64

def setup_database():
    with app.app_context():
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        print("🗑️  Dropped old database")
        print("✅ Created new database tables")
        
        # Create sample packages
        packages = [
            DiamondPackage(name="Starter Pack", diamonds=100, price=0.99, original_price=1.99, discount=50, description="Perfect for beginners"),
            DiamondPackage(name="Elite Pack", diamonds=500, price=4.99, original_price=6.99, discount=29, popular=True, description="Great value package"),
            DiamondPackage(name="Pro Pack", diamonds=1200, price=9.99, original_price=14.99, discount=33, description="For serious players"),
            DiamondPackage(name="VIP Pack", diamonds=2500, price=19.99, original_price=29.99, discount=33, popular=True, description="Best seller"),
            DiamondPackage(name="Ultimate Pack", diamonds=5000, price=34.99, original_price=49.99, discount=30, description="Maximum diamonds"),
            DiamondPackage(name="Mega Pack", diamonds=10000, price=64.99, original_price=89.99, discount=28, description="For ultimate gamers"),
        ]
        
        for package in packages:
            db.session.add(package)
        print("✅ Added diamond packages")
        
        # Create admin user
        encryption_key = base64.urlsafe_b64encode(Fernet.generate_key())
        admin_user = User(
            username='admin',
            email='admin@freefirediamonds.com',
            password_hash=generate_password_hash('admin123'),
            freefire_id='000000000',
            encryption_key=encryption_key.decode(),
            is_admin=True
        )
        db.session.add(admin_user)
        
        # Create demo user
        demo_key = base64.urlsafe_b64encode(Fernet.generate_key())
        demo_user = User(
            username='demo',
            email='demo@example.com',
            password_hash=generate_password_hash('password123'),
            freefire_id='123456789',
            encryption_key=demo_key.decode()
        )
        db.session.add(demo_user)
        
        db.session.commit()
        print("✅ Created admin and demo users")
        print("\n🎉 Database setup complete!")
        print("👤 Admin credentials: username='admin', password='admin123'")
        print("👤 Demo credentials: username='demo', password='password123'")
        print("\n🚀 Start the application with: python app.py")

if __name__ == '__main__':
    setup_database()
