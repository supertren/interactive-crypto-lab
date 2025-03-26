#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wallet Implementation
-------------------
This module implements cryptocurrency wallet functionality for the interactive
cryptocurrency lab, including key generation, address management, and transaction signing.
"""

import hashlib
import binascii
import os
import json
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

class Wallet:
    """
    A cryptocurrency wallet that manages keys and addresses.
    
    The wallet handles:
    - Private/public key generation
    - Address creation
    - Transaction signing
    - Balance tracking
    """
    
    def __init__(self, blockchain_instance=None, private_key=None):
        """
        Initialize a new wallet.
        
        Args:
            blockchain_instance: Reference to the blockchain (optional)
            private_key: Existing private key to import (optional)
        """
        self.blockchain = blockchain_instance
        
        if private_key:
            self.private_key = RSA.import_key(private_key)
        else:
            # Generate a new key pair
            self.private_key = RSA.generate(2048)
            
        # Extract public key
        self.public_key = self.private_key.publickey()
        
        # Generate address from public key
        self.address = self._generate_address()
    
    def _generate_address(self):
        """
        Generate a wallet address from the public key.
        
        Returns:
            A string representation of the wallet address
        """
        # Export public key in DER format
        public_key_bytes = self.public_key.export_key(format='DER')
        
        # Hash the public key using SHA-256
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        
        # Further hash it with RIPEMD-160 (simulated with another SHA-256 for simplicity)
        ripemd160_hash = hashlib.sha256(sha256_hash).digest()
        
        # Create a simple address format (in a real implementation, we would add checksums and encoding)
        address = binascii.hexlify(ripemd160_hash).decode('ascii')[:40]
        
        return address
    
    def get_balance(self):
        """
        Get the current balance of this wallet.
        
        Returns:
            The wallet balance or None if no blockchain is connected
        """
        if self.blockchain:
            return self.blockchain.get_balance(self.address)
        return None
    
    def get_transaction_history(self):
        """
        Get the transaction history for this wallet.
        
        Returns:
            List of transactions involving this wallet or None if no blockchain is connected
        """
        if self.blockchain:
            return self.blockchain.get_address_transactions(self.address)
        return None
    
    def create_transaction(self, recipient_address, amount):
        """
        Create and sign a new transaction.
        
        Args:
            recipient_address: The recipient's wallet address
            amount: The amount to transfer
            
        Returns:
            A signed transaction dictionary
        
        Raises:
            ValueError: If the wallet has insufficient funds
        """
        if self.blockchain:
            balance = self.get_balance()
            if balance < amount:
                raise ValueError(f"Insufficient funds. Available: {balance}, Required: {amount}")
        
        # Create transaction data
        transaction_data = {
            'sender': self.address,
            'recipient': recipient_address,
            'amount': amount
        }
        
        # Convert to string for signing
        transaction_string = json.dumps(transaction_data, sort_keys=True).encode()
        
        # Create hash of the transaction
        transaction_hash = SHA256.new(transaction_string)
        
        # Sign the transaction
        signature = pkcs1_15.new(self.private_key).sign(transaction_hash)
        
        # Convert signature to string format for storage
        signature_str = binascii.hexlify(signature).decode('ascii')
        
        # Add signature to transaction
        transaction_data['signature'] = signature_str
        
        return transaction_data
    
    def send_transaction(self, recipient_address, amount):
        """
        Create, sign, and send a transaction to the blockchain.
        
        Args:
            recipient_address: The recipient's wallet address
            amount: The amount to transfer
            
        Returns:
            The index of the block that will include this transaction
            
        Raises:
            ValueError: If the wallet has insufficient funds or no blockchain is connected
        """
        if not self.blockchain:
            raise ValueError("No blockchain connected to this wallet")
        
        # Create and sign transaction
        transaction = self.create_transaction(recipient_address, amount)
        
        # Send to blockchain
        return self.blockchain.add_transaction(
            transaction['sender'],
            transaction['recipient'],
            transaction['amount'],
            transaction['signature']
        )
    
    def export_private_key(self):
        """
        Export the private key.
        
        Returns:
            The private key in PEM format
        """
        return self.private_key.export_key().decode('ascii')
    
    def export_public_key(self):
        """
        Export the public key.
        
        Returns:
            The public key in PEM format
        """
        return self.public_key.export_key().decode('ascii')
    
    def to_dict(self):
        """
        Convert wallet to dictionary for serialization.
        
        Note: This includes the private key, so handle with care!
        """
        return {
            'address': self.address,
            'private_key': self.export_private_key(),
            'public_key': self.export_public_key()
        }
    
    def to_json(self):
        """
        Convert wallet to JSON format.
        
        Note: This includes the private key, so handle with care!
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_private_key(cls, private_key_pem, blockchain_instance=None):
        """
        Create a wallet from an existing private key.
        
        Args:
            private_key_pem: Private key in PEM format
            blockchain_instance: Reference to the blockchain (optional)
            
        Returns:
            A new Wallet instance with the imported key
        """
        return cls(blockchain_instance, private_key_pem)
    
    def __str__(self):
        """String representation of the wallet."""
        return f"Wallet Address: {self.address}"


