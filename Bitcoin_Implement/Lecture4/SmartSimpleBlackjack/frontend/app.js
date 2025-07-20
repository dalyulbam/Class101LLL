// 블랙잭 DApp 메인 JavaScript

// 컨트랙트 ABI (실제 ABI로 교체 필요)
const CONTRACT_ABI = [
    "function startGame() external payable",
    "function hit(uint256 gameId) external",
    "function stand(uint256 gameId) external",
    "function getGameState(uint256 gameId) external view returns (address player, uint256 betAmount, uint8[] memory playerCards, uint8[] memory dealerCards, uint8 state, uint8 result, uint256 playerValue, uint256 dealerValue)",
    "function activeGames(address player) external view returns (uint256)",
    "function getContractBalance() external view returns (uint256)",
    "function minBet() external view returns (uint256)",
    "function maxBet() external view returns (uint256)",
    "function owner() external view returns (address)",
    "function deposit() external payable",
    "function withdraw(uint256 amount) external",
    "event GameStarted(uint256 indexed gameId, address indexed player, uint256 betAmount)",
    "event CardDealt(uint256 indexed gameId, address indexed player, uint8 card, bool isDealer)",
    "event GameEnded(uint256 indexed gameId, address indexed player, uint8 result, uint256 payout)",
    "event PlayerAction(uint256 indexed gameId, address indexed player, string action)"
];

class BlackjackDApp {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.contract = null;
        this.currentGameId = null;
        this.userAccount = null;
        this.isOwner = false;
        this.connectionMethod = null; // 'metamask' or 'privatekey'
        
