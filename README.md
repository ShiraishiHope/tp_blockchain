# TP1 — Token ERC-20 from scratch (Hardhat + Foundry)

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
Adresse : 0x06021139e70144Be71e63a6F171762e09812aD31
Etherscan : https://sepolia.etherscan.io/address/0x06021139e70144Be71e63a6F171762e09812aD31#code
