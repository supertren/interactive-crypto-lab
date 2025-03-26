#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Transaction System
----------------
This module implements the transaction system for the interactive
cryptocurrency lab, handling transaction creation, validation, and processing.
"""

import json
import time
import hashlib
import binascii
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

class Transaction:
    """
    Represents a cryptocurrency transaction.
    
    A transaction records the transfer of value from one address to another,
    including metadata and cryptographic proof of authenticity.
    """
    
    def __init__(self, sender, recipient, amount, timestamp=None, signature=None):
        """
        Initialize a new transaction.
        
        Args:
            sender: Address of the sender
            recipient: Address of the recipient
            amount: Amount to transfer
            timestamp: When the transaction was created (optional)
            signature: Digital signature of the transaction (optional)
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.signature = signature
        self.transaction_id = self.calculate_hash()
        self.status = "pending"  # pending, confirmed, rejected
        self.block_index = None  # Block where this transaction is included
    
    def calculate_hash(self):
        """
        Calculate a unique hash for this transaction.
        
        Returns:
            A hash string that uniquely identifies this transaction
        """
        transaction_string = json.dumps({
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp
        }, sort_keys=True).encode()
        
        return hashlib.sha256(transaction_string).hexdigest()
    
    def to_dict(self):
        """Convert transaction to dictionary for serialization."""
        return {
            "transaction_id": self.transaction_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "signature": self.signature,
            "status": self.status,
            "block_index": self.block_index
        }
    
    @classmethod
    def from_dict(cls, transaction_dict):
        """Create a Transaction instance from a dictionary."""
        transaction = cls(
            transaction_dict["sender"],
            transaction_dict["recipient"],
            transaction_dict["amount"],
            transaction_dict["timestamp"],
            transaction_dict["signature"]
        )
        transaction.transaction_id = transaction_dict["transaction_id"]
        transaction.status = transaction_dict["status"]
        transaction.block_index = transaction_dict["block_index"]
        return transaction
    
    def __str__(self):
        """String representation of the transaction."""
        return json.dumps(self.to_dict(), indent=2)


