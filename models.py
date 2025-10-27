from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from cryptography.fernet import Fernet
import base64

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    freefire_id = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Integer, default=0)
    encryption_key = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='user', lazy=True)
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True)

class DiamondPackage(db.Model):
    __tablename__ = 'diamond_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    diamonds = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # USD price
    price_ngn = db.Column(db.Float, default=0.0)  # Naira price
    original_price = db.Column(db.Float, nullable=False)  # USD original price
    original_price_ngn = db.Column(db.Float, default=0.0)  # Naira original price
    discount = db.Column(db.Integer, default=0)
    popular = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', backref='package', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'diamonds': self.diamonds,
            'price': self.price,
            'price_ngn': self.price_ngn,
            'original_price': self.original_price,
            'original_price_ngn': self.original_price_ngn,
            'discount': self.discount,
            'popular': self.popular,
            'description': self.description
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('diamond_packages.id'), nullable=False)
    diamonds = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'), nullable=True)
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'package_id': self.package_id,
            'diamonds': self.diamonds,
            'amount': self.amount,
            'status': self.status,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_type = db.Column(db.String(20), nullable=False)
    last_four = db.Column(db.String(4), nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)
    encrypted_card_number = db.Column(db.Text, nullable=False)
    encrypted_cvv = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - using different name to avoid conflicts
    payment_orders = db.relationship('Order', backref='payment_method_ref', lazy=True)
    
    # Temporary properties for encryption/decryption (not stored in DB)
    @property
    def card_number(self):
        """This is only used before encryption"""
        return getattr(self, '_card_number', None)
    
    @card_number.setter
    def card_number(self, value):
        """Set the card number before encryption"""
        self._card_number = value
    
    @property
    def cvv(self):
        """This is only used before encryption"""
        return getattr(self, '_cvv', None)
    
    @cvv.setter
    def cvv(self, value):
        """Set the CVV before encryption"""
        self._cvv = value
    
    def encrypt_data(self, encryption_key):
        """Encrypt card number and CVV"""
        try:
            fernet = Fernet(encryption_key)
            if hasattr(self, '_card_number') and self._card_number:
                self.encrypted_card_number = fernet.encrypt(self._card_number.encode()).decode()
            if hasattr(self, '_cvv') and self._cvv:
                self.encrypted_cvv = fernet.encrypt(self._cvv.encode()).decode()
            return True
        except Exception as e:
            print(f"Encryption error: {e}")
            return False
    
    def decrypt_data(self, encryption_key):
        """Decrypt card number and CVV"""
        try:
            fernet = Fernet(encryption_key)
            card_number = fernet.decrypt(self.encrypted_card_number.encode()).decode()
            cvv = fernet.decrypt(self.encrypted_cvv.encode()).decode()
            return {
                'card_number': card_number,
                'cvv': cvv,
                'card_holder_name': self.card_holder_name,
                'expiry_month': self.expiry_month,
                'expiry_year': self.expiry_year
            }
        except Exception as e:
            print(f"Decryption error: {e}")
            return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'card_type': self.card_type,
            'last_four': self.last_four,
            'expiry_month': self.expiry_month,
            'expiry_year': self.expiry_year,
            'card_holder_name': self.card_holder_name,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
