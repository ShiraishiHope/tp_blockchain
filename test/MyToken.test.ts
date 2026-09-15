import { expect } from 'chai';
import { ethers } from 'hardhat';
import { MyToken } from '../typechain-types';
import { SignerWithAddress } from '@nomicfoundation/hardhat-ethers/signers';

describe('MyToken', function () {
  let token: MyToken;
  let owner: SignerWithAddress;
  let alice: SignerWithAddress;
  let bob: SignerWithAddress;

  const NAME = 'MyToken';
  const SYMBOL = 'MTK';
  const SUPPLY = ethers.parseEther('1000000');

  beforeEach(async function () {
    [owner, alice, bob] = await ethers.getSigners();
    const Token = await ethers.getContractFactory('MyToken');
    token = await Token.deploy(NAME, SYMBOL, 18, SUPPLY);
  });

  describe('Deployment', function () {
    it('should set name, symbol and decimals correctly', async function () {
      // Controle des metadonnees enregistrees par le constructeur
      expect(await token.name()).to.equal(NAME);
      expect(await token.symbol()).to.equal(SYMBOL);
      expect(Number(await token.decimals())).to.equal(18);
      expect(await token.owner()).to.equal(owner.address);
    });

    it('should mint initial supply to owner', async function () {
      // Controle de l'offre initiale creditee au deployeur
      expect(await token.totalSupply()).to.equal(SUPPLY);
      expect(await token.balanceOf(owner.address)).to.equal(SUPPLY);
    });
  });

  describe('transfer()', function () {
    it('should transfer tokens and emit Transfer event', async function () {
      const amount = ethers.parseEther('100');

      // Controle de l'evenement emis lors du transfert
      await expect(token.transfer(alice.address, amount))
        .to.emit(token, 'Transfer')
        .withArgs(owner.address, alice.address, amount);

      // Controle des soldes apres transfert
      expect(await token.balanceOf(alice.address)).to.equal(amount);
      expect(await token.balanceOf(owner.address)).to.equal(SUPPLY - amount);
    });

    it('should revert with InsufficientBalance if sender has not enough', async function () {
      const amount = ethers.parseEther('1');

      // Alice possede un solde nul au moment de l'appel
      await expect(token.connect(alice).transfer(bob.address, amount))
        .to.be.revertedWithCustomError(token, 'InsufficientBalance')
        .withArgs(0n, amount);
    });

    it('should revert with ZeroAddress if recipient is address(0)', async function () {
      // Controle du rejet de l'adresse nulle comme destinataire
      await expect(
        token.transfer(ethers.ZeroAddress, ethers.parseEther('1'))
      ).to.be.revertedWithCustomError(token, 'ZeroAddress');
    });
  });

  describe('approve() and transferFrom()', function () {
    it('should allow transferFrom after approve', async function () {
      const allowanceAmount = ethers.parseEther('500');
      const transferAmount = ethers.parseEther('200');

      // Autorisation accordee par owner a alice
      await expect(token.approve(alice.address, allowanceAmount))
        .to.emit(token, 'Approval')
        .withArgs(owner.address, alice.address, allowanceAmount);

      // Consommation partielle de l'autorisation par alice
      await token
        .connect(alice)
        .transferFrom(owner.address, bob.address, transferAmount);

      expect(await token.balanceOf(bob.address)).to.equal(transferAmount);
      expect(await token.balanceOf(owner.address)).to.equal(SUPPLY - transferAmount);
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        allowanceAmount - transferAmount
      );
    });

    it('should revert if allowance exceeded', async function () {
      const allowanceAmount = ethers.parseEther('10');
      const transferAmount = ethers.parseEther('11');

      await token.approve(alice.address, allowanceAmount);

      // Controle du rejet lorsque le montant depasse l'autorisation
      await expect(
        token.connect(alice).transferFrom(owner.address, bob.address, transferAmount)
      )
        .to.be.revertedWithCustomError(token, 'InsufficientAllowance')
        .withArgs(allowanceAmount, transferAmount);
    });

    it('should support infinite approval (uint256.max)', async function () {
      const transferAmount = ethers.parseEther('1000');

      await token.approve(alice.address, ethers.MaxUint256);
      await token
        .connect(alice)
        .transferFrom(owner.address, bob.address, transferAmount);

      // Autorisation infinie conservee apres consommation
      expect(await token.allowance(owner.address, alice.address)).to.equal(
        ethers.MaxUint256
      );
      expect(await token.balanceOf(bob.address)).to.equal(transferAmount);
    });
  });

  describe('mint() and burn()', function () {
    it('owner can mint additional tokens', async function () {
      const amount = ethers.parseEther('1000');

      // Frappe emise depuis l'adresse nulle selon la norme EIP-20
      await expect(token.mint(alice.address, amount))
        .to.emit(token, 'Transfer')
        .withArgs(ethers.ZeroAddress, alice.address, amount);

      expect(await token.totalSupply()).to.equal(SUPPLY + amount);
      expect(await token.balanceOf(alice.address)).to.equal(amount);
    });

    it('non-owner cannot mint', async function () {
      // Controle de la restriction d'acces du modifier onlyOwner
      await expect(
        token.connect(alice).mint(alice.address, ethers.parseEther('1'))
      ).to.be.revertedWithCustomError(token, 'Unauthorized');
    });

    it('any user can burn their own tokens', async function () {
      const amount = ethers.parseEther('100');

      // Destruction dirigee vers l'adresse nulle selon la norme EIP-20
      await expect(token.burn(amount))
        .to.emit(token, 'Transfer')
        .withArgs(owner.address, ethers.ZeroAddress, amount);

      expect(await token.totalSupply()).to.equal(SUPPLY - amount);
      expect(await token.balanceOf(owner.address)).to.equal(SUPPLY - amount);
    });
  });
});
