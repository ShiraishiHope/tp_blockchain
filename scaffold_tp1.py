"""Generation de tous les fichiers du TP1 ERC-20."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent

FILES = {}

# ---------------------------------------------------------------- foundry.toml
FILES["foundry.toml"] = """[profile.default]
src = 'contracts'
test = 'test'
script = 'script'
out = 'out'
libs = ['lib', 'node_modules']
cache_path = 'cache_forge'
solc = '0.8.24'
optimizer = true
optimizer_runs = 200
via_ir = false
remappings = [
    'forge-std/=lib/forge-std/src/',
    '@openzeppelin/=node_modules/@openzeppelin/',
]

[fuzz]
runs = 256
"""

# ----------------------------------------------------------- hardhat.config.ts
FILES["hardhat.config.ts"] = """import { HardhatUserConfig } from 'hardhat/config';
import '@nomicfoundation/hardhat-toolbox';
import 'hardhat-gas-reporter';
import * as dotenv from 'dotenv';

dotenv.config();

const config: HardhatUserConfig = {
  solidity: {
    version: '0.8.24',
    settings: {
      // Optimiseur active avec un profil equilibre entre taille et cout d'appel
      optimizer: { enabled: true, runs: 200 },
      // Compilation via la representation intermediaire Yul
      viaIR: true,
    },
  },
  networks: {
    hardhat: { chainId: 31337 },
    sepolia: {
      url: process.env.RPC_URL_SEPOLIA ?? '',
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
  etherscan: {
    // Cle unique multi-chaines du format Etherscan API V2
    apiKey: process.env.ETHERSCAN_API_KEY ?? '',
  },
  gasReporter: {
    enabled: true,
    currency: 'EUR',
    outputFile: 'gas-report.txt',
    noColors: true,
  },
};

export default config;
"""

# ------------------------------------------------------- contracts/IERC20.sol
FILES["contracts/IERC20.sol"] = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IERC20 — Interface standard EIP-20
interface IERC20 {
    function totalSupply() external view returns (uint256);

    function balanceOf(address account) external view returns (uint256);

    function transfer(address to, uint256 amount) external returns (bool);

    function allowance(address owner, address spender) external view returns (uint256);

    function approve(address spender, uint256 amount) external returns (bool);

    function transferFrom(address from, address to, uint256 amount) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
}
"""

# ------------------------------------------------------ contracts/MyToken.sol
FILES["contracts/MyToken.sol"] = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import './IERC20.sol';

/// @title MyToken — Token ERC-20 pedagogique
/// @notice Implementation complete de l'interface EIP-20 avec administration par un proprietaire
/// @dev Arithmetique verifiee par defaut en Solidity 0.8.x, blocs unchecked limites aux cas prouves
contract MyToken is IERC20 {
    // -- Storage ---------------------------------------------------

    /// @notice Nom lisible du token
    string public name;

    /// @notice Symbole court du token
    string public symbol;

    /// @notice Nombre de decimales, fige au deploiement
    uint8 public immutable decimals;

    /// @notice Quantite totale de tokens en circulation
    uint256 public totalSupply;

    /// @notice Adresse detenant les droits d'administration
    address public owner;

    /// @notice Solde de tokens par adresse
    mapping(address => uint256) public balanceOf;

    /// @notice Allocation accordee par un proprietaire a un depensier
    mapping(address => mapping(address => uint256)) public allowance;

    // -- Erreurs custom --------------------------------------------

    /// @notice Appelant depourvu des droits d'administration
    error Unauthorized();

    /// @notice Solde insuffisant pour l'operation demandee
    error InsufficientBalance(uint256 available, uint256 required);

    /// @notice Allocation insuffisante pour l'operation demandee
    error InsufficientAllowance(uint256 available, uint256 required);

    /// @notice Adresse nulle interdite dans ce contexte
    error ZeroAddress();

    /// @notice Montant nul interdit dans ce contexte
    error ZeroAmount();

    // -- Events supplementaires ------------------------------------

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    // -- Modificateurs ---------------------------------------------

    /// @notice Restriction de l'execution aux seuls appels emis par owner
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // -- Constructor -----------------------------------------------

    /// @notice Initialisation des metadonnees et frappe de l'offre initiale
    /// @param _name Nom du token
    /// @param _symbol Symbole du token
    /// @param _decimals Nombre de decimales
    /// @param _initialSupply Offre initiale attribuee au deployeur
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _decimals,
        uint256 _initialSupply
    ) {
        // Enregistrement des metadonnees du token
        name = _name;
        symbol = _symbol;
        decimals = _decimals;

        // Attribution des droits d'administration au deployeur
        owner = msg.sender;

        // Frappe de l'offre initiale au profit du deployeur
        _mint(msg.sender, _initialSupply);
    }

    // -- Fonctions ERC-20 publiques --------------------------------

    /// @notice Transfert de tokens depuis l'appelant vers un destinataire
    /// @param to Adresse destinataire
    /// @param amount Montant transfere
    /// @return Booleen de succes impose par la norme EIP-20
    function transfer(address to, uint256 amount) external returns (bool) {
        // Rejet de l'adresse nulle comme destinataire
        if (to == address(0)) revert ZeroAddress();

        _transfer(msg.sender, to, amount);

        return true;
    }

    /// @notice Attribution d'une allocation a un depensier
    /// @param spender Adresse autorisee a depenser
    /// @param amount Montant de l'allocation
    /// @return Booleen de succes impose par la norme EIP-20
    function approve(address spender, uint256 amount) external returns (bool) {
        // Rejet de l'adresse nulle comme depensier
        if (spender == address(0)) revert ZeroAddress();

        // Ecrasement de l'allocation precedente
        allowance[msg.sender][spender] = amount;

        emit Approval(msg.sender, spender, amount);

        return true;
    }

    /// @notice Transfert delegue consommant l'allocation de l'appelant
    /// @param from Adresse source des tokens
    /// @param to Adresse destinataire
    /// @param amount Montant transfere
    /// @return Booleen de succes impose par la norme EIP-20
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) external returns (bool) {
        // Rejet de l'adresse nulle comme destinataire
        if (to == address(0)) revert ZeroAddress();

        // Lecture unique de l'allocation pour limiter les acces au storage
        uint256 allowed = allowance[from][msg.sender];

        // Cas d'une allocation infinie laissee inchangee, economie d'un SSTORE
        if (allowed != type(uint256).max) {
            if (allowed < amount) revert InsufficientAllowance(allowed, amount);

            // Soustraction sans verification, bornee par le controle precedent
            unchecked {
                allowance[from][msg.sender] = allowed - amount;
            }
        }

        _transfer(from, to, amount);

        return true;
    }

    // -- Fonctions admin -------------------------------------------

    /// @notice Frappe de nouveaux tokens reservee au proprietaire
    /// @param to Adresse creditee
    /// @param amount Montant cree
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /// @notice Destruction de tokens detenus par l'appelant
    /// @param amount Montant detruit
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }

    /// @notice Transfert des droits d'administration
    /// @param newOwner Adresse du nouveau proprietaire
    function transferOwnership(address newOwner) external onlyOwner {
        // Rejet de l'adresse nulle comme nouveau proprietaire
        if (newOwner == address(0)) revert ZeroAddress();

        emit OwnershipTransferred(owner, newOwner);

        owner = newOwner;
    }

    // -- Fonctions internes ----------------------------------------

    /// @notice Deplacement de tokens entre deux adresses
    /// @dev Controle de solde prealable puis arithmetique non verifiee
    function _transfer(address from, address to, uint256 amount) internal {
        uint256 bal = balanceOf[from];
        if (bal < amount) revert InsufficientBalance(bal, amount);
        unchecked {
            balanceOf[from] = bal - amount;
            balanceOf[to] += amount;
        }
        emit Transfer(from, to, amount);
    }

    /// @notice Creation de tokens et augmentation de l'offre totale
    /// @dev Arithmetique verifiee, le depassement de uint256 provoque un revert
    function _mint(address to, uint256 amount) internal {
        if (to == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        totalSupply += amount;
        balanceOf[to] += amount;
        emit Transfer(address(0), to, amount);
    }

    /// @notice Destruction de tokens et reduction de l'offre totale
    /// @dev Controle de solde prealable puis arithmetique non verifiee
    function _burn(address from, uint256 amount) internal {
        uint256 bal = balanceOf[from];
        if (bal < amount) revert InsufficientBalance(bal, amount);
        unchecked {
            balanceOf[from] = bal - amount;
            totalSupply -= amount;
        }
        emit Transfer(from, address(0), amount);
    }
}
"""

# ------------------------------------------------------ test/MyToken.test.ts
FILES["test/MyToken.test.ts"] = """import { expect } from 'chai';
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
"""

# --------------------------------------------------------- test/MyToken.t.sol
FILES["test/MyToken.t.sol"] = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import 'forge-std/Test.sol';
import '../contracts/MyToken.sol';

/// @title MyTokenTest — Suite de tests Foundry du token MyToken
contract MyTokenTest is Test {
    MyToken token;
    address owner = makeAddr('owner');
    address alice = makeAddr('alice');
    address bob = makeAddr('bob');
    uint256 SUPPLY = 1_000_000 ether;

    function setUp() public {
        // Deploiement effectue au nom de owner
        vm.prank(owner);
        token = new MyToken('MyToken', 'MTK', 18, SUPPLY);
    }

    // --- Tests unitaires ---

    function test_InitialState() public view {
        // Controle des metadonnees et de l'offre initiale
        assertEq(token.name(), 'MyToken');
        assertEq(token.symbol(), 'MTK');
        assertEq(token.decimals(), 18);
        assertEq(token.totalSupply(), SUPPLY);
        assertEq(token.balanceOf(owner), SUPPLY);
        assertEq(token.owner(), owner);
    }

    function test_Transfer() public {
        uint256 amount = 100 ether;

        vm.prank(owner);
        token.transfer(alice, amount);

        // Controle des soldes apres transfert
        assertEq(token.balanceOf(alice), amount);
        assertEq(token.balanceOf(owner), SUPPLY - amount);
    }

    function test_RevertIf_InsufficientBalance() public {
        // Alice possede un solde nul au moment de l'appel
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(MyToken.InsufficientBalance.selector, 0, 1 ether)
        );
        token.transfer(bob, 1 ether);
    }

    function test_RevertIf_TransferToZeroAddress() public {
        vm.prank(owner);
        vm.expectRevert(MyToken.ZeroAddress.selector);
        token.transfer(address(0), 1 ether);
    }

    function test_Approve() public {
        vm.prank(owner);
        token.approve(alice, 500 ether);

        assertEq(token.allowance(owner, alice), 500 ether);
    }

    function test_RevertIf_ApproveZeroAddress() public {
        vm.prank(owner);
        vm.expectRevert(MyToken.ZeroAddress.selector);
        token.approve(address(0), 1 ether);
    }

    function test_TransferFrom() public {
        vm.prank(owner);
        token.approve(alice, 500 ether);

        vm.prank(alice);
        token.transferFrom(owner, bob, 200 ether);

        // Controle du solde credite et de l'autorisation restante
        assertEq(token.balanceOf(bob), 200 ether);
        assertEq(token.allowance(owner, alice), 300 ether);
    }

    function test_InfiniteApprovalIsNotDecreased() public {
        vm.prank(owner);
        token.approve(alice, type(uint256).max);

        vm.prank(alice);
        token.transferFrom(owner, bob, 1000 ether);

        // Autorisation infinie conservee apres consommation
        assertEq(token.allowance(owner, alice), type(uint256).max);
    }

    function test_RevertIf_TransferFromToZeroAddress() public {
        vm.prank(owner);
        token.approve(alice, 500 ether);

        vm.prank(alice);
        vm.expectRevert(MyToken.ZeroAddress.selector);
        token.transferFrom(owner, address(0), 1 ether);
    }

    function test_Mint() public {
        vm.prank(owner);
        token.mint(alice, 1000 ether);

        assertEq(token.totalSupply(), SUPPLY + 1000 ether);
        assertEq(token.balanceOf(alice), 1000 ether);
    }

    function test_RevertIf_MintFromNonOwner() public {
        vm.prank(alice);
        vm.expectRevert(MyToken.Unauthorized.selector);
        token.mint(alice, 1 ether);
    }

    function test_RevertIf_MintZeroAmount() public {
        vm.prank(owner);
        vm.expectRevert(MyToken.ZeroAmount.selector);
        token.mint(alice, 0);
    }

    function test_RevertIf_MintToZeroAddress() public {
        vm.prank(owner);
        vm.expectRevert(MyToken.ZeroAddress.selector);
        token.mint(address(0), 1 ether);
    }

    function test_Burn() public {
        vm.prank(owner);
        token.burn(100 ether);

        assertEq(token.totalSupply(), SUPPLY - 100 ether);
        assertEq(token.balanceOf(owner), SUPPLY - 100 ether);
    }

    function test_RevertIf_BurnMoreThanBalance() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(MyToken.InsufficientBalance.selector, 0, 1 ether)
        );
        token.burn(1 ether);
    }

    function test_TransferOwnership() public {
        vm.prank(owner);
        token.transferOwnership(alice);

        assertEq(token.owner(), alice);
    }

    function test_RevertIf_TransferOwnershipToZeroAddress() public {
        vm.prank(owner);
        vm.expectRevert(MyToken.ZeroAddress.selector);
        token.transferOwnership(address(0));
    }

    function test_RevertIf_TransferOwnershipFromNonOwner() public {
        vm.prank(alice);
        vm.expectRevert(MyToken.Unauthorized.selector);
        token.transferOwnership(alice);
    }

    /// @notice Mesure du cout de deploiement pour la question Q4
    function test_DeploymentGas() public {
        uint256 gasBefore = gasleft();
        MyToken fresh = new MyToken('MyToken', 'MTK', 18, SUPPLY);
        uint256 gasUsed = gasBefore - gasleft();

        emit log_named_uint('deployment gas', gasUsed);
        assertEq(fresh.totalSupply(), SUPPLY);
    }

    // --- Tests de fuzzing ---

    /// @notice Le fuzzing genere des valeurs aleatoires pour to et amount
    function testFuzz_TransferConservesTotalSupply(
        address to,
        uint256 amount
    ) public {
        // Filtrage des destinataires invalides
        vm.assume(to != address(0));
        vm.assume(to != owner);

        // Bornage du montant dans les limites du solde de owner
        amount = bound(amount, 0, SUPPLY);

        uint256 totalBefore = token.totalSupply();

        vm.prank(owner);
        token.transfer(to, amount);

        // L'offre totale reste constante lors d'un transfert
        assertEq(token.totalSupply(), totalBefore);
        assertEq(token.balanceOf(to), amount);
        assertEq(token.balanceOf(owner), SUPPLY - amount);
    }

    /// @notice Le fuzzing couvre les deux branches de la verification d'autorisation
    function testFuzz_ApproveAndTransferFrom(
        uint256 approveAmt,
        uint256 transferAmt
    ) public {
        // Bornage des deux montants dans les limites du solde de owner
        approveAmt = bound(approveAmt, 0, SUPPLY);
        transferAmt = bound(transferAmt, 0, SUPPLY);

        vm.prank(owner);
        token.approve(alice, approveAmt);

        if (transferAmt > approveAmt) {
            // Branche de rejet pour autorisation insuffisante
            vm.prank(alice);
            vm.expectRevert(
                abi.encodeWithSelector(
                    MyToken.InsufficientAllowance.selector,
                    approveAmt,
                    transferAmt
                )
            );
            token.transferFrom(owner, bob, transferAmt);
        } else {
            // Branche nominale avec decrement de l'autorisation
            vm.prank(alice);
            token.transferFrom(owner, bob, transferAmt);

            assertEq(token.balanceOf(bob), transferAmt);
            assertEq(token.allowance(owner, alice), approveAmt - transferAmt);
        }
    }

    // --- Invariants ---

    /// @notice Foundry evalue cet invariant apres chaque sequence d'actions
    function invariant_totalSupplyIsConsistent() public view {
        // Aucune frappe ni destruction accessible aux appelants aleatoires
        assertEq(token.totalSupply(), SUPPLY);
    }
}
"""

