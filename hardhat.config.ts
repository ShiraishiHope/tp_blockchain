import { HardhatUserConfig } from 'hardhat/config';
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
