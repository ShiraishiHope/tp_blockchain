import { ethers, run, network } from 'hardhat';

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
