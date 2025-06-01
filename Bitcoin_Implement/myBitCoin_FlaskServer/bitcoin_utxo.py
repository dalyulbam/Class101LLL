import os
import ecdsa
import hashlib
import base58
import json
import datetime as _dt
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class UTXO:
    """미사용 트랜잭션 출력 (Unspent Transaction Output)"""
    tx_id: str          # 트랜잭션 ID
    output_index: int   # 출력 인덱스
    amount: float       # 금액
    address: str        # 소유자 주소
    
    def to_dict(self):
        return {
            "tx_id": self.tx_id,
            "output_index": self.output_index,
            "amount": self.amount,
            "address": self.address
        }

@dataclass
class TransactionInput:
    """트랜잭션 입력"""
    prev_tx_id: str     # 이전 트랜잭션 ID
    output_index: int   # 출력 인덱스
    signature: str      # 서명
    public_key: str     # 공개키
    
    def to_dict(self):
        return {
            "prev_tx_id": self.prev_tx_id,
            "output_index": self.output_index,
            "signature": self.signature,
            "public_key": self.public_key
        }

@dataclass
class TransactionOutput:
    """트랜잭션 출력"""
    amount: float       # 금액
    address: str        # 수신자 주소
    
    def to_dict(self):
        return {
            "amount": self.amount,
            "address": self.address
        }

class Wallet:
    def __init__(self):
        """새로운 비트코인 월렛 생성"""
        self.private_key = self._generate_private_key()
        self.public_key = self._generate_public_key(self.private_key)
        self.address = self._generate_address(self.public_key)

    def _generate_private_key(self) -> bytes:
        """32바이트 랜덤 개인 키 생성"""
        return os.urandom(32)

    def _generate_public_key(self, private_key: bytes) -> bytes:
        """타원 곡선 연산을 이용해 공개 키 생성"""
        sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
        vk = sk.verifying_key
        return b'\x04' + vk.to_string()

    def _generate_address(self, public_key: bytes) -> str:
        """비트코인 주소 생성"""
        sha256_pub = hashlib.sha256(public_key).digest()
        ripemd160_pub = hashlib.new('ripemd160', sha256_pub).digest()
        network_byte = b'\x00' + ripemd160_pub
        checksum = hashlib.sha256(hashlib.sha256(network_byte).digest()).digest()[:4]
        address = base58.b58encode(network_byte + checksum).decode()
        return address

    def get_private_key_hex(self) -> str:
        return self.private_key.hex()

    def get_public_key_hex(self) -> str:
        return self.public_key.hex()

    def get_address(self) -> str:
        return self.address

