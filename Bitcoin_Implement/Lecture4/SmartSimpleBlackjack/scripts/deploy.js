const { ethers } = require("hardhat");

async function main() {
  console.log("🎰 블랙잭 게임 컨트랙트 배포를 시작합니다...\n");

  // 배포자 계정 정보
  const [deployer] = await ethers.getSigners();
  console.log("배포 계정:", deployer.address);
  
  const balance = await deployer.getBalance();
  console.log("계정 잔고:", ethers.utils.formatEther(balance), "ETH\n");

  // 컨트랙트 배포
  console.log("BlackjackGame 컨트랙트 배포 중...");
  const BlackjackGame = await ethers.getContractFactory("BlackjackGame");
  const blackjack = await BlackjackGame.deploy();
  
  await blackjack.deployed();
  console.log("✅ BlackjackGame 배포 완료!");
  console.log("컨트랙트 주소:", blackjack.address);
  
  // 네트워크 정보
  const network = await ethers.provider.getNetwork();
  console.log("네트워크:", network.name, `(chainId: ${network.chainId})`);
  
  // 컨트랙트 설정 확인
  const minBet = await blackjack.minBet();
  const maxBet = await blackjack.maxBet();
  console.log("\n📋 컨트랙트 설정:");
  console.log("최소 베팅:", ethers.utils.formatEther(minBet), "ETH");
  console.log("최대 베팅:", ethers.utils.formatEther(maxBet), "ETH");
  
  // 컨트랙트에 초기 자금 입금
  console.log("\n💰 컨트랙트에 초기 자금 입금 중...");
  const depositAmount = ethers.utils.parseEther("10");
  const depositTx = await blackjack.deposit({ value: depositAmount });
  await depositTx.wait();
  
  const contractBalance = await blackjack.getContractBalance();
  console.log("✅ 입금 완료!");
  console.log("컨트랙트 잔고:", ethers.utils.formatEther(contractBalance), "ETH");
  
  // 검증을 위한 정보 출력
  console.log("\n🔍 컨트랙트 검증 정보:");
  console.log("컨트랙트 주소:", blackjack.address);
  console.log("배포자 주소:", deployer.address);
  console.log("트랜잭션 해시:", blackjack.deployTransaction.hash);
  
  // 프론트엔드를 위한 정보 저장
  const deploymentInfo = {
    contractAddress: blackjack.address,
    deployer: deployer.address,
    network: network.name,
    chainId: network.chainId,
    deploymentTime: new Date().toISOString(),
    minBet: ethers.utils.formatEther(minBet),
    maxBet: ethers.utils.formatEther(maxBet),
    initialBalance: ethers.utils.formatEther(contractBalance)
  };
  
  console.log("\n📄 배포 정보 (프론트엔드용):");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  
  console.log("\n🎮 게임을 시작하려면 다음 명령어를 실행하세요:");
  console.log(`npx hardhat run scripts/play-game.js --network ${network.name === "unknown" ? "localhost" : network.name}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ 배포 실패:", error);
    process.exit(1);
  });