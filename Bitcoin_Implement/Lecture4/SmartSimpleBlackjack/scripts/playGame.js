const { ethers } = require("hardhat");

// 컨트랙트 주소 (deploy.js 실행 후 여기에 입력)
const CONTRACT_ADDRESS = "YOUR_CONTRACT_ADDRESS_HERE";

async function main() {
  console.log("🎰 블랙잭 게임을 시작합니다!\n");

  // 계정들 가져오기
  const [owner, player1, player2] = await ethers.getSigners();
  console.log("Owner:", owner.address);
  console.log("Player 1:", player1.address);
  console.log("Player 2:", player2.address, "\n");

  // 컨트랙트 연결
  const BlackjackGame = await ethers.getContractFactory("BlackjackGame");
  const blackjack = BlackjackGame.attach(CONTRACT_ADDRESS);

  // 컨트랙트 잔고 확인
  const contractBalance = await blackjack.getContractBalance();
  console.log("컨트랙트 잔고:", ethers.utils.formatEther(contractBalance), "ETH\n");

  // Player 1으로 게임 시작
  console.log("🎯 Player 1이 게임을 시작합니다...");
  const betAmount = ethers.utils.parseEther("0.1");
  
  try {
    const startTx = await blackjack.connect(player1).startGame({ 
      value: betAmount,
      gasLimit: 500000 
    });
    const receipt = await startTx.wait();
    console.log("✅ 게임 시작 성공!");
    
    // 이벤트 로그 파싱
    const gameStartedEvent = receipt.events?.find(e => e.event === 'GameStarted');
    if (gameStartedEvent) {
      const gameId = gameStartedEvent.args.gameId;
      console.log("게임 ID:", gameId.toString());
      
      // 게임 상태 조회
      await displayGameState(blackjack, gameId);
      
      // 자동으로 게임 플레이
      await autoPlay(blackjack, player1, gameId);
    }
    
  } catch (error) {
    console.error("❌ 게임 시작 실패:", error.message);
  }
}

async function displayGameState(blackjack, gameId) {
  try {
    const gameState = await blackjack.getGameState(gameId);
    
    console.log("\n📋 현재 게임 상태:");
    console.log("플레이어:", gameState.player);
    console.log("베팅 금액:", ethers.utils.formatEther(gameState.betAmount), "ETH");
    console.log("플레이어 카드:", gameState.playerCards.map(c => formatCard(c.toString())).join(", "));
    console.log("플레이어 핸드 값:", gameState.playerValue.toString());
    console.log("딜러 카드:", gameState.dealerCards.map(c => formatCard(c.toString())).join(", "));
    console.log("딜러 핸드 값:", gameState.dealerValue.toString());
    console.log("게임 상태:", getGameStateText(gameState.state));
    console.log("게임 결과:", getResultText(gameState.result));
    
  } catch (error) {
    console.error("게임 상태 조회 실패:", error.message);
  }
}

async function autoPlay(blackjack, player, gameId) {
  try {
    // 현재 게임 상태 확인
    let gameState = await blackjack.getGameState(gameId);
    
    // 플레이어 턴일 때만 진행
    if (gameState.state === 1) { // PlayerTurn
      const playerValue = parseInt(gameState.playerValue.toString());
      
      console.log(`\n🤔 플레이어 핸드 값: ${playerValue}`);
      
      if (playerValue < 17) {
        console.log("💡 17 미만이므로 Hit을 선택합니다...");
        const hitTx = await blackjack.connect(player).hit(gameId, { gasLimit: 300000 });
        await hitTx.wait();
        console.log("✅ Hit 완료!");
        
        // 업데이트된 상태 표시
        await displayGameState(blackjack, gameId);
        
        // 게임이 계속되면 다시 플레이
        gameState = await blackjack.getGameState(gameId);
        if (gameState.state === 1) {
          await autoPlay(blackjack, player, gameId);
        }
      } else {
        console.log("💡 17 이상이므로 Stand를 선택합니다...");
        const standTx = await blackjack.connect(player).stand(gameId, { gasLimit: 300000 });
        await standTx.wait();
        console.log("✅ Stand 완료!");
        
        // 최종 게임 결과 표시
        console.log("\n🏁 게임 종료!");
        await displayGameState(blackjack, gameId);
      }
    }
    
  } catch (error) {
    console.error("❌ 게임 플레이 실패:", error.message);
  }
}

// 헬퍼 함수들
function formatCard(cardValue) {
  const suits = ['♠', '♥', '♦', '♣'];
  const suit = suits[Math.floor(Math.random() * 4)];
  
  switch(cardValue) {
    case '1': return `A${suit}`;
    case '11': return `J${suit}`;
    case '12': return `Q${suit}`;
    case '13': return `K${suit}`;
    default: return `${cardValue}${suit}`;
  }
}

function getGameStateText(state) {
  const states = ['대기중', '플레이어 턴', '딜러 턴', '게임 종료'];
  return states[parseInt(state.toString())] || '알 수 없음';
}

function getResultText(result) {
  const results = ['없음', '플레이어 승리', '딜러 승리', '무승부', '블랙잭!'];
  return results[parseInt(result.toString())] || '알 수 없음';
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ 실행 실패:", error);
    process.exit(1);
  });