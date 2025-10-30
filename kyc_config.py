class KYCConfig:
    # KYC Tiers and their limits
    KYC_TIERS = {
        'unverified': {
            'name': 'Unverified',
            'daily_limit': 100.00,
            'monthly_limit': 1000.00,
            'features': ['basic_banking'],
            'description': 'Basic account with minimal limits'
        },
        'basic': {
            'name': 'Basic Verification',
            'daily_limit': 1000.00,
            'monthly_limit': 10000.00,
            'features': ['basic_banking', 'crypto_trading'],
            'description': 'Email and phone verified'
        },
        'id_verified': {
            'name': 'ID Verified',
            'daily_limit': 5000.00,
            'monthly_limit': 50000.00,
            'features': ['basic_banking', 'crypto_trading', 'stock_trading'],
            'description': 'Government ID verified'
        },
        'full_kyc': {
            'name': 'Full KYC',
            'daily_limit': 25000.00,
            'monthly_limit': 250000.00,
            'features': ['basic_banking', 'crypto_trading', 'stock_trading', 'high_limits'],
            'description': 'Full identity and address verification'
        }
    }
    
    # Document types
    DOCUMENT_TYPES = ['id_card', 'passport', 'driver_license', 'utility_bill', 'bank_statement']
    
    # Verification requirements for each tier
    VERIFICATION_REQUIREMENTS = {
        'basic': ['email_verified', 'phone_verified'],
        'id_verified': ['email_verified', 'phone_verified', 'id_document_verified'],
        'full_kyc': ['email_verified', 'phone_verified', 'id_document_verified', 'address_verified']
    }