# ---------------------------------------------------------- scripts/deploy.ts
FILES["scripts/deploy.ts"] = """import { ethers, run, network } from 'hardhat';

async function main() {
  const [deployer] = await ethers.getSigners();
  const balance = await deployer.provider.getBalance(deployer.address);

  console.log('Deploying from :', deployer.address);
  console.log('Balance        :', ethers.formatEther(balance), 'ETH');

  // Garde-fou contre un solde trop faible pour couvrir le gas
  if (balance < ethers.parseEther('0.01')) {
    throw new Error('Balance insuffisante — recuperez des ETH Sepolia sur un faucet');
  }

  const SUPPLY = ethers.parseEther('1000000');
  const Token = await ethers.getContractFactory('MyToken');

  console.log('Deploying MyToken...');
  const token = await Token.deploy('MyToken', 'MTK', 18, SUPPLY);
  await token.waitForDeployment();

  const addr = await token.getAddress();
  console.log('MyToken deployed to:', addr);
  console.log('TX hash            :', token.deploymentTransaction()?.hash);

  // Verification Etherscan reservee aux reseaux publics
  if (network.name !== 'hardhat' && network.name !== 'localhost') {
    console.log('Waiting 5 blocks for Etherscan indexing...');
    await token.deploymentTransaction()?.wait(5);

    await run('verify:verify', {
      address: addr,
      constructorArguments: ['MyToken', 'MTK', 18, SUPPLY],
    });

    console.log('Contract verified on Etherscan!');
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
"""

