// SPDX-License-Identifier: MIT
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