class Transaction:
    def __init__(self, inputs: List[TransactionInput], outputs: List[TransactionOutput]):
        """UTXO 기반 트랜잭션 생성"""
        self.inputs = inputs
        self.outputs = outputs
        self.tx_id = self._calculate_tx_id()
        
    def _calculate_tx_id(self) -> str:
        """트랜잭션 ID 계산"""
        tx_data = {
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        message = json.dumps(tx_data, sort_keys=True).encode()
        return hashlib.sha256(message).hexdigest()

    def to_dict(self):
        return {
            "tx_id": self.tx_id,
            "inputs": [inp.to_dict() for inp in self.inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }

    def sign_input(self, input_index: int, private_key_hex: str):
        """특정 입력에 대해 서명"""
        if input_index >= len(self.inputs):
            raise ValueError("Invalid input index")
            
        # 서명할 데이터 준비 (해당 입력의 서명 필드를 제외한 트랜잭션 데이터)
        temp_inputs = []
        for i, inp in enumerate(self.inputs):
            if i == input_index:
                temp_input = TransactionInput(
                    prev_tx_id=inp.prev_tx_id,
                    output_index=inp.output_index,
                    signature="",  # 서명 필드는 빈 문자열
                    public_key=inp.public_key
                )
            else:
                temp_input = inp
            temp_inputs.append(temp_input)
        
        temp_tx_data = {
            "inputs": [inp.to_dict() for inp in temp_inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        
        message = json.dumps(temp_tx_data, sort_keys=True).encode()
        
        # 서명 생성
        private_key_bytes = bytes.fromhex(private_key_hex)
        sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        signature = sk.sign(message).hex()
        
        # 서명을 해당 입력에 저장
        self.inputs[input_index].signature = signature

    def verify_input(self, input_index: int, utxo: UTXO) -> bool:
        """특정 입력의 서명 검증"""
        if input_index >= len(self.inputs):
            return False
            
        inp = self.inputs[input_index]
        
        # 서명할 데이터 재구성
        temp_inputs = []
        for i, current_inp in enumerate(self.inputs):
            if i == input_index:
                temp_input = TransactionInput(
                    prev_tx_id=current_inp.prev_tx_id,
                    output_index=current_inp.output_index,
                    signature="",
                    public_key=current_inp.public_key
                )
            else:
                temp_input = current_inp
            temp_inputs.append(temp_input)
        
        temp_tx_data = {
            "inputs": [inp_temp.to_dict() for inp_temp in temp_inputs],
            "outputs": [out.to_dict() for out in self.outputs]
        }
        
        message = json.dumps(temp_tx_data, sort_keys=True).encode()
        
        try:
            # 공개키에서 주소 계산하여 UTXO 소유자와 일치하는지 확인
            public_key_bytes = bytes.fromhex(inp.public_key)
            calculated_address = self._public_key_to_address(public_key_bytes)
            
            if calculated_address != utxo.address:
                return False
            
            # 서명 검증
            if len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
                public_key_bytes = public_key_bytes[1:]
            
            vk = ecdsa.VerifyingKey.from_string(public_key_bytes, curve=ecdsa.SECP256k1)
            return vk.verify(bytes.fromhex(inp.signature), message)
        except:
            return False

    def _public_key_to_address(self, public_key: bytes) -> str:
        """공개키에서 주소 계산"""
        sha256_pub = hashlib.sha256(public_key).digest()
        ripemd160_pub = hashlib.new('ripemd160', sha256_pub).digest()
        network_byte = b'\x00' + ripemd160_pub
        checksum = hashlib.sha256(hashlib.sha256(network_byte).digest()).digest()[:4]
        return base58.b58encode(network_byte + checksum).decode()

class UTXOPool:
    """UTXO 풀 관리"""
    def __init__(self):
        self.utxos: Dict[str, UTXO] = {}  # key: "tx_id:output_index"
    
    def add_utxo(self, utxo: UTXO):
        """UTXO 추가"""
        key = f"{utxo.tx_id}:{utxo.output_index}"
        self.utxos[key] = utxo
    
    def remove_utxo(self, tx_id: str, output_index: int):
        """UTXO 제거 (사용됨)"""
        key = f"{tx_id}:{output_index}"
        if key in self.utxos:
            del self.utxos[key]
    
    def get_utxo(self, tx_id: str, output_index: int) -> Optional[UTXO]:
        """UTXO 조회"""
        key = f"{tx_id}:{output_index}"
        return self.utxos.get(key)
    
    def get_utxos_by_address(self, address: str) -> List[UTXO]:
        """특정 주소의 모든 UTXO 조회"""
        return [utxo for utxo in self.utxos.values() if utxo.address == address]
    
    def get_balance(self, address: str) -> float:
        """주소의 잔액 계산"""
        utxos = self.get_utxos_by_address(address)
        return sum(utxo.amount for utxo in utxos)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.utxo_pool = UTXOPool()
        
        # Genesis 블록 생성
        genesis_block = self._create_block(
            data="genesis block",
            proof=1,
            previous_hash="0",
            index=1
        )
        self.chain.append(genesis_block)

    def _create_block(self, data: str, proof: int, previous_hash: str, index: int) -> dict:
        block = {
            "index": index,
            "timestamp": str(_dt.datetime.now()),
            "data": data,
            "proof": proof,
            "previous_hash": previous_hash
        }
        return block

    def get_previous_block(self) -> dict:
        return self.chain[-1]

    def _hash(self, block: dict) -> str:
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def add_transaction(self, transaction: Transaction) -> bool:
        """트랜잭션 유효성 검증 후 추가"""
        if not self._validate_transaction(transaction):
            return False
        
        self.pending_transactions.append(transaction)
        return True

    def _validate_transaction(self, transaction: Transaction) -> bool:
        """트랜잭션 유효성 검증"""
        total_input = 0
        total_output = sum(output.amount for output in transaction.outputs)
        
        # 각 입력 검증
        for i, inp in enumerate(transaction.inputs):
            # UTXO 존재 확인
            utxo = self.utxo_pool.get_utxo(inp.prev_tx_id, inp.output_index)
            if not utxo:
                print(f"UTXO not found: {inp.prev_tx_id}:{inp.output_index}")
                return False
            
            # 서명 검증
            if not transaction.verify_input(i, utxo):
                print(f"Invalid signature for input {i}")
                return False
            
            total_input += utxo.amount
        
        # 입력 >= 출력 확인 (수수료 고려)
        if total_input < total_output:
            print(f"Insufficient funds: input={total_input}, output={total_output}")
            return False
        
        return True

    def mine_block(self, miner_address: str) -> dict:
        """블록 채굴"""
        previous_block = self.get_previous_block()
        previous_proof = previous_block["proof"]
        index = len(self.chain) + 1
        
        # 채굴 보상 트랜잭션 생성
        reward_tx = Transaction(
            inputs=[],  # 코인베이스는 입력이 없음
            outputs=[TransactionOutput(amount=10.0, address=miner_address)]
        )
        reward_tx.tx_id = f"coinbase_{index}"
        
        # 대기 중인 트랜잭션들과 보상 트랜잭션 포함
        all_transactions = self.pending_transactions + [reward_tx]
        
        data = json.dumps({
            "transactions": [tx.to_dict() for tx in all_transactions]
        })
        
        proof = self._proof_of_work(previous_proof, index, data)
        previous_hash = self._hash(previous_block)
        
        block = self._create_block(data, proof, previous_hash, index)
        
        # 블록을 체인에 추가
        self.chain.append(block)
        
        # UTXO 풀 업데이트
        self._update_utxo_pool(all_transactions)
        
        # 대기 중인 트랜잭션 초기화
        self.pending_transactions = []
        
        return block

    def _update_utxo_pool(self, transactions: List[Transaction]):
        """트랜잭션 처리 후 UTXO 풀 업데이트"""
        for tx in transactions:
            # 사용된 UTXO 제거
            for inp in tx.inputs:
                self.utxo_pool.remove_utxo(inp.prev_tx_id, inp.output_index)
            
            # 새로운 UTXO 추가
            for i, output in enumerate(tx.outputs):
                utxo = UTXO(
                    tx_id=tx.tx_id,
                    output_index=i,
                    amount=output.amount,
                    address=output.address
                )
                self.utxo_pool.add_utxo(utxo)

    def _proof_of_work(self, previous_proof: int, index: int, data: str) -> int:
        """작업 증명"""
        new_proof = 1
        while True:
            to_digest = f"{new_proof**2 - previous_proof**2 + index}{data}"
            hash_operation = hashlib.sha256(to_digest.encode()).hexdigest()
            if hash_operation[:4] == "0000":
                return new_proof
            new_proof += 1

    def get_balance(self, address: str) -> float:
        """주소의 잔액 조회"""
        return self.utxo_pool.get_balance(address)

    def create_transaction(self, sender_address: str, receiver_address: str, 
                          amount: float, sender_wallet: Wallet) -> Optional[Transaction]:
        """트랜잭션 생성 도우미 함수"""
        # 송신자의 UTXO 조회
        utxos = self.utxo_pool.get_utxos_by_address(sender_address)
        
        # 필요한 금액만큼 UTXO 선택
        selected_utxos = []
        total_selected = 0
        for utxo in utxos:
            selected_utxos.append(utxo)
            total_selected += utxo.amount
            if total_selected >= amount:
                break
        
        if total_selected < amount:
            print(f"Insufficient balance: need {amount}, have {total_selected}")
            return None
        
        # 입력 생성
        inputs = []
        for utxo in selected_utxos:
            tx_input = TransactionInput(
                prev_tx_id=utxo.tx_id,
                output_index=utxo.output_index,
                signature="",  # 나중에 서명
                public_key=sender_wallet.get_public_key_hex()
            )
            inputs.append(tx_input)
        
        # 출력 생성
        outputs = [TransactionOutput(amount=amount, address=receiver_address)]
        
        # 거스름돈 처리
        change = total_selected - amount
        if change > 0:
            outputs.append(TransactionOutput(amount=change, address=sender_address))
        
        # 트랜잭션 생성
        transaction = Transaction(inputs, outputs)
        
        # 각 입력에 서명
        for i in range(len(inputs)):
            transaction.sign_input(i, sender_wallet.get_private_key_hex())
        
        return transaction