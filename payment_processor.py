"""
Mock Payment Processor - Simulates payment processing without external dependencies
"""
import random
import string

class PaymentProcessor:
    def __init__(self):
        self.supported_cards = ['visa', 'mastercard', 'amex', 'discover']
    
    def validate_card(self, card_number, expiry_month, expiry_year, cvv):
        """Validate card details"""
        try:
            # Remove spaces from card number
            card_number = card_number.replace(' ', '')
            
            # Basic validation
            if len(card_number) < 13 or len(card_number) > 19:
                return False, "Invalid card number length"
            
            if not card_number.isdigit():
                return False, "Card number must contain only digits"
            
            if expiry_month < 1 or expiry_month > 12:
                return False, "Invalid expiry month"
            
            current_year = 2024  # You might want to make this dynamic
            if expiry_year < current_year:
                return False, "Card has expired"
            
            if expiry_year == current_year and expiry_month < 10:  # Current month check
                return False, "Card has expired"
            
            if len(cvv) not in [3, 4] or not cvv.isdigit():
                return False, "Invalid CVV"
            
            return True, "Card validated successfully"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_card_type(self, card_number):
        """Determine card type based on number"""
        card_number = card_number.replace(' ', '')
        
        if card_number.startswith('4'):
            return 'visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'mastercard'
        elif card_number.startswith(('34', '37')):
            return 'amex'
        elif card_number.startswith('6'):
            return 'discover'
        else:
            return 'unknown'
    
    def simulate_payment(self, amount, card_data):
        """Simulate a payment transaction"""
        try:
            # Generate a fake transaction ID
            transaction_id = 'txn_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=14))
            
            # Simulate 95% success rate
            success = random.random() > 0.05
            
            if success:
                return True, transaction_id, f"Payment of ${amount:.2f} processed successfully"
            else:
                return False, None, "Payment declined: Insufficient funds"
                
        except Exception as e:
            return False, None, f"Payment error: {str(e)}"

# Create global instance
payment_processor = PaymentProcessor()
