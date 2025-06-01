import requests
import json
import time

class BitcoinClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        
    def api_call(self, endpoint, method="GET", data=None):
        """API 호출 헬퍼 함수"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_wallet(self):
        """새 지갑 생성"""
        print("🆕 새 지갑 생성 중...")
        result = self.api_call("/wallet/create", "POST")
        
        if result["success"]:
            data = result["data"]
            print(f"✅ 지갑 생성 성공!")
            print(f"   주소: {data['address']}")
            print(f"   공개키: {data['public_key']}")
            return data["address"]
        else:
            print(f"❌ 지갑 생성 실패: {result.get('error', 'Unknown error')}")
            return None
    
    def get_balance(self, address):
        """잔액 조회"""
        print(f"💰 잔액 조회 중... ({address[:10]}...)")
        result = self.api_call(f"/wallet/{address}/balance")
        
        if result["success"]:
            balance = result["data"]["balance"]
            utxo_count = result["data"]["utxo_count"]
            print(f"✅ 잔액: {balance} BTC (UTXO 개수: {utxo_count})")
            return balance
        else:
            print(f"❌ 잔액 조회 실패: {result.get('error', 'Unknown error')}")
            return 0
    
    def get_utxos(self, address):
        """UTXO 조회"""
        print(f"🔍 UTXO 조회 중... ({address[:10]}...)")
        result = self.api_call(f"/wallet/{address}/utxos")
        
        if result["success"]:
            utxos = result["data"]["utxos"]
            total = result["data"]["total_amount"]
            print(f"✅ UTXO 개수: {len(utxos)}, 총 금액: {total} BTC")
            for i, utxo in enumerate(utxos):
                print(f"   UTXO {i+1}: {utxo['amount']} BTC (TX: {utxo['tx_id'][:10]}...)")
            return utxos
        else:
            print(f"❌ UTXO 조회 실패: {result.get('error', 'Unknown error')}")
            return []
    
    def send_transaction(self, sender_address, receiver_address, amount):
        """트랜잭션 전송"""
        print(f"🚀 트랜잭션 전송 중... ({amount} BTC)")
        print(f"   송신자: {sender_address[:10]}...")
        print(f"   수신자: {receiver_address[:10]}...")
        
        result = self.api_call("/transaction/send", "POST", {
            "sender_address": sender_address,
            "receiver_address": receiver_address,
            "amount": amount
        })
        
        if result["success"]:
            tx_id = result["data"]["transaction_id"]
            print(f"✅ 트랜잭션 전송 성공! TX ID: {tx_id[:10]}...")
            return tx_id
        else:
            print(f"❌ 트랜잭션 전송 실패: {result.get('error', 'Unknown error')}")
            return None
    
    def mine_block(self, miner_address):
        """블록 채굴"""
        print(f"⛏️  블록 채굴 시작... (채굴자: {miner_address[:10]}...)")
        start_time = time.time()
        
        result = self.api_call("/mine", "POST", {
            "miner_address": miner_address
        })
        
        end_time = time.time()
        mining_time = end_time - start_time
        
        if result["success"]:
            block = result["data"]["block"]
            print(f"✅ 블록 채굴 성공! (소요시간: {mining_time:.2f}초)")
            print(f"   블록 번호: {block['index']}")
            print(f"   Proof: {block['proof']}")
            print(f"   트랜잭션 처리: {result['data']['transactions_processed']}개")
            return block
        else:
            print(f"❌ 블록 채굴 실패: {result.get('error', 'Unknown error')}")
            return None
    
    def get_blockchain_info(self):
        """블록체인 정보 조회"""
        print("📊 블록체인 정보 조회 중...")
        result = self.api_call("/blockchain")
        
        if result["success"]:
            chain_length = result["data"]["length"]
            pending_txs = result["data"]["pending_transactions"]
            print(f"✅ 블록체인 길이: {chain_length}")
            print(f"   대기 중인 트랜잭션: {pending_txs}개")
            return result["data"]
        else:
            print(f"❌ 블록체인 정보 조회 실패: {result.get('error', 'Unknown error')}")
            return None
    
    def get_stats(self):
        """통계 조회"""
        print("📈 시스템 통계 조회 중...")
        result = self.api_call("/stats")
        
        if result["success"]:
            stats = result["data"]
            print(f"✅ 시스템 통계:")
            print(f"   총 블록 수: {stats['total_blocks']}")
            print(f"   총 공급량: {stats['total_supply']} BTC")
            print(f"   총 UTXO 수: {stats['total_utxos']}")
            print(f"   대기 트랜잭션: {stats['pending_transactions']}")
            print(f"   등록된 지갑: {stats['registered_wallets']}")
            return stats
        else:
            print(f"❌ 통계 조회 실패: {result.get('error', 'Unknown error')}")
            return None

def run_demo():
    """데모 실행"""
    print("🚀 Bitcoin UTXO 블록체인 테스트 시작!")
    print("=" * 50)
    
    client = BitcoinClient()
    
    # 1. 시스템 상태 확인
    print("\n📊 1. 시스템 상태 확인")
    client.get_stats()
    
    # 2. 지갑 생성
    print("\n👛 2. 지갑 생성")
    alice_address = client.create_wallet()
    bob_address = client.create_wallet()
    miner_address = client.create_wallet()
    
    if not all([alice_address, bob_address, miner_address]):
        print("❌ 지갑 생성 실패로 테스트 중단")
        return
    
    # 3. 초기 잔액 확인
    print("\n💰 3. 초기 잔액 확인")
    client.get_balance(alice_address)
    client.get_balance(bob_address)
    client.get_balance(miner_address)
    
    # 4. 첫 번째 블록 채굴 (Alice에게 보상 지급)
    print("\n⛏️  4. 첫 번째 블록 채굴 (Alice 보상)")
    client.mine_block(alice_address)
    
    # 5. Alice 잔액 확인
    print("\n💰 5. 채굴 후 Alice 잔액 확인")
    alice_balance = client.get_balance(alice_address)
    client.get_utxos(alice_address)
    
    # 6. Alice → Bob 트랜잭션
    print("\n🚀 6. Alice → Bob 트랜잭션 (3 BTC)")
    if alice_balance >= 3:
        client.send_transaction(alice_address, bob_address, 3.0)
    else:
        print("❌ Alice의 잔액이 부족합니다.")
    
    # 7. 두 번째 블록 채굴 (Miner에게 보상 지급)
    print("\n⛏️  7. 두 번째 블록 채굴 (Miner 보상)")
    client.mine_block(miner_address)
    
    # 8. 최종 잔액 확인
    print("\n💰 8. 최종 잔액 확인")
    print(f"Alice ({alice_address[:10]}...): {client.get_balance(alice_address)} BTC")
    print(f"Bob   ({bob_address[:10]}...): {client.get_balance(bob_address)} BTC")
    print(f"Miner ({miner_address[:10]}...): {client.get_balance(miner_address)} BTC")
    
    # 9. 블록체인 정보
    print("\n🔗 9. 최종 블록체인 정보")
    client.get_blockchain_info()
    
    # 10. 최종 통계
    print("\n📈 10. 최종 시스템 통계")
    client.get_stats()
    
    print("\n🎉 테스트 완료!")
    print("=" * 50)

def interactive_mode():
    """대화형 모드"""
    client = BitcoinClient()
    
    print("🚀 Bitcoin UTXO 블록체인 대화형 클라이언트")
    print("사용 가능한 명령어:")
    print("  1. create_wallet - 새 지갑 생성")
    print("  2. balance <address> - 잔액 조회")
    print("  3. utxos <address> - UTXO 조회")
    print("  4. send <sender> <receiver> <amount> - 트랜잭션 전송")
    print("  5. mine <miner_address> - 블록 채굴")
    print("  6. blockchain - 블록체인 정보")
    print("  7. stats - 시스템 통계")
    print("  8. demo - 자동 데모 실행")
    print("  9. exit - 종료")
    print()
    
    while True:
        try:
            command = input("💻 명령어 입력: ").strip().split()
            
            if not command:
                continue
                
            cmd = command[0].lower()
            
            if cmd == "create_wallet":
                client.create_wallet()
                
            elif cmd == "balance" and len(command) == 2:
                client.get_balance(command[1])
                
            elif cmd == "utxos" and len(command) == 2:
                client.get_utxos(command[1])
                
            elif cmd == "send" and len(command) == 4:
                client.send_transaction(command[1], command[2], float(command[3]))
                
            elif cmd == "mine" and len(command) == 2:
                client.mine_block(command[1])
                
            elif cmd == "blockchain":
                client.get_blockchain_info()
                
            elif cmd == "stats":
                client.get_stats()
                
            elif cmd == "demo":
                run_demo()
                
            elif cmd == "exit":
                print("👋 클라이언트를 종료합니다.")
                break
                
            else:
                print("❌ 잘못된 명령어입니다. 다시 입력해주세요.")
                
        except KeyboardInterrupt:
            print("\n👋 클라이언트를 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("Bitcoin UTXO 블록체인 테스트 클라이언트")
    print("=" * 50)
    
    mode = input("모드 선택 (1: 자동 데모, 2: 대화형 모드): ").strip()
    
    if mode == "1":
        run_demo()
    elif mode == "2":
        interactive_mode()
    else:
        print("❌ 잘못된 선택입니다. 자동 데모를 실행합니다.")
        run_demo()