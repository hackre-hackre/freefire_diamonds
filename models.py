from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid
from cryptography.fernet import Fernet
import base64

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    freefire_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Integer, default=0)
    encryption_key = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    orders = db.relationship('Order', backref='user', lazy=True)
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)

class DiamondPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    diamonds = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)
    discount = db.Column(db.Integer, default=0)
    popular = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('diamond_package.id'), nullable=False)
    diamonds = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    package = db.relationship('DiamondPackage', backref='orders')
    payment_method_rel = db.relationship('PaymentMethod', backref='orders')

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    card_type = db.Column(db.String(20))
    last_four = db.Column(db.String(4), nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    
    # Encrypted fields
    card_holder_name = db.Column(db.Text, nullable=False)
    card_number = db.Column(db.Text, nullable=False)
    cvv = db.Column(db.Text, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def encrypt_data(self, encryption_key):
        """Encrypt sensitive card data"""
        fernet = Fernet(encryption_key)
        self.card_holder_name = fernet.encrypt(self.card_holder_name.encode()).decode()
        self.card_number = fernet.encrypt(self.card_number.encode()).decode()
        self.cvv = fernet.encrypt(self.cvv.encode()).decode()

    def decrypt_data(self, encryption_key):
        """Decrypt sensitive card data"""
        fernet = Fernet(encryption_key)
        try:
            return {
                'card_holder_name': fernet.decrypt(self.card_holder_name.encode()).decode(),
                'card_number': fernet.decrypt(self.card_number.encode()).decode(),
                'cvv': fernet.decrypt(self.cvv.encode()).decode()
            }
        except:
            return None

    def to_dict(self):
        """Return safe payment method data"""
        return {
            'id': self.id,
            'card_type': self.card_type,
            'last_four': self.last_four,
            'expiry_month': self.expiry_month,
            'expiry_year': self.expiry_year,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat()
        }
