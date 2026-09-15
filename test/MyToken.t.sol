// SPDX-License-Identifier: MIT
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

        // Restriction du fuzzing d'invariants aux fonctions sans effet sur l'offre
        bytes4[] memory selectors = new bytes4[](4);
        selectors[0] = MyToken.transfer.selector;
        selectors[1] = MyToken.approve.selector;
        selectors[2] = MyToken.transferFrom.selector;
        selectors[3] = MyToken.transferOwnership.selector;

        targetContract(address(token));
        targetSelector(FuzzSelector({addr: address(token), selectors: selectors}));
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
        // Les selecteurs cibles excluent mint et burn, seules sources de variation
        assertEq(token.totalSupply(), SUPPLY);
    }
}