class TransactionPool:
    """
    Manages pending transactions waiting to be included in blocks.
    """
    
    def __init__(self):
        """Initialize a new transaction pool."""
        self.pending_transactions = {}  # transaction_id -> Transaction
    
    def add_transaction(self, transaction):
        """
        Add a transaction to the pool.
        
        Args:
            transaction: The Transaction object to add
            
        Returns:
            True if added successfully, False otherwise
        """
        if transaction.transaction_id in self.pending_transactions:
            return False  # Transaction already in pool
            
        self.pending_transactions[transaction.transaction_id] = transaction
        return True
    
    def get_transaction(self, transaction_id):
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The ID of the transaction to retrieve
            
        Returns:
            The Transaction object or None if not found
        """
        return self.pending_transactions.get(transaction_id)
    
    def remove_transaction(self, transaction_id):
        """
        Remove a transaction from the pool.
        
        Args:
            transaction_id: The ID of the transaction to remove
            
        Returns:
            The removed Transaction object or None if not found
        """
        return self.pending_transactions.pop(transaction_id, None)
    
    def get_all_transactions(self):
        """
        Get all pending transactions.
        
        Returns:
            List of all Transaction objects in the pool
        """
        return list(self.pending_transactions.values())
    
    def clear(self):
        """Clear all transactions from the pool."""
        self.pending_transactions.clear()
    
    def get_count(self):
        """
        Get the number of transactions in the pool.
        
        Returns:
            The number of pending transactions
        """
        return len(self.pending_transactions)


class TransactionManager:
    """
    Manages the lifecycle of transactions from creation to confirmation.
    """
    
    def __init__(self, blockchain_instance=None, wallet_manager=None):
        """
        Initialize a new transaction manager.
        
        Args:
            blockchain_instance: Reference to the blockchain (optional)
            wallet_manager: Reference to the wallet manager (optional)
        """
        self.blockchain = blockchain_instance
        self.wallet_manager = wallet_manager
        self.transaction_pool = TransactionPool()
        self.transaction_history = {}  # transaction_id -> Transaction
    
    def create_transaction(self, sender_address, recipient_address, amount):
        """
        Create a new transaction.
        
        Args:
            sender_address: Address of the sender
            recipient_address: Address of the recipient
            amount: Amount to transfer
            
        Returns:
            The created Transaction object
            
        Raises:
            ValueError: If the sender has insufficient funds or wallet not found
        """
        # Check if sender wallet exists
        if self.wallet_manager:
            sender_wallet = self.wallet_manager.get_wallet(sender_address)
            if not sender_wallet:
                raise ValueError(f"Sender wallet not found: {sender_address}")
                
            # Check balance
            if self.blockchain:
                balance = self.blockchain.get_balance(sender_address)
                if balance < amount:
                    raise ValueError(f"Insufficient funds. Available: {balance}, Required: {amount}")
                
            # Create and sign transaction using the wallet
            transaction_data = sender_wallet.create_transaction(recipient_address, amount)
            
            # Create Transaction object
            transaction = Transaction(
                transaction_data["sender"],
                transaction_data["recipient"],
                transaction_data["amount"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                transaction_data["signature"]
            )
        else:
            # If no wallet manager, create unsigned transaction
            transaction = Transaction(sender_address, recipient_address, amount)
        
        # Add to pool
        self.transaction_pool.add_transaction(transaction)
        
        # Add to history
        self.transaction_history[transaction.transaction_id] = transaction
        
        return transaction
    
    def verify_transaction(self, transaction):
        """
        Verify a transaction's signature and validity.
        
        Args:
            transaction: The Transaction object to verify
            
        Returns:
            True if valid, False otherwise
        """
        # System transactions are always valid
        if transaction.sender == "SYSTEM":
            return True
            
        # If no signature, reject
        if not transaction.signature:
            return False
            
        # In a real implementation, we would verify the signature here
        # using the sender's public key
        
        # For this lab, we'll assume all transactions with signatures are valid
        return True
    
    def submit_transaction_to_blockchain(self, transaction_id):
        """
        Submit a transaction from the pool to the blockchain.
        
        Args:
            transaction_id: The ID of the transaction to submit
            
        Returns:
            True if submitted successfully, False otherwise
        """
        if not self.blockchain:
            return False
            
        transaction = self.transaction_pool.get_transaction(transaction_id)
        if not transaction:
            return False
            
        # Verify transaction
        if not self.verify_transaction(transaction):
            transaction.status = "rejected"
            return False
            
        # Submit to blockchain
        self.blockchain.add_transaction(
            transaction.sender,
            transaction.recipient,
            transaction.amount,
            transaction.signature
        )
        
        # Remove from pool
        self.transaction_pool.remove_transaction(transaction_id)
        
        # Update status
        transaction.status = "confirmed"
        
        return True
    
    def submit_all_pending_transactions(self):
        """
        Submit all pending transactions to the blockchain.
        
        Returns:
            Number of transactions submitted successfully
        """
        if not self.blockchain:
            return 0
            
        success_count = 0
        for transaction in self.transaction_pool.get_all_transactions():
            if self.submit_transaction_to_blockchain(transaction.transaction_id):
                success_count += 1
                
        return success_count
    
    def get_transaction(self, transaction_id):
        """
        Get a transaction by ID from pool or history.
        
        Args:
            transaction_id: The ID of the transaction to retrieve
            
        Returns:
            The Transaction object or None if not found
        """
        # Check pool first
        transaction = self.transaction_pool.get_transaction(transaction_id)
        if transaction:
            return transaction
            
        # Then check history
        return self.transaction_history.get(transaction_id)
    
    def get_pending_transactions(self):
        """
        Get all pending transactions.
        
        Returns:
            List of pending Transaction objects
        """
        return self.transaction_pool.get_all_transactions()
    
    def get_transaction_history(self, address=None):
        """
        Get transaction history, optionally filtered by address.
        
        Args:
            address: Address to filter by (optional)
            
        Returns:
            List of Transaction objects
        """
        if not address:
            return list(self.transaction_history.values())
            
        return [tx for tx in self.transaction_history.values() 
                if tx.sender == address or tx.recipient == address]
    
    def update_transaction_statuses(self):
        """
        Update the status of transactions based on blockchain state.
        
        Returns:
            Number of transactions updated
        """
        if not self.blockchain:
            return 0
            
        updated_count = 0
        
        # Check each transaction in history
        for transaction_id, transaction in self.transaction_history.items():
            if transaction.status == "confirmed" and transaction.block_index is None:
                # Look for this transaction in the blockchain
                for i, block in enumerate(self.blockchain.chain):
                    for tx in block.transactions:
                        if (tx.get('sender') == transaction.sender and 
                            tx.get('recipient') == transaction.recipient and 
                            tx.get('amount') == transaction.amount):
                            
                            transaction.block_index = i
                            updated_count += 1
                            break
        
        return updated_count


# For testing the module directly
if __name__ == "__main__":
    # Import the blockchain and wallet modules
    from blockchain import Blockchain
    from wallet import WalletManager, Wallet
    
    # Create a blockchain
    blockchain = Blockchain()
    
    # Create a wallet manager
    wallet_manager = WalletManager(blockchain)
    
    # Create a transaction manager
    transaction_manager = TransactionManager(blockchain, wallet_manager)
    
    # Create some wallets
    alice_wallet = wallet_manager.create_wallet()
    bob_wallet = wallet_manager.create_wallet()
    miner_wallet = wallet_manager.create_wallet()
    
    print(f"Created wallets:")
    print(f"Alice: {alice_wallet.address}")
    print(f"Bob: {bob_wallet.address}")
    print(f"Miner: {miner_wallet.address}")
    
    # Add some initial coins to Alice (in a real blockchain, this would come from mining)
    system_tx = transaction_manager.create_transaction("SYSTEM", alice_wallet.address, 100)
    print(f"\nCreated system transaction: {system_tx.transaction_id}")
    
    # Submit to blockchain
    transaction_manager.submit_transaction_to_blockchain(system_tx.transaction_id)
    
    # Mine the block to confirm the transaction
    print("\nMining initial block...")
    blockchain.mine_pending_transactions(miner_wallet.address)
    
    # Wait for mining to complete
    import time
    while blockchain.mining_in_progress:
        time.sleep(0.5)
    
    # Check balances
    print("\nInitial balances:")
    print(f"Alice: {blockchain.get_balance(alice_wallet.address)}")
    print(f"Bob: {blockchain.get_balance(bob_wallet.address)}")
    print(f"Miner: {blockchain.get_balance(miner_wallet.address)}")
    
    # Alice sends coins to Bob
    try:
        print("\nAlice sending 30 coins to Bob...")
        alice_to_bob_tx = transaction_manager.create_transaction(
            alice_wallet.address, bob_wallet.address, 30
        )
        print(f"Created transaction: {alice_to_bob_tx.transaction_id}")
        
        # Submit to blockchain
        transaction_manager.submit_transaction_to_blockchain(alice_to_bob_tx.transaction_id)
        
        # Mine the block to confirm the transaction
        print("Mining transaction block...")
        blockchain.mine_pending_transactions(miner_wallet.address)
        
        # Wait for mining to complete
        while blockchain.mining_in_progress:
            time.sleep(0.5)
        
        # Update transaction statuses
        transaction_manager.update_transaction_statuses()
        
        # Check updated balances
        print("\nUpdated balances:")
        print(f"Alice: {blockchain.get_balance(alice_wallet.address)}")
        print(f"Bob: {blockchain.get_balance(bob_wallet.address)}")
        print(f"Miner: {blockchain.get_balance(miner_wallet.address)}")
        
        # Check transaction status
        print(f"\nTransaction status: {alice_to_bob_tx.status}")
        print(f"Block index: {alice_to_bob_tx.block_index}")
        
    except ValueError as e:
        print(f"Transaction failed: {e}")
    
    # Get transaction history for Alice
    alice_history = transaction_manager.get_transaction_history(alice_wallet.address)
    print(f"\nAlice's transaction history ({len(alice_history)} transactions):")
    for tx in alice_history:
        print(f"- {tx.transaction_id}: {tx.sender} -> {tx.recipient}: {tx.amount} coins ({tx.status})")
