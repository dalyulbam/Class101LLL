// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract BlackjackGame {
    // 게임 상태 열거형
    enum GameState { 
        WaitingForPlayer, 
        PlayerTurn, 
        DealerTurn, 
        GameOver 
    }
    
    // 게임 결과 열거형
    enum GameResult { 
        None, 
        PlayerWins, 
        DealerWins, 
        Push, 
        PlayerBlackjack 
    }
    
    // 게임 구조체
    struct Game {
        address player;
        uint256 betAmount;
        uint8[] playerCards;
        uint8[] dealerCards;
        GameState state;
        GameResult result;
        uint256 timestamp;
        bool isActive;
    }
    
    // 상태 변수
    mapping(uint256 => Game) public games;
    mapping(address => uint256) public activeGames;
    uint256 public gameCounter;
    uint256 public houseEdge = 2; // 2% 하우스 엣지
    
    address public owner;
    uint256 public minBet = 0.001 ether;
    uint256 public maxBet = 1 ether;
    
    // 이벤트
    event GameStarted(uint256 indexed gameId, address indexed player, uint256 betAmount);
    event CardDealt(uint256 indexed gameId, address indexed player, uint8 card, bool isDealer);
    event GameEnded(uint256 indexed gameId, address indexed player, GameResult result, uint256 payout);
    event PlayerAction(uint256 indexed gameId, address indexed player, string action);
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier validGame(uint256 gameId) {
        require(games[gameId].isActive, "Game is not active");
        require(games[gameId].player == msg.sender, "Not your game");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    // 게임 시작
    function startGame() external payable {
        require(msg.value >= minBet && msg.value <= maxBet, "Invalid bet amount");
        require(activeGames[msg.sender] == 0, "You already have an active game");
        require(address(this).balance >= msg.value * 2, "Insufficient contract balance");
        
        gameCounter++;
        uint256 gameId = gameCounter;
        
        // 게임 초기화
        games[gameId] = Game({
            player: msg.sender,
            betAmount: msg.value,
            playerCards: new uint8[](0),
            dealerCards: new uint8[](0),
            state: GameState.PlayerTurn,
            result: GameResult.None,
            timestamp: block.timestamp,
            isActive: true
        });
        
        activeGames[msg.sender] = gameId;
        
        // 초기 카드 2장씩 배분
        _dealCard(gameId, false); // 플레이어 카드 1
        _dealCard(gameId, true);  // 딜러 카드 1 (숨김)
        _dealCard(gameId, false); // 플레이어 카드 2
        _dealCard(gameId, true);  // 딜러 카드 2
        
        // 블랙잭 체크
        if (_getHandValue(games[gameId].playerCards) == 21) {
            _checkBlackjack(gameId);
        }
        
        emit GameStarted(gameId, msg.sender, msg.value);
    }
    
    // 히트 (카드 한 장 더 받기)
    function hit(uint256 gameId) external validGame(gameId) {
        Game storage game = games[gameId];
        require(game.state == GameState.PlayerTurn, "Not player's turn");
        
        _dealCard(gameId, false);
        emit PlayerAction(gameId, msg.sender, "hit");
        
        uint256 playerValue = _getHandValue(game.playerCards);
        
        if (playerValue > 21) {
            // 플레이어 버스트
            game.state = GameState.GameOver;
            game.result = GameResult.DealerWins;
            _endGame(gameId);
        }
    }
    
    // 스탠드 (카드 받기 중단)
    function stand(uint256 gameId) external validGame(gameId) {
        Game storage game = games[gameId];
        require(game.state == GameState.PlayerTurn, "Not player's turn");
        
        game.state = GameState.DealerTurn;
        emit PlayerAction(gameId, msg.sender, "stand");
        
        _dealerPlay(gameId);
    }
    
    // 카드 배분 (내부 함수)
    function _dealCard(uint256 gameId, bool isDealer) internal {
        uint8 card = _generateRandomCard(gameId, games[gameId].playerCards.length + games[gameId].dealerCards.length);
        
        if (isDealer) {
            games[gameId].dealerCards.push(card);
        } else {
            games[gameId].playerCards.push(card);
        }
        
        emit CardDealt(gameId, games[gameId].player, card, isDealer);
    }
    
    // 랜덤 카드 생성 (개선 필요: 실제로는 Chainlink VRF 사용 권장)
    function _generateRandomCard(uint256 gameId, uint256 nonce) internal view returns (uint8) {
        uint256 randomHash = uint256(keccak256(abi.encodePacked(
            block.timestamp,
            block.difficulty,
            gameId,
            nonce,
            msg.sender
        )));
        
        // 1-13 범위의 카드 (1=A, 11=J, 12=Q, 13=K)
        uint8 card = uint8((randomHash % 13) + 1);
        return card;
    }
    
    // 핸드 값 계산
    function _getHandValue(uint8[] memory cards) internal pure returns (uint256) {
        uint256 value = 0;
        uint256 aces = 0;
        
        for (uint256 i = 0; i < cards.length; i++) {
            if (cards[i] == 1) {
                aces++;
                value += 11;
            } else if (cards[i] > 10) {
                value += 10; // J, Q, K는 10으로 계산
            } else {
                value += cards[i];
            }
        }
        
        // A를 1로 계산해야 하는 경우 조정
        while (value > 21 && aces > 0) {
            value -= 10;
            aces--;
        }
        
        return value;
    }
    
    // 블랙잭 체크
    function _checkBlackjack(uint256 gameId) internal {
        Game storage game = games[gameId];
        uint256 playerValue = _getHandValue(game.playerCards);
        uint256 dealerValue = _getHandValue(game.dealerCards);
        
        if (playerValue == 21 && dealerValue == 21) {
            game.result = GameResult.Push;
        } else if (playerValue == 21) {
            game.result = GameResult.PlayerBlackjack;
        } else if (dealerValue == 21) {
            game.result = GameResult.DealerWins;
        }
        
        if (game.result != GameResult.None) {
            game.state = GameState.GameOver;
            _endGame(gameId);
        }
    }
    
    // 딜러 플레이
    function _dealerPlay(uint256 gameId) internal {
        Game storage game = games[gameId];
        
        // 딜러는 17 이상까지 카드를 받아야 함
        while (_getHandValue(game.dealerCards) < 17) {
            _dealCard(gameId, true);
        }
        
        uint256 playerValue = _getHandValue(game.playerCards);
        uint256 dealerValue = _getHandValue(game.dealerCards);
        
        // 게임 결과 결정
        if (dealerValue > 21) {
            game.result = GameResult.PlayerWins;
        } else if (playerValue > dealerValue) {
            game.result = GameResult.PlayerWins;
        } else if (dealerValue > playerValue) {
            game.result = GameResult.DealerWins;
        } else {
            game.result = GameResult.Push;
        }
        
        game.state = GameState.GameOver;
        _endGame(gameId);
    }
    
    // 게임 종료 및 지불
    function _endGame(uint256 gameId) internal {
        Game storage game = games[gameId];
        uint256 payout = 0;
        
        if (game.result == GameResult.PlayerWins) {
            payout = game.betAmount * 2; // 1:1 지불
        } else if (game.result == GameResult.PlayerBlackjack) {
            payout = game.betAmount * 25 / 10; // 3:2 지불
        } else if (game.result == GameResult.Push) {
            payout = game.betAmount; // 베팅 금액 반환
        }
        // DealerWins의 경우 payout = 0
        
        game.isActive = false;
        activeGames[game.player] = 0;
        
        if (payout > 0) {
            payable(game.player).transfer(payout);
        }
        
        emit GameEnded(gameId, game.player, game.result, payout);
    }
    
    // 게임 상태 조회
    function getGameState(uint256 gameId) external view returns (
        address player,
        uint256 betAmount,
        uint8[] memory playerCards,
        uint8[] memory dealerCards,
        GameState state,
        GameResult result,
        uint256 playerValue,
        uint256 dealerValue
    ) {
        Game memory game = games[gameId];
        
        // 게임이 진행 중일 때는 딜러의 첫 번째 카드만 보여줌
        uint8[] memory visibleDealerCards = new uint8[](game.dealerCards.length);
        if (game.state == GameState.PlayerTurn && game.dealerCards.length > 0) {
            visibleDealerCards = new uint8[](1);
            visibleDealerCards[0] = game.dealerCards[0];
        } else {
            visibleDealerCards = game.dealerCards;
        }
        
        return (
            game.player,
            game.betAmount,
            game.playerCards,
            visibleDealerCards,
            game.state,
            game.result,
            _getHandValue(game.playerCards),
            _getHandValue(visibleDealerCards)
        );
    }
    
    // 컨트랙트 잔고 충전 (소유자만)
    function deposit() external payable onlyOwner {}
    
    // 컨트랙트 잔고 인출 (소유자만)
    function withdraw(uint256 amount) external onlyOwner {
        require(address(this).balance >= amount, "Insufficient balance");
        payable(owner).transfer(amount);
    }
    
    // 베팅 한도 설정 (소유자만)
    function setBettingLimits(uint256 _minBet, uint256 _maxBet) external onlyOwner {
        minBet = _minBet;
        maxBet = _maxBet;
    }
    
    // 컨트랙트 잔고 확인
    function getContractBalance() external view returns (uint256) {
        return address(this).balance;
    }
}