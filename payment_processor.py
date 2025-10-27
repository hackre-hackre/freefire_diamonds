import stripe
from flask import current_app
import random
import string
from datetime import datetime

class PaymentProcessor:
    def __init__(self):
        # In production, use real Stripe keys
        self.stripe_public_key = "pk_test_your_public_key"
        self.stripe_secret_key = "sk_test_your_secret_key"
        stripe.api_key = self.stripe_secret_key
    
    def validate_card(self, card_number, expiry_month, expiry_year, cvv):
        """Validate card details"""
        card_number = card_number.replace(' ', '')
        
        if not (13 <= len(card_number) <= 19):
            return False, "Invalid card number length"
        
        if not (1 <= expiry_month <= 12):
            return False, "Invalid expiry month"
        
        current_year = datetime.now().year
        if expiry_year < current_year or (expiry_year == current_year and expiry_month < datetime.now().month):
            return False, "Card has expired"
        
        if len(cvv) not in [3, 4]:
            return False, "Invalid CVV"
        
        # Luhn algorithm validation
        if not self.luhn_check(card_number):
            return False, "Invalid card number"
        
        return True, "Card is valid"
    
    def luhn_check(self, card_number):
        """Luhn algorithm for card number validation"""
        def digits_of(n):
            return [int(d) for d in str(n)]
        digits = digits_of(card_number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d*2))
        return checksum % 10 == 0
    
    def process_payment(self, amount, card_token, description):
        """Process payment using Stripe"""
        try:
            # In production, use actual Stripe integration
            # For demo, we'll simulate successful payment
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency='usd',
                payment_method=card_token,
                confirmation_method='manual',
                confirm=True,
                description=description,
                return_url=current_app.config.get('BASE_URL', '') + '/payment/success'
            )
            
            if payment_intent.status == 'succeeded':
                return True, payment_intent.id, "Payment successful"
            else:
                return False, None, f"Payment failed: {payment_intent.status}"
                
        except stripe.error.CardError as e:
            return False, None, f"Card error: {e.error.message}"
        except Exception as e:
            return False, None, f"Payment error: {str(e)}"
    
    def simulate_payment(self, amount, card_data):
        """Simulate payment processing for demo"""
        import time
        time.sleep(2)
        
        # Simulate random failures (5% failure rate for demo)
        if random.random() < 0.05:
            return False, None, "Payment declined by bank"
        
        transaction_id = f"txn_{''.join(random.choices(string.ascii_uppercase + string.digits, k=14))}"
        return True, transaction_id, "Payment successful"
    
    def get_card_type(self, card_number):
        """Determine card type from number"""
        card_number = card_number.replace(' ', '')
        
        if card_number.startswith('4'):
            return 'visa'
        elif card_number.startswith(('51', '52', '53', '54', '55')):
            return 'mastercard'
        elif card_number.startswith(('34', '37')):
            return 'amex'
        elif card_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38')):
            return 'diners'
        elif card_number.startswith('6011'):
            return 'discover'
        else:
            return 'unknown'

payment_processor = PaymentProcessor()
