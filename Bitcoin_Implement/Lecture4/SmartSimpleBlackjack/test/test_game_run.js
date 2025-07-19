const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("BlackjackGame", function () {
  let blackjack;
  let owner;
  let player1;
  let player2;

  beforeEach(async function () {
    [owner, player1, player2] = await ethers.getSigners();
    
    const BlackjackGame = await ethers.getContractFactory("BlackjackGame");
    blackjack = await BlackjackGame.deploy();
    await blackjack.deployed();
    
    // 컨트랙트에 초기 자금 입금
    await blackjack.deposit({ value: ethers.utils.parseEther("10") });
  });

  describe("배포", function () {
    it("올바른 owner가 설정되어야 함", async function () {
      expect(await blackjack.owner()).to.equal(owner.address);
    });

    it("올바른 베팅 한도가 설정되어야 함", async function () {
      expect(await blackjack.minBet()).to.equal(ethers.utils.parseEther("0.001"));
      expect(await blackjack.maxBet()).to.equal(ethers.utils.parseEther("1"));
    });
  });

  describe("게임 시작", function () {
    it("올바른 베팅으로 게임을 시작할 수 있어야 함", async function () {
      const betAmount = ethers.utils.parseEther("0.1");
      
      await expect(blackjack.connect(player1).startGame({ value: betAmount }))
        .to.emit(blackjack, "GameStarted")
        .withArgs(1, player1.address, betAmount);
    });

    it("최소 베팅 미만으로는 게임을 시작할 수 없어야 함", async function () {
      const betAmount = ethers.utils.parseEther("0.0001");
      
      await expect(
        blackjack.connect(player1).startGame({ value: betAmount })
      ).to.be.revertedWith("Invalid bet amount");
    });

    it("최대 베팅 초과로는 게임을 시작할 수 없어야 함", async function () {
      const betAmount = ethers.utils.parseEther("2");
      
      await expect(
        blackjack.connect(player1).startGame({ value: betAmount })
      ).to.be.revertedWith("Invalid bet amount");
    });

    it("이미 활성 게임이 있으면 새 게임을 시작할 수 없어야 함", async function () {
      const betAmount = ethers.utils.parseEther("0.1");
      
      await blackjack.connect(player1).startGame({ value: betAmount });
      
      await expect(
        blackjack.connect(player1).startGame({ value: betAmount })
      ).to.be.revertedWith("You already have an active game");
    });
  });

  describe("게임 플레이", function () {
    let gameId;
    
    beforeEach(async function () {
      const betAmount = ethers.utils.parseEther("0.1");
      await blackjack.connect(player1).startGame({ value: betAmount });
      gameId = await blackjack.activeGames(player1.address);
    });

    it("플레이어가 hit을 할 수 있어야 함", async function () {
      await expect(blackjack.connect(player1).hit(gameId))
        .to.emit(blackjack, "PlayerAction")
        .withArgs(gameId, player1.address, "hit");
    });

    it("플레이어가 stand를 할 수 있어야 함", async function () {
      await expect(blackjack.connect(player1).stand(gameId))
        .to.emit(blackjack, "PlayerAction")
        .withArgs(gameId, player1.address, "stand");
    });

    it("다른 플레이어는 게임에 참여할 수 없어야 함", async function () {
      await expect(
        blackjack.connect(player2).hit(gameId)
      ).to.be.revertedWith("Not your game");
    });
  });

  describe("게임 상태 조회", function () {
    let gameId;
    
    beforeEach(async function () {
      const betAmount = ethers.utils.parseEther("0.1");
      await blackjack.connect(player1).startGame({ value: betAmount });
      gameId = await blackjack.activeGames(player1.address);
    });

    it("게임 상태를 올바르게 반환해야 함", async function () {
      const gameState = await blackjack.getGameState(gameId);
      
      expect(gameState.player).to.equal(player1.address);
      expect(gameState.betAmount).to.equal(ethers.utils.parseEther("0.1"));
      expect(gameState.playerCards.length).to.equal(2);
      expect(gameState.dealerCards.length).to.equal(1); // 게임 중에는 하나만 보임
    });
  });

  describe("Owner 함수들", function () {
    it("Owner만 자금을 인출할 수 있어야 함", async function () {
      const withdrawAmount = ethers.utils.parseEther("1");
      
      await expect(
        blackjack.connect(player1).withdraw(withdrawAmount)
      ).to.be.revertedWith("Only owner can call this function");
    });

    it("Owner가 베팅 한도를 설정할 수 있어야 함", async function () {
      const newMinBet = ethers.utils.parseEther("0.01");
      const newMaxBet = ethers.utils.parseEther("5");
      
      await blackjack.setBettingLimits(newMinBet, newMaxBet);
      
      expect(await blackjack.minBet()).to.equal(newMinBet);
      expect(await blackjack.maxBet()).to.equal(newMaxBet);
    });
  });
});