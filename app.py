from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from config import get_db_connection

# Authentication
from routes.auth import Register, Login

# Banking
from routes.banking import Balance, Deposit, Withdraw

# Transactions
from routes.transactions import TransactionHistory, TransactionDetail

# Transfers
from routes.transfers import Transfer, Beneficiaries

# Accounts
from routes.accounts import Accounts, AccountDetail

# Crypto
from routes.crypto import (
    CryptoWallets,
    CryptoDeposit,
    CryptoWithdraw,
    CryptoSell
)

# Crypto Funding
from routes.crypto_funding import (
    RequestCryptoFunding,
    CryptoToBankDeposit,
    BankToCryptoWithdraw,
    SimulateCryptoDeposit,
    GetUserPendingFundingRequests
)

# Stocks
from routes.stocks import (
    StockMarket,
    StockDetail,
    BuyStock,
    SellStock,
    StockPortfolio,
    StockTransactions
)

# Profile & KYC
from routes.profile import (
    UserProfile,
    VerifyPhone,
    VerifyEmail,
    KYCDocuments
)

# Admin
from routes.admin import (
    AdminRegister,
    AdminLogin,
    AdminUsers,
    AdminUserAccounts,
    AdminAdjustBalance,
    AdminAddStock,
    AdminUpdateStockPrice,
    AdminAllStocks,
    AdminStockTransactions,
    AdminCryptoFundingRequests,
    AdminApproveCryptoFunding,
    AdminRejectCryptoFunding
)

# -----------------------------------------------------------
# ✅ APP INITIALIZATION
# -----------------------------------------------------------
app = Flask(__name__)
app.config.from_object('config.Config')

# ✅ Universal CORS (so frontend can access it when deployed)
CORS(app, resources={r"/api/*": {"origins": "*"}})

api = Api(app)

# -----------------------------------------------------------
# ✅ ROUTES REGISTRATION
# -----------------------------------------------------------

# Authentication
api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')

# Banking
api.add_resource(Balance, '/api/balance')
api.add_resource(Deposit, '/api/deposit')
api.add_resource(Withdraw, '/api/withdraw')

# Transactions
api.add_resource(TransactionHistory, '/api/transactions')
api.add_resource(TransactionDetail, '/api/transactions/<int:transaction_id>')

# Transfers
api.add_resource(Transfer, '/api/transfer')
api.add_resource(Beneficiaries, '/api/beneficiaries')

# Accounts
api.add_resource(Accounts, '/api/accounts')
api.add_resource(AccountDetail, '/api/accounts/<string:account_number>')

# Crypto
api.add_resource(CryptoWallets, '/api/crypto/wallets')
api.add_resource(CryptoDeposit, '/api/crypto/deposit')
api.add_resource(CryptoWithdraw, '/api/crypto/withdraw')
api.add_resource(CryptoSell, '/api/crypto/sell')

# Crypto funding
api.add_resource(CryptoToBankDeposit, '/api/crypto/fund-bank')
api.add_resource(RequestCryptoFunding, '/api/crypto/request-funding')
api.add_resource(BankToCryptoWithdraw, '/api/bank/withdraw-to-crypto')
api.add_resource(SimulateCryptoDeposit, '/api/crypto/simulate-deposit')
api.add_resource(GetUserPendingFundingRequests, '/api/crypto/pending-funding-requests')

# Stocks
api.add_resource(StockMarket, '/api/stocks/market')
api.add_resource(StockDetail, '/api/stocks/<string:symbol>')
api.add_resource(BuyStock, '/api/stocks/buy')
api.add_resource(SellStock, '/api/stocks/sell')
api.add_resource(StockPortfolio, '/api/stocks/portfolio')
api.add_resource(StockTransactions, '/api/stocks/transactions')

# Profile & KYC
api.add_resource(UserProfile, '/api/profile')
api.add_resource(VerifyPhone, '/api/verify-phone')
api.add_resource(VerifyEmail, '/api/verify-email')
api.add_resource(KYCDocuments, '/api/kyc/documents')

# Admin
api.add_resource(AdminRegister, '/api/admin/register')
api.add_resource(AdminLogin, '/api/admin/login')
api.add_resource(AdminUsers, '/api/admin/users')
api.add_resource(AdminUserAccounts, '/api/admin/users/<int:user_id>/accounts')
api.add_resource(AdminAdjustBalance, '/api/admin/adjust-balance')
api.add_resource(AdminAddStock, '/api/admin/stocks/add')
api.add_resource(AdminUpdateStockPrice, '/api/admin/stocks/update-price')
api.add_resource(AdminAllStocks, '/api/admin/stocks')
api.add_resource(AdminStockTransactions, '/api/admin/stock-transactions')
api.add_resource(AdminCryptoFundingRequests, '/api/admin/crypto-funding-requests')
api.add_resource(AdminApproveCryptoFunding, '/api/admin/approve-crypto-funding')
api.add_resource(AdminRejectCryptoFunding, '/api/admin/reject-crypto-funding')

# -----------------------------------------------------------
# ✅ UTILITY ROUTES
# -----------------------------------------------------------
@app.route('/')
def home():
    return jsonify({
        'message': 'Welcome to NexaBank API!',
        'status': 'running'
    })

@app.route('/test-db')
def test_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return jsonify({'message': 'Database connection successful!'})
    else:
        return jsonify({'error': 'Database connection failed!'}), 500


# -----------------------------------------------------------
# ✅ RUN SERVER (WORKS LOCALLY + ON RAILWAY)
# -----------------------------------------------------------
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))  # Railway sets PORT automatically
    app.run(debug=True, host='0.0.0.0', port=port)