        this.initializeEventListeners();
        this.checkWalletConnection();
    }

    // 이벤트 리스너 초기화
    initializeEventListeners() {
        document.getElementById('connectWallet').addEventListener('click', () => this.connectWallet());
        document.getElementById('connectPrivateKey').addEventListener('click', () => this.connectWithPrivateKey());
        document.getElementById('loadContract').addEventListener('click', () => this.loadContract());
        document.getElementById('startGame').addEventListener('click', () => this.startGame());
        document.getElementById('hitButton').addEventListener('click', () => this.hit());
        document.getElementById('standButton').addEventListener('click', () => this.stand());
        document.getElementById('newGameButton').addEventListener('click', () => this.newGame());
        document.getElementById('clearLog').addEventListener('click', () => this.clearLog());
        document.getElementById('depositButton').addEventListener('click', () => this.deposit());
        document.getElementById('withdrawButton').addEventListener('click', () => this.withdraw());
    }

    // 지갑 연결 상태 확인
    async checkWalletConnection() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' });
                if (accounts.length > 0) {
                    await this.connectWallet();
                }
            } catch (error) {
                this.log('지갑 연결 상태 확인 실패', 'error');
            }
        }
    }

    // MetaMask 연결
    async connectWallet() {
        if (typeof window.ethereum === 'undefined') {
            alert('MetaMask가 설치되지 않았습니다! Private Key로 연결하세요.');
            return false;
        }

        try {
            this.showTransactionStatus('지갑 연결 중...');
            
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            this.provider = new ethers.providers.Web3Provider(window.ethereum);
            this.signer = this.provider.getSigner();
            this.connectionMethod = 'metamask';
            
            this.userAccount = await this.signer.getAddress();
            const balance = await this.signer.getBalance();
            
            this.updateConnectionUI(this.userAccount, balance);
            this.log(`MetaMask 연결 성공: ${this.userAccount}`, 'success');
            this.hideTransactionStatus();
            
            // 계정 변경 감지
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnectWallet();
                } else {
                    location.reload();
                }
            });
            
            return true;
        } catch (error) {
            this.log(`MetaMask 연결 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
            return false;
        }
    }

    // Private Key로 연결
    async connectWithPrivateKey() {
        const privateKey = document.getElementById('privateKeyInput').value.trim();
        
        if (!privateKey) {
            alert('Private Key를 입력하세요');
            return false;
        }

        if (!privateKey.startsWith('0x') || privateKey.length !== 66) {
            alert('올바른 Private Key 형식이 아닙니다 (0x로 시작하는 64자리)');
            return false;
        }

        try {
            this.showTransactionStatus('Private Key로 연결 중...');
            
            // RPC URL 가져오기
            const rpcUrl = document.getElementById('rpcUrl').value.trim() || 'http://127.0.0.1:8545';
            
            this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
            this.signer = new ethers.Wallet(privateKey, this.provider);
            this.connectionMethod = 'privatekey';
            
            this.userAccount = this.signer.address;
            const balance = await this.signer.getBalance();
            
            this.updateConnectionUI(this.userAccount, balance);
            this.log(`Private Key 연결 성공: ${this.userAccount}`, 'success');
            this.hideTransactionStatus();
            
            return true;
        } catch (error) {
            this.log(`Private Key 연결 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
            return false;
        }
    }

    // 연결 UI 업데이트
    updateConnectionUI(address, balance) {
        document.getElementById('accountAddress').textContent = address;
        document.getElementById('accountBalance').textContent = ethers.utils.formatEther(balance);
        document.getElementById('walletInfo').style.display = 'block';
        document.getElementById('connectionStatus').textContent = '연결됨';
        document.getElementById('connectionStatus').className = 'status connected';
        
        // 연결 방법에 따른 버튼 상태 변경
        if (this.connectionMethod === 'metamask') {
            document.getElementById('connectWallet').textContent = 'MetaMask 연결됨';
            document.getElementById('connectWallet').disabled = true;
        } else {
            document.getElementById('connectPrivateKey').textContent = 'Private Key 연결됨';
            document.getElementById('connectPrivateKey').disabled = true;
        }
    }

    // 지갑 연결 해제
    disconnectWallet() {
        this.provider = null;
        this.signer = null;
        this.contract = null;
        this.userAccount = null;
        this.connectionMethod = null;
        
        document.getElementById('walletInfo').style.display = 'none';
        document.getElementById('connectionStatus').textContent = '연결되지 않음';
        document.getElementById('connectionStatus').className = 'status disconnected';
        document.getElementById('connectWallet').textContent = 'MetaMask 연결';
        document.getElementById('connectWallet').disabled = false;
        document.getElementById('connectPrivateKey').textContent = 'Private Key 연결';
        document.getElementById('connectPrivateKey').disabled = false;
        
        this.log('지갑 연결이 해제되었습니다', 'warning');
    }

    // 컨트랙트 로드
    async loadContract() {
        const contractAddress = document.getElementById('contractAddress').value.trim();
        
        if (!contractAddress) {
            alert('컨트랙트 주소를 입력하세요');
            return;
        }

        if (!this.signer) {
            alert('먼저 지갑을 연결하세요');
            return;
        }

        try {
            this.showTransactionStatus('컨트랙트 로딩 중...');
            
            this.contract = new ethers.Contract(contractAddress, CONTRACT_ABI, this.signer);
            
            // 컨트랙트 정보 가져오기
            const contractBalance = await this.contract.getContractBalance();
            const minBet = await this.contract.minBet();
            const maxBet = await this.contract.maxBet();
            const owner = await this.contract.owner();
            
            // Owner 여부 확인
            this.isOwner = (owner.toLowerCase() === this.userAccount.toLowerCase());
            
            // UI 업데이트
            document.getElementById('contractBalance').textContent = ethers.utils.formatEther(contractBalance);
            document.getElementById('minBet').textContent = ethers.utils.formatEther(minBet);
            document.getElementById('maxBet').textContent = ethers.utils.formatEther(maxBet);
            document.getElementById('contractInfo').style.display = 'block';
            document.getElementById('startGame').disabled = false;
            
            // Owner 전용 섹션 표시
            if (this.isOwner) {
                const ownerSection = document.querySelector('.owner-section');
                if (ownerSection) ownerSection.style.display = 'block';
            }
            
            // 베팅 금액 입력 필드 설정
            const betInput = document.getElementById('betAmount');
            betInput.min = ethers.utils.formatEther(minBet);
            betInput.max = ethers.utils.formatEther(maxBet);
            betInput.value = ethers.utils.formatEther(minBet);
            
            this.log(`컨트랙트 로드 성공: ${contractAddress}`, 'success');
            this.hideTransactionStatus();
            
            // 이벤트 리스너 설정
            this.setupEventListeners();
            
            // 기존 활성 게임 확인
            await this.checkActiveGame();
            
        } catch (error) {
            this.log(`컨트랙트 로드 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        this.contract.on("GameStarted", (gameId, player, betAmount, event) => {
            if (player.toLowerCase() === this.userAccount.toLowerCase()) {
                this.log(`게임 시작됨 - ID: ${gameId}, 베팅: ${ethers.utils.formatEther(betAmount)} ETH`, 'success');
                this.currentGameId = gameId;
                this.updateGameState();
            }
        });

        this.contract.on("CardDealt", (gameId, player, card, isDealer, event) => {
            if (player.toLowerCase() === this.userAccount.toLowerCase()) {
                const cardType = isDealer ? '딜러' : '플레이어';
                this.log(`카드 배분 - ${cardType}: ${this.formatCard(card)}`, 'info');
                this.updateGameState();
            }
        });

        this.contract.on("GameEnded", (gameId, player, result, payout, event) => {
            if (player.toLowerCase() === this.userAccount.toLowerCase()) {
                const resultText = this.getResultText(result);
                const payoutEth = ethers.utils.formatEther(payout);
                this.log(`게임 종료 - 결과: ${resultText}, 지불: ${payoutEth} ETH`, 'success');
                this.updateGameState();
            }
        });

        this.contract.on("PlayerAction", (gameId, player, action, event) => {
            if (player.toLowerCase() === this.userAccount.toLowerCase()) {
                this.log(`플레이어 액션: ${action}`, 'info');
            }
        });
    }

    // 활성 게임 확인
    async checkActiveGame() {
        try {
            const activeGameId = await this.contract.activeGames(this.userAccount);
            if (activeGameId.gt(0)) {
                this.currentGameId = activeGameId;
                this.log(`활성 게임 발견 - ID: ${activeGameId}`, 'info');
                await this.updateGameState();
            }
        } catch (error) {
            this.log(`활성 게임 확인 실패: ${error.message}`, 'error');
        }
    }

    // 게임 시작
    async startGame() {
        const betAmount = document.getElementById('betAmount').value;
        
        if (!betAmount || parseFloat(betAmount) <= 0) {
            alert('유효한 베팅 금액을 입력하세요');
            return;
        }

        try {
            this.showTransactionStatus('게임 시작 중...');
            
            const betWei = ethers.utils.parseEther(betAmount);
            const tx = await this.contract.startGame({ 
                value: betWei,
                gasLimit: 500000 
            });
            
            this.log(`트랜잭션 전송됨: ${tx.hash}`, 'info');
            const receipt = await tx.wait();
            
            this.log('게임이 시작되었습니다!', 'success');
            this.hideTransactionStatus();
            
        } catch (error) {
            this.log(`게임 시작 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 히트
    async hit() {
        if (!this.currentGameId) {
            alert('활성 게임이 없습니다');
            return;
        }

        try {
            this.showTransactionStatus('카드 받는 중...');
            
            const tx = await this.contract.hit(this.currentGameId, { gasLimit: 300000 });
            this.log(`트랜잭션 전송됨: ${tx.hash}`, 'info');
            await tx.wait();
            
            this.hideTransactionStatus();
            
        } catch (error) {
            this.log(`히트 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 스탠드
    async stand() {
        if (!this.currentGameId) {
            alert('활성 게임이 없습니다');
            return;
        }

        try {
            this.showTransactionStatus('스탠드 처리 중...');
            
            const tx = await this.contract.stand(this.currentGameId, { gasLimit: 300000 });
            this.log(`트랜잭션 전송됨: ${tx.hash}`, 'info');
            await tx.wait();
            
            this.hideTransactionStatus();
            
        } catch (error) {
            this.log(`스탠드 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 게임 상태 업데이트
    async updateGameState() {
        if (!this.currentGameId || !this.contract) return;

        try {
            const gameState = await this.contract.getGameState(this.currentGameId);
            
            // UI 표시
            document.getElementById('gameId').textContent = this.currentGameId.toString();
            document.getElementById('currentBet').textContent = ethers.utils.formatEther(gameState.betAmount);
            document.getElementById('gameStatus').textContent = this.getGameStateText(gameState.state);
            document.getElementById('playerValue').textContent = gameState.playerValue.toString();
            document.getElementById('dealerValue').textContent = gameState.dealerValue.toString();
            
            // 카드 표시
            this.displayCards('playerCards', gameState.playerCards);
            this.displayCards('dealerCards', gameState.dealerCards);
            
            // 게임 섹션 표시
            document.querySelector('.game-state-section').style.display = 'block';
            
            // 버튼 상태 업데이트
            const isPlayerTurn = gameState.state === 1;
            const isGameOver = gameState.state === 3;
            
            document.getElementById('hitButton').disabled = !isPlayerTurn;
            document.getElementById('standButton').disabled = !isPlayerTurn;
            document.getElementById('newGameButton').style.display = isGameOver ? 'inline-block' : 'none';
            document.getElementById('startGame').disabled = !isGameOver;
            
            // 게임 결과 표시
            if (isGameOver && gameState.result !== 0) {
                this.displayGameResult(gameState.result);
                this.currentGameId = null;
            }
            
        } catch (error) {
            this.log(`게임 상태 업데이트 실패: ${error.message}`, 'error');
        }
    }

    // 카드 표시
    displayCards(elementId, cards) {
        const container = document.getElementById(elementId);
        container.innerHTML = '';
        
        cards.forEach(card => {
            const cardElement = document.createElement('span');
            cardElement.className = 'card';
            cardElement.textContent = this.formatCard(card);
            
            // 하트, 다이아몬드는 빨간색
            if (this.isRedSuit(card)) {
                cardElement.classList.add('red');
            }
            
            container.appendChild(cardElement);
        });
    }

    // 카드 포맷팅
    formatCard(cardValue) {
        const suits = ['♠', '♥', '♦', '♣'];
        const suit = suits[Math.floor(Math.random() * 4)];
        
        switch(parseInt(cardValue)) {
            case 1: return `A${suit}`;
            case 11: return `J${suit}`;
            case 12: return `Q${suit}`;
            case 13: return `K${suit}`;
            default: return `${cardValue}${suit}`;
        }
    }

    // 빨간 무늬 확인
    isRedSuit(cardValue) {
        // 간단한 랜덤으로 하트/다이아몬드 결정
        return Math.random() < 0.5;
    }

    // 게임 상태 텍스트
    getGameStateText(state) {
        const states = ['대기중', '플레이어 턴', '딜러 턴', '게임 종료'];
        return states[parseInt(state)] || '알 수 없음';
    }

    // 결과 텍스트
    getResultText(result) {
        const results = ['없음', '플레이어 승리', '딜러 승리', '무승부', '블랙잭!'];
        return results[parseInt(result)] || '알 수 없음';
    }

    // 게임 결과 표시
    displayGameResult(result) {
        const resultElement = document.getElementById('gameResult');
        const resultText = this.getResultText(result);
        
        resultElement.textContent = `게임 결과: ${resultText}`;
        resultElement.style.display = 'block';
        
        // 결과에 따른 스타일 적용
        resultElement.className = 'result';
        switch(parseInt(result)) {
            case 1: // 플레이어 승리
            case 4: // 블랙잭
                resultElement.classList.add('win');
                break;
            case 2: // 딜러 승리
                resultElement.classList.add('lose');
                break;
            case 3: // 무승부
                resultElement.classList.add('push');
                break;
        }
    }

    // 새 게임
    newGame() {
        this.currentGameId = null;
        document.querySelector('.game-state-section').style.display = 'none';
        document.getElementById('gameResult').style.display = 'none';
        document.getElementById('startGame').disabled = false;
        this.log('새 게임을 시작할 수 있습니다', 'info');
    }

    // 입금 (Owner 전용)
    async deposit() {
        if (!this.isOwner) {
            alert('Owner만 사용할 수 있습니다');
            return;
        }

        const depositAmount = document.getElementById('depositAmount').value;
        
        if (!depositAmount || parseFloat(depositAmount) <= 0) {
            alert('유효한 입금 금액을 입력하세요');
            return;
        }

        try {
            this.showTransactionStatus('입금 처리 중...');
            
            const depositWei = ethers.utils.parseEther(depositAmount);
            const tx = await this.contract.deposit({ 
                value: depositWei,
                gasLimit: 100000 
            });
            
            this.log(`입금 트랜잭션 전송됨: ${tx.hash}`, 'info');
            await tx.wait();
            
            this.log(`${depositAmount} ETH 입금 완료`, 'success');
            this.hideTransactionStatus();
            
            // 컨트랙트 잔고 업데이트
            await this.updateContractBalance();
            
        } catch (error) {
            this.log(`입금 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 출금 (Owner 전용)
    async withdraw() {
        if (!this.isOwner) {
            alert('Owner만 사용할 수 있습니다');
            return;
        }

        const withdrawAmount = document.getElementById('withdrawAmount').value;
        
        if (!withdrawAmount || parseFloat(withdrawAmount) <= 0) {
            alert('유효한 출금 금액을 입력하세요');
            return;
        }

        try {
            this.showTransactionStatus('출금 처리 중...');
            
            const withdrawWei = ethers.utils.parseEther(withdrawAmount);
            const tx = await this.contract.withdraw(withdrawWei, { gasLimit: 100000 });
            
            this.log(`출금 트랜잭션 전송됨: ${tx.hash}`, 'info');
            await tx.wait();
            
            this.log(`${withdrawAmount} ETH 출금 완료`, 'success');
            this.hideTransactionStatus();
            
            // 컨트랙트 잔고 업데이트
            await this.updateContractBalance();
            
        } catch (error) {
            this.log(`출금 실패: ${error.message}`, 'error');
            this.hideTransactionStatus();
        }
    }

    // 컨트랙트 잔고 업데이트
    async updateContractBalance() {
        try {
            const contractBalance = await this.contract.getContractBalance();
            document.getElementById('contractBalance').textContent = ethers.utils.formatEther(contractBalance);
        } catch (error) {
            this.log(`컨트랙트 잔고 업데이트 실패: ${error.message}`, 'error');
        }
    }

    // 로그 출력
    log(message, type = 'info') {
        const logBox = document.getElementById('gameLog');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logBox.appendChild(logEntry);
        logBox.scrollTop = logBox.scrollHeight;
    }

    // 로그 지우기
    clearLog() {
        document.getElementById('gameLog').innerHTML = '';
    }

    // 트랜잭션 상태 표시
    showTransactionStatus(message) {
        const statusElement = document.getElementById('transactionStatus');
        document.getElementById('transactionMessage').textContent = message;
        statusElement.style.display = 'block';
    }

    // 트랜잭션 상태 숨기기
    hideTransactionStatus() {
        document.getElementById('transactionStatus').style.display = 'none';
    }
}

// DApp 초기화
let dapp;

document.addEventListener('DOMContentLoaded', function() {
    dapp = new BlackjackDApp();
    
    // 페이지 로드 시 기본 컨트랙트 주소 설정
    const defaultContractAddress = '0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0'; // 배포된 주소
    document.getElementById('contractAddress').value = defaultContractAddress;
});

// 전역 함수로 콘솔에서 디버깅 가능
window.dapp = dapp;