# --------------------------------------------------------------- .env.example
FILES[".env.example"] = """RPC_URL_SEPOLIA=https://eth-sepolia.g.alchemy.com/v2/VOTRE_CLE
PRIVATE_KEY=0xVOTRE_CLE_PRIVEE_WALLET_TEST
ETHERSCAN_API_KEY=VOTRE_CLE_ETHERSCAN
"""

# ------------------------------------------------------------------ gitignore
FILES[".gitignore"] = """node_modules/
.env
artifacts/
cache/
cache_forge/
out/
typechain-types/
broadcast/
.gas-tmp
"""

# ---------------------------------------------------- tools/gas_experiments.py
FILES["tools/gas_experiments.py"] = '''"""Mesures comparatives de gas pour les questions Q2, Q3, Q4 et Q5 du TP1."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "MyToken.sol"
FOUNDRY = ROOT / "foundry.toml"
SNAP = ROOT / ".gas-tmp"

# Bloc arithmetique non verifie present dans _transfer
UNCHECKED_BLOCK = """        unchecked {
            balanceOf[from] = bal - amount;
            balanceOf[to] += amount;
        }"""

# Equivalent arithmetique verifie utilise pour la question Q2
CHECKED_BLOCK = """        balanceOf[from] = bal - amount;
        balanceOf[to] += amount;"""

# Controle de solde par erreur custom present dans _transfer et _burn
CUSTOM_ERROR = "        if (bal < amount) revert InsufficientBalance(bal, amount);"

# Equivalent par require et chaine de caracteres utilise pour la question Q3
REQUIRE_STRING = "        require(bal >= amount, 'MyToken: insufficient balance');"


def run_snapshot(label):
    """Execution du test test_Transfer et extraction du gas consomme."""
    result = subprocess.run(
        [
            "forge", "snapshot",
            "--snap", str(SNAP),
            "--match-contract", "MyTokenTest",
            "--match-test", "^test_Transfer$",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Echec de la mesure pour la variante", label, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    match = re.search(r"test_Transfer\\(\\)\\s*\\(gas:\\s*(\\d+)\\)", SNAP.read_text())

    if match is None:
        print("Aucune valeur de gas trouvee pour la variante", label, file=sys.stderr)
        sys.exit(1)

    return int(match.group(1))


def run_deployment_gas():
    """Execution du test test_DeploymentGas et extraction du cout de deploiement."""
    result = subprocess.run(
        ["forge", "test", "--match-test", "test_DeploymentGas", "-vv"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    match = re.search(r"deployment gas:\\s*(\\d+)", result.stdout)

    return int(match.group(1)) if match else None


def measure_variant(label, replacements):
    """Application temporaire de modifications du contrat puis mesure du gas."""
    original = CONTRACT.read_text()
    patched = original

    for old, new in replacements:
        if old not in patched:
            print("Motif introuvable dans MyToken.sol pour", label, file=sys.stderr)
            sys.exit(1)
        patched = patched.replace(old, new)

    CONTRACT.write_text(patched)
    try:
        return run_snapshot(label)
    finally:
        CONTRACT.write_text(original)


def measure_optimizer(runs):
    """Modification temporaire du nombre de passes de l'optimiseur puis mesure."""
    original = FOUNDRY.read_text()
    patched = re.sub(r"optimizer_runs = \\d+", "optimizer_runs = " + str(runs), original)

    FOUNDRY.write_text(patched)
    try:
        return run_snapshot("optimizer_runs=" + str(runs))
    finally:
        FOUNDRY.write_text(original)


def main():
    lines = []

    baseline = run_snapshot("baseline")
    lines.append("Q1 — gas de transfer() (implementation de reference) : " + str(baseline))

    checked = measure_variant("sans unchecked", [(UNCHECKED_BLOCK, CHECKED_BLOCK)])
    lines.append(
        "Q2 — gas de transfer() sans bloc unchecked : "
        + str(checked)
        + "  (ecart : "
        + str(checked - baseline)
        + ")"
    )

    with_require = measure_variant(
        "require avec chaine", [(CUSTOM_ERROR, REQUIRE_STRING)]
    )
    lines.append(
        "Q3 — gas de transfer() avec require et chaine : "
        + str(with_require)
        + "  (ecart : "
        + str(with_require - baseline)
        + ")"
    )

    deployment = run_deployment_gas()
    lines.append("Q4 — gas du constructeur : " + str(deployment))

    for runs in (1, 200, 1000):
        value = measure_optimizer(runs)
        lines.append(
            "Q5 — gas de transfer() avec optimizer_runs=" + str(runs) + " : " + str(value)
        )

    if SNAP.exists():
        SNAP.unlink()

    report = "\\n".join(lines)
    print(report)
    (ROOT / "gas-analysis.txt").write_text(report + "\\n")


if __name__ == "__main__":
    main()
'''

# ----------------------------------------------------------------- README.md
FILES["README.md"] = """# TP1 — Token ERC-20 from scratch (Hardhat + Foundry)

M2 AL/IABD — Blockchain & Developpement — 2025-2026

## Description

Implementation complete d'un token ERC-20 conforme a l'EIP-20, ecrite sans
dependance externe. Le contrat utilise des erreurs custom plutot que des chaines
`require`, un bloc `unchecked` la ou le controle prealable rend le depassement
impossible, et le pattern Checks-Effects-Interactions sur l'ensemble des
fonctions mutantes.

Le workspace combine deux outillages sur la meme base de code : Hardhat pour les
tests TypeScript, le rapport de gas et le deploiement, Foundry pour les tests
Solidity natifs, le fuzzing et les snapshots de gas.

## Structure

```
contracts/IERC20.sol        interface standard EIP-20
contracts/MyToken.sol       implementation du token
test/MyToken.test.ts        tests TypeScript (Hardhat + Chai)
test/MyToken.t.sol          tests Solidity (Foundry + fuzzing)
scripts/deploy.ts           deploiement et verification Etherscan
tools/gas_experiments.py    mesures comparatives de gas
```

## Installation

```bash
npm install
forge install foundry-rs/forge-std
cp .env.example .env
```

Le fichier `.env` doit contenir l'URL RPC Sepolia, la cle privee d'un wallet de
developpement et une cle API Etherscan.

## Commandes

```bash
npx hardhat compile              # compilation et generation des types
npx hardhat test                 # tests TypeScript et gas-report.txt
npx hardhat coverage             # couverture de code cote Hardhat
forge build                      # compilation Foundry
forge test -vv                   # tests Solidity et fuzzing
forge test --fuzz-runs 1000      # fuzzing etendu
forge coverage --report summary  # couverture de code cote Foundry
forge snapshot                   # generation de .gas-snapshot
python3 tools/gas_experiments.py # mesures des questions Q1 a Q5
```

## Deploiement

```bash
npx hardhat run scripts/deploy.ts --network sepolia
```

## Adresse deployee

Reseau : Sepolia (chainId 11155111)
Adresse : A_COMPLETER
Etherscan : A_COMPLETER
"""


def main():
    """Ecriture de l'ensemble des fichiers du projet."""
    for relative_path, content in FILES.items():
        target = ROOT / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print("ecrit :", relative_path)


if __name__ == "__main__":
    main()