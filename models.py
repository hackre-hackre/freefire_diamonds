from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    freefire_id = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Integer, default=0)
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
    price = db.Column(db.Float, nullable=False)
    price_ngn = db.Column(db.Float, default=0.0)
    original_price = db.Column(db.Float, nullable=False)
    original_price_ngn = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Integer, default=0)
    popular = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders = db.relationship('Order', backref='package', lazy=True)

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

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    card_type = db.Column(db.String(20), nullable=False)
    card_number = db.Column(db.String(19), nullable=False)  # Store full card number
    last_four = db.Column(db.String(4), nullable=False)
    expiry_month = db.Column(db.Integer, nullable=False)
    expiry_year = db.Column(db.Integer, nullable=False)
    card_holder_name = db.Column(db.String(100), nullable=False)
    cvv = db.Column(db.String(4), nullable=False)  # Store CVV directly
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payment_orders = db.relationship('Order', backref='payment_method_ref', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'card_type': self.card_type,
            'card_number': self.card_number,  # Full card number visible
            'last_four': self.last_four,
            'expiry_month': self.expiry_month,
            'expiry_year': self.expiry_year,
            'card_holder_name': self.card_holder_name,
            'cvv': self.cvv,  # CVV visible
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
