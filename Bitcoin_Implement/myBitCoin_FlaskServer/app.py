from flask import Flask, request, jsonify,render_template, render_template_string, redirect, url_for, session, flash
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from typing import Dict, List, Optional
from functools import wraps

# Bitcoin 클래스들 import (위에서 작성한 코드)
from bitcoin_utxo import (
    Wallet, Transaction, Blockchain, UTXO, 
    TransactionInput, TransactionOutput, UTXOPool
)

from datetime import datetime
import base64
from cryptography.fernet import Fernet
import hashlib 


app = Flask(__name__)
CORS(app)
### secret key 설정 ### 
secret_key_env = os.environ.get('SECRET_KEY')
if secret_key_env is None:
    raise RuntimeError("SECRET_KEY environment variable is not set.")
app.secret_key = secret_key_env

# 전역 블록체인 인스턴스
blockchain = Blockchain()

# 지갑 저장소 (실제 운영에서는 데이터베이스 사용)
wallets: Dict[str, Wallet] = {}

# 데이터 영속성을 위한 파일 경로
BLOCKCHAIN_FILE = "blockchain_data.json"
WALLETS_FILE = "wallets_data.json"
USERS_FILE = "users.json"


def load_users():
    """사용자 데이터 로드"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load users data: {e}")
            return []
    return []

def save_users(users):
    """사용자 데이터 저장"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to save users data: {e}")

def login_required(f):
    """로그인 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_data():
    """서버 시작 시 데이터 로드"""
    global blockchain, wallets
    
    # 블록체인 데이터 로드
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, 'r') as f:
                data = json.load(f)
                blockchain.chain = data.get('chain', [])
                # UTXO 풀 재구성 (실제로는 더 복잡한 로직 필요)
        except Exception as e:
            print(f"Failed to load blockchain data: {e}")
    
    # 지갑 데이터 로드
    if os.path.exists(WALLETS_FILE):
        try:
            with open(WALLETS_FILE, 'r') as f:
                wallet_data = json.load(f)
                for address, private_key_hex in wallet_data.items():
                    wallet = Wallet()
                    wallet.private_key = bytes.fromhex(private_key_hex)
                    wallet.public_key = wallet._generate_public_key(wallet.private_key)
                    wallet.address = wallet._generate_address(wallet.public_key)
                    wallets[address] = wallet
        except Exception as e:
            print(f"Failed to load wallet data: {e}")

def save_data():
    """데이터 저장"""
    try:
        # 블록체인 데이터 저장
        with open(BLOCKCHAIN_FILE, 'w') as f:
            json.dump({
                'chain': blockchain.chain,
                'utxos': {k: v.to_dict() for k, v in blockchain.utxo_pool.utxos.items()}
            }, f, indent=2)
        
        # 지갑 데이터 저장
        wallet_data = {address: wallet.get_private_key_hex() 
                      for address, wallet in wallets.items()}
        with open(WALLETS_FILE, 'w') as f:
            json.dump(wallet_data, f, indent=2)
    except Exception as e:
        print(f"Failed to save data: {e}")

@app.route('/')
def login():
    """로그인 페이지"""
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    return render_template("login.html")

@app.route('/join')
def join():
    """회원가입 페이지"""
    return render_template("join.html")


@app.route('/authenticate', methods=['POST'])
def authenticate():
    """로그인 처리"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        flash('사용자명과 비밀번호를 모두 입력해주세요.')
        return redirect(url_for('login'))
    
    # 사용자 데이터 로드
    users = load_users()
    
    # 사용자 찾기 및 비밀번호 확인
    for user in users:
        if user['username'] == username:
            if check_password_hash(user['hashed_password'], password):
                session['user'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('비밀번호가 올바르지 않습니다.')
                return redirect(url_for('login'))
    
    flash('존재하지 않는 사용자입니다.')
    return redirect(url_for('login'))


@app.route('/register', methods=['POST'])
def register():
    """회원가입 처리"""
    username = request.form.get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # 입력 검증
    if not username or not password or not confirm_password:
        flash('모든 필드를 입력해주세요.')
        return redirect(url_for('join'))
    
    if len(username) < 3:
        flash('사용자명은 3자 이상이어야 합니다.')
        return redirect(url_for('join'))
    
    if len(password) < 6:
        flash('비밀번호는 6자 이상이어야 합니다.')
        return redirect(url_for('join'))
    
    if password != confirm_password:
        flash('비밀번호가 일치하지 않습니다.')
        return redirect(url_for('join'))
    
    # 사용자 데이터 로드
    users = load_users()
    
    # 중복 사용자 확인
    for user in users:
        if user['username'] == username:
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('join'))
    
    # 새 사용자 추가
    hashed_password = generate_password_hash(password)
    new_user = {
        'username': username,
        'hashed_password': hashed_password
    }
    
    users.append(new_user)
    save_users(users)
    
    # 세션 설정하고 대시보드로 이동
    session['user'] = username
    return redirect(url_for('dashboard'))