class WalletManager:
    """
    Manages multiple wallets and provides wallet operations.
    """
    
    def __init__(self, blockchain_instance=None):
        """
        Initialize a new wallet manager.
        
        Args:
            blockchain_instance: Reference to the blockchain (optional)
        """
        self.blockchain = blockchain_instance
        self.wallets = {}  # address -> wallet mapping
    
    def create_wallet(self):
        """
        Create a new wallet.
        
        Returns:
            The newly created wallet
        """
        wallet = Wallet(self.blockchain)
        self.wallets[wallet.address] = wallet
        return wallet
    
    def import_wallet(self, private_key_pem):
        """
        Import a wallet from a private key.
        
        Args:
            private_key_pem: Private key in PEM format
            
        Returns:
            The imported wallet
        """
        wallet = Wallet.from_private_key(private_key_pem, self.blockchain)
        self.wallets[wallet.address] = wallet
        return wallet
    
    def get_wallet(self, address):
        """
        Get a wallet by address.
        
        Args:
            address: The wallet address
            
        Returns:
            The wallet or None if not found
        """
        return self.wallets.get(address)
    
    def list_wallets(self):
        """
        Get a list of all wallet addresses.
        
        Returns:
            List of wallet addresses
        """
        return list(self.wallets.keys())
    
    def get_total_balance(self):
        """
        Get the total balance of all wallets.
        
        Returns:
            The total balance
        """
        if not self.blockchain:
            return None
            
        total = 0
        for wallet in self.wallets.values():
            total += wallet.get_balance()
        return total
    
    def save_wallets(self, filename):
        """
        Save all wallets to a file.
        
        Args:
            filename: The file to save to
            
        Note: This saves private keys, so the file should be secured!
        """
        wallet_data = {address: wallet.to_dict() for address, wallet in self.wallets.items()}
        with open(filename, 'w') as f:
            json.dump(wallet_data, f, indent=2)
    
    def load_wallets(self, filename):
        """
        Load wallets from a file.
        
        Args:
            filename: The file to load from
            
        Returns:
            Number of wallets loaded
        """
        try:
            with open(filename, 'r') as f:
                wallet_data = json.load(f)
                
            for address, wallet_dict in wallet_data.items():
                if address not in self.wallets:
                    self.import_wallet(wallet_dict['private_key'])
                    
            return len(wallet_data)
        except (FileNotFoundError, json.JSONDecodeError):
            return 0


# For testing the module directly
if __name__ == "__main__":
    # Import the blockchain module
    from blockchain import Blockchain
    
    # Create a blockchain
    blockchain = Blockchain()
    
    # Create a wallet manager
    wallet_manager = WalletManager(blockchain)
    
    # Create some wallets
    alice_wallet = wallet_manager.create_wallet()
    bob_wallet = wallet_manager.create_wallet()
    miner_wallet = wallet_manager.create_wallet()
    
    print(f"Created wallets:")
    print(f"Alice: {alice_wallet.address}")
    print(f"Bob: {bob_wallet.address}")
    print(f"Miner: {miner_wallet.address}")
    
    # Add some initial coins to Alice (in a real blockchain, this would come from mining)
    blockchain.add_transaction("SYSTEM", alice_wallet.address, 100)
    
    # Mine the block to confirm the transaction
    print("\nMining initial block...")
    blockchain.mine_pending_transactions(miner_wallet.address)
    
    # Wait for mining to complete
    import time
    while blockchain.mining_in_progress:
        time.sleep(0.5)
    
    # Check balances
    print("\nInitial balances:")
    print(f"Alice: {alice_wallet.get_balance()}")
    print(f"Bob: {bob_wallet.get_balance()}")
    print(f"Miner: {miner_wallet.get_balance()}")
    
    # Alice sends coins to Bob
    try:
        print("\nAlice sending 30 coins to Bob...")
        alice_wallet.send_transaction(bob_wallet.address, 30)
        
        # Mine the block to confirm the transaction
        print("Mining transaction block...")
        blockchain.mine_pending_transactions(miner_wallet.address)
        
        # Wait for mining to complete
        while blockchain.mining_in_progress:
            time.sleep(0.5)
        
        # Check updated balances
        print("\nUpdated balances:")
        print(f"Alice: {alice_wallet.get_balance()}")
        print(f"Bob: {bob_wallet.get_balance()}")
        print(f"Miner: {miner_wallet.get_balance()}")
        
    except ValueError as e:
        print(f"Transaction failed: {e}")
    
    # Export and import a wallet
    print("\nExporting and importing Alice's wallet...")
    alice_key = alice_wallet.export_private_key()
    imported_wallet = wallet_manager.import_wallet(alice_key)
    print(f"Original address: {alice_wallet.address}")
    print(f"Imported address: {imported_wallet.address}")
    
    # Save and load wallets
    print("\nSaving wallets to file...")
    wallet_manager.save_wallets("test_wallets.json")
    
    # Create a new wallet manager and load the wallets
    new_manager = WalletManager(blockchain)
    loaded_count = new_manager.load_wallets("test_wallets.json")
    print(f"Loaded {loaded_count} wallets from file.")
    print(f"Addresses: {new_manager.list_wallets()}")
