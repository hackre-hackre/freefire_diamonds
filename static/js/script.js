// Card number formatting
function formatCardNumber(input) {
    let value = input.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    let matches = value.match(/\d{4,16}/g);
    let match = matches && matches[0] || '';
    let parts = [];
    
    for (let i = 0; i < match.length; i += 4) {
        parts.push(match.substring(i, i + 4));
    }
    
    if (parts.length) {
        input.value = parts.join(' ');
    } else {
        input.value = value;
    }
}

// CVV formatting
function formatCVV(input) {
    input.value = input.value.replace(/[^0-9]/g, '').substring(0, 4);
}

// Initialize card formatting
document.addEventListener('DOMContentLoaded', function() {
    // Add card number formatting
    const cardNumberInputs = document.querySelectorAll('input[name="card_number"]');
    cardNumberInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatCardNumber(this);
        });
    });
    
    // Add CVV formatting
    const cvvInputs = document.querySelectorAll('input[name="cvv"]');
    cvvInputs.forEach(input => {
        input.addEventListener('input', function() {
            formatCVV(this);
        });
    });
});