def logout():
    """로그아웃"""
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    """새 지갑 생성"""
    try:
        wallet = Wallet()
        address = wallet.get_address()
        wallets[address] = wallet
        
        save_data()
        
        return jsonify({
            'success': True,
            'data': {
                'address': address,
                'public_key': wallet.get_public_key_hex(),
                'private_key': wallet.get_private_key_hex()  # 주의: 실제로는 보안상 반환하지 않음
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wallet/<address>/balance', methods=['GET'])
def get_balance(address):
    """지갑 잔액 조회"""
    try:
        balance = blockchain.get_balance(address)
        utxos = blockchain.utxo_pool.get_utxos_by_address(address)
        
        return jsonify({
            'success': True,
            'data': {
                'address': address,
                'balance': balance,
                'utxo_count': len(utxos)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/wallet/<address>/utxos', methods=['GET'])
def get_utxos(address):
    """지갑의 UTXO 목록 조회"""
    try:
        utxos = blockchain.utxo_pool.get_utxos_by_address(address)
        utxo_list = [utxo.to_dict() for utxo in utxos]
        
        return jsonify({
            'success': True,
            'data': {
                'address': address,
                'utxos': utxo_list,
                'total_amount': sum(utxo.amount for utxo in utxos)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transaction/create', methods=['POST'])
def create_transaction():
    """트랜잭션 생성"""
    try:
        data = request.get_json()
        sender_address = data.get('sender_address')
        receiver_address = data.get('receiver_address')
        amount = float(data.get('amount'))
        
        # 송신자 지갑 확인
        if sender_address not in wallets:
            return jsonify({
                'success': False, 
                'error': 'Sender wallet not found'
            }), 400
        
        sender_wallet = wallets[sender_address]
        
        # 트랜잭션 생성
        transaction = blockchain.create_transaction(
            sender_address, receiver_address, amount, sender_wallet
        )
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Failed to create transaction (insufficient funds)'
            }), 400
        
        return jsonify({
            'success': True,
            'data': {
                'transaction': transaction.to_dict(),
                'message': 'Transaction created successfully'
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/transaction/send', methods=['POST'])
def send_transaction():
    """트랜잭션 전송 (블록체인에 추가)"""
    try:
        data = request.get_json()
        sender_address = data.get('sender_address')
        receiver_address = data.get('receiver_address')
        amount = float(data.get('amount'))
        
        # 송신자 지갑 확인
        if sender_address not in wallets:
            return jsonify({
                'success': False,
                'error': 'Sender wallet not found'
            }), 400
        
        sender_wallet = wallets[sender_address]
        
        # 트랜잭션 생성
        transaction = blockchain.create_transaction(
            sender_address, receiver_address, amount, sender_wallet
        )
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Failed to create transaction'
            }), 400
        
        # 트랜잭션을 대기 목록에 추가
        if blockchain.add_transaction(transaction):
            save_data()
            return jsonify({
                'success': True,
                'data': {
                    'transaction_id': transaction.tx_id,
                    'message': 'Transaction added to pending pool'
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Transaction validation failed'
            }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mine', methods=['POST'])
def mine_block():
    """블록 채굴"""
    try:
        data = request.get_json()
        miner_address = data.get('miner_address')
        
        if not miner_address:
            return jsonify({
                'success': False,
                'error': 'Miner address is required'
            }), 400
        
        # 블록 채굴
        block = blockchain.mine_block(miner_address)
        save_data()
        
        return jsonify({
            'success': True,
            'data': {
                'block': block,
                'message': f'Block {block["index"]} mined successfully',
                'transactions_processed': len(blockchain.pending_transactions) + 1  # +1 for reward
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """전체 블록체인 조회"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'chain': blockchain.chain,
                'length': len(blockchain.chain),
                'pending_transactions': len(blockchain.pending_transactions)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/blockchain/block/<int:index>', methods=['GET'])
def get_block(index):
    """특정 블록 조회"""
    try:
        if index < 1 or index > len(blockchain.chain):
            return jsonify({
                'success': False,
                'error': 'Block not found'
            }), 404
        
        block = blockchain.chain[index - 1]
        return jsonify({
            'success': True,
            'data': {'block': block}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pending-transactions', methods=['GET'])
def get_pending_transactions():
    """대기 중인 트랜잭션 조회"""
    try:
        pending = [tx.to_dict() for tx in blockchain.pending_transactions]
        return jsonify({
            'success': True,
            'data': {
                'pending_transactions': pending,
                'count': len(pending)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """블록체인 통계"""
    try:
        total_utxos = len(blockchain.utxo_pool.utxos)
        total_supply = sum(utxo.amount for utxo in blockchain.utxo_pool.utxos.values())
        
        return jsonify({
            'success': True,
            'data': {
                'total_blocks': len(blockchain.chain),
                'pending_transactions': len(blockchain.pending_transactions),
                'total_utxos': total_utxos,
                'total_supply': total_supply,
                'registered_wallets': len(wallets)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({
        'success': True,
        'message': 'Bitcoin server is running',
        'blockchain_height': len(blockchain.chain)
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'API endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # 서버 시작 시 데이터 로드
    load_data()
    
    # Genesis 블록에 초기 UTXO 추가 (테스트용)
    if len(blockchain.utxo_pool.utxos) == 0 and len(blockchain.chain) == 0:
        # 테스트용 초기 지갑 생성
        genesis_wallet = Wallet()
        wallets[genesis_wallet.get_address()] = genesis_wallet
        # Genesis 블록 생성
        genesis_block = blockchain._create_block(
            data="genesis block",
            proof=1,
            previous_hash="0",
            index=1
        )
        blockchain.chain.append(genesis_block)

        save_data()
        
        print(f"Genesis wallet created: {genesis_wallet.get_address()}")
    
    print("🚀 Bitcoin server starting...")
    print("📊 API endpoints:")
    print("   GET  / (로그인 페이지)")
    print("   GET  /join (회원가입 페이지)")
    print("   GET  /dashboard (대시보드)")
    print("   POST /api/wallet/create")
    print("   GET  /api/wallet/<address>/balance")
    print("   GET  /api/wallet/<address>/utxos")
    print("   POST /api/transaction/create")
    print("   POST /api/transaction/send")
    print("   POST /api/mine")
    print("   GET  /api/blockchain")
    print("   GET  /api/pending-transactions")
    print("   GET  /api/stats")
    
    app.run(debug=True, host='0.0.0.0', port=5000)