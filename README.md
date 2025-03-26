# Interactive Cryptocurrency Lab

A functional cryptocurrency laboratory that demonstrates blockchain concepts through hands-on interaction.

## Overview

This project provides a fully interactive cryptocurrency lab where you can:

- Create and manage blockchain wallets
- Make transactions between wallets
- Mine blocks to confirm transactions
- View the blockchain and transaction history
- Explore all key cryptocurrency concepts in action

## Components

### 1. Blockchain Core (`blockchain.py`)

The blockchain implementation includes:
- Block creation and chaining
- Proof of Work mining with difficulty adjustment
- Transaction validation
- Chain integrity verification
- Balance tracking

### 2. Wallet System (`wallet.py`)

The wallet functionality includes:
- Private/public key generation
- Address creation
- Transaction signing
- Balance tracking
- Wallet import/export

### 3. Transaction System (`transaction.py`)

The transaction system includes:
- Transaction creation and signing
- Transaction pool management
- Transaction lifecycle tracking
- Transaction history

### 4. Web Interface (`app.py`)

The web interface provides:
- Blockchain explorer
- Wallet management
- Transaction creation and tracking
- Block mining interface
- Real-time updates

## Installation

### Prerequisites

- Python 3.6 or higher
- pip (Python package manager)

### Setup

1. Clone this repository:
```
git clone https://github.com/your-username/interactive-crypto-lab.git
cd interactive-crypto-lab
```

2. Install dependencies:
```
pip install cryptography pycryptodome flask
```

3. Run the application:
```
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage Guide

### Creating a Wallet

1. Click on "Wallets" in the navigation menu
2. Click the "Create New Wallet" button
3. Your new wallet will be created with a unique address

### Making a Transaction

1. Click on "Transactions" in the navigation menu
2. Click "Create New Transaction"
3. Select the sender wallet (must have funds)
4. Select the recipient wallet
5. Enter the amount to send
6. Click "Create Transaction"

### Mining a Block

1. Click on "Mine" in the navigation menu
2. Select a wallet to receive the mining reward
3. Click "Start Mining"
4. Wait for the mining process to complete
5. View the newly mined block and your mining reward

### Viewing the Blockchain

1. Click on "Blockchain" in the navigation menu
2. Browse through all blocks in the chain
3. Click on any block to view its details and transactions

### Checking Wallet Balance and History

1. Click on "Wallets" in the navigation menu
2. Click on a specific wallet address
3. View the wallet's balance and transaction history

## Technical Details

### Blockchain Implementation

The blockchain uses a Proof of Work consensus mechanism similar to Bitcoin. Each block contains:

- Index: Position in the blockchain
- Timestamp: When the block was created
- Transactions: List of transactions included in the block
- Previous Hash: Hash of the previous block
- Nonce: Number used for mining
- Hash: The block's own hash

Mining difficulty is set to require a specific number of leading zeros in the block hash, making it computationally intensive to find a valid hash.

### Wallet Implementation

Wallets use asymmetric cryptography (RSA) for security:

- Private Key: Used to sign transactions (kept secret)
- Public Key: Used to verify signatures and generate addresses
- Address: Derived from the public key using hashing

### Transaction Implementation

Transactions include:

- Sender: Wallet address of the sender
- Recipient: Wallet address of the recipient
- Amount: Amount of cryptocurrency to transfer
- Timestamp: When the transaction was created
- Signature: Digital signature proving the sender authorized the transaction
- Status: Current state (pending, confirmed, rejected)

## Educational Value

This lab demonstrates key cryptocurrency concepts:

1. **Blockchain**: See how blocks link together to form an immutable chain
2. **Mining**: Experience the computational work required to secure the network
3. **Wallets**: Understand how cryptographic keys secure digital assets
4. **Transactions**: Learn how value transfers are created, signed, and verified
5. **Consensus**: Observe how the network agrees on the state of the ledger

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project is for educational purposes only and is not intended for production use or real cryptocurrency transactions.
