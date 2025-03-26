#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive Blockchain Core
--------------------------
This module implements the core blockchain functionality for the interactive
cryptocurrency lab, including blocks, mining, and chain validation.
"""

import hashlib
import time
import json
from datetime import datetime
import threading
import random

class Block:
    """
    A block in the blockchain.
    
    Each block contains:
    - Index: Position in the blockchain
    - Timestamp: When the block was created
    - Transactions: List of transactions included in the block
    - Previous Hash: Hash of the previous block
    - Nonce: Number used for mining (Proof of Work)
    - Hash: The block's own hash
    """
    
    def __init__(self, index, timestamp, transactions, previous_hash):
        """Initialize a new block."""
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        """Calculate the hash of this block."""
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def mine_block(self, difficulty):
        """
        Mine the block by finding a hash with a specific pattern.
        
        Args:
            difficulty: Number of leading zeros required in the hash
        
        Returns:
            The time taken to mine the block in seconds
        """
        target = '0' * difficulty
        start_time = time.time()
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        end_time = time.time()
        mining_time = end_time - start_time
        
        return mining_time
    
    def to_dict(self):
        """Convert block to dictionary for serialization."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, block_dict):
        """Create a Block instance from a dictionary."""
        block = cls(
            block_dict['index'],
            block_dict['timestamp'],
            block_dict['transactions'],
            block_dict['previous_hash']
        )
        block.nonce = block_dict['nonce']
        block.hash = block_dict['hash']
        return block
    
    def __str__(self):
        """String representation of the block."""
        return json.dumps(self.to_dict(), indent=2)


class Blockchain:
    """
    The blockchain implementation.
    
    The blockchain is a chain of blocks, where each block contains
    transactions and is linked to the previous block through its hash.
    """
    
    def __init__(self):
        """Initialize a new blockchain with a genesis block."""
        self.chain = [self.create_genesis_block()]
        self.difficulty = 4  # Mining difficulty (number of leading zeros)
        self.pending_transactions = []
        self.mining_reward = 10  # Reward for mining a block
        self.mining_in_progress = False
        self.mining_thread = None
        self.mining_status = {"status": "idle", "progress": 0, "block_index": None}
    
    def create_genesis_block(self):
        """Create the first block in the blockchain (genesis block)."""
        return Block(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), [], "0")
    
    def get_latest_block(self):
        """Get the most recent block in the blockchain."""
        return self.chain[-1]
    
    def add_transaction(self, sender, recipient, amount, signature=None):
        """
        Add a new transaction to the pending transactions list.
        
        Args:
            sender: Address of the sender
            recipient: Address of the recipient
            amount: Amount to transfer
            signature: Transaction signature (optional for simplicity)
            
        Returns:
            The index of the block that will include this transaction
        """
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'signature': signature
        }
        
        # In a real implementation, we would verify the signature here
        
        self.pending_transactions.append(transaction)
        return self.get_latest_block().index + 1
    
    def mine_pending_transactions(self, mining_reward_address, callback=None):
        """
        Mine pending transactions and add them to a new block.
        
        Args:
            mining_reward_address: Address to receive the mining reward
            callback: Function to call with mining status updates
            
        Returns:
            True if mining started successfully, False if mining is already in progress
        """
        if self.mining_in_progress:
            return False
        
        self.mining_in_progress = True
        self.mining_status = {"status": "starting", "progress": 0, "block_index": self.get_latest_block().index + 1}
        
        # Start mining in a separate thread to avoid blocking
        self.mining_thread = threading.Thread(
            target=self._mine_block_thread,
            args=(mining_reward_address, callback)
        )
        self.mining_thread.daemon = True
        self.mining_thread.start()
        
        return True
    
    def _mine_block_thread(self, mining_reward_address, callback=None):
        """
        Internal method to mine a block in a separate thread.
        
        Args:
            mining_reward_address: Address to receive the mining reward
            callback: Function to call with mining status updates
        """
        try:
            # Create a new block with all pending transactions
            new_block_index = self.get_latest_block().index + 1
            new_block = Block(
                new_block_index,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.pending_transactions.copy(),
                self.get_latest_block().hash
            )
            
            self.mining_status = {"status": "mining", "progress": 10, "block_index": new_block_index}
            if callback:
                callback(self.mining_status)
            
            # Simulate mining progress updates
            def progress_updater():
                progress = 10
                while self.mining_in_progress and progress < 90:
                    time.sleep(0.2)  # Update every 0.2 seconds
                    progress += random.randint(1, 5)
                    progress = min(progress, 90)  # Cap at 90%
                    self.mining_status["progress"] = progress
                    if callback:
                        callback(self.mining_status)
            
            progress_thread = threading.Thread(target=progress_updater)
            progress_thread.daemon = True
            progress_thread.start()
            
            # Mine the block
            mining_time = new_block.mine_block(self.difficulty)
            
            # Add the block to the chain
            self.chain.append(new_block)
            
            # Reset pending transactions and add mining reward transaction
            self.pending_transactions = [{
                'sender': "SYSTEM",
                'recipient': mining_reward_address,
                'amount': self.mining_reward,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'signature': None
            }]
            
            self.mining_status = {
                "status": "completed", 
                "progress": 100, 
                "block_index": new_block_index,
                "mining_time": mining_time,
                "hash": new_block.hash,
                "transactions": len(new_block.transactions)
            }
            
            if callback:
                callback(self.mining_status)
                
        except Exception as e:
            self.mining_status = {
                "status": "failed", 
                "progress": 0, 
                "block_index": new_block_index,
                "error": str(e)
            }
            
            if callback:
                callback(self.mining_status)
        
        finally:
            self.mining_in_progress = False
    
    def get_balance(self, address):
        """
        Calculate the balance of an address by looking at all transactions.
        
        Args:
            address: The address to calculate balance for
            
        Returns:
            The current balance of the address
        """
        balance = 0
        
        # Look through all blocks
        for block in self.chain:
            for transaction in block.transactions:
                if transaction['sender'] == address:
                    balance -= transaction['amount']
                
                if transaction['recipient'] == address:
                    balance += transaction['amount']
        
        # Also check pending transactions
        for transaction in self.pending_transactions:
            if transaction['sender'] == address:
                balance -= transaction['amount']
            
            if transaction['recipient'] == address:
                balance += transaction['amount']
        
        return balance
    
    def get_address_transactions(self, address):
        """
        Get all transactions involving a specific address.
        
        Args:
            address: The address to get transactions for
            
        Returns:
            List of transactions involving the address
        """
        transactions = []
        
        # Look through all blocks
        for block in self.chain:
            for transaction in block.transactions:
                if transaction['sender'] == address or transaction['recipient'] == address:
                    tx_copy = transaction.copy()
                    tx_copy['block'] = block.index
                    tx_copy['confirmed'] = True
                    transactions.append(tx_copy)
        
        # Also check pending transactions
        for transaction in self.pending_transactions:
            if transaction['sender'] == address or transaction['recipient'] == address:
                tx_copy = transaction.copy()
                tx_copy['confirmed'] = False
                transactions.append(tx_copy)
        
        return transactions
    
    def is_chain_valid(self):
        """
        Verify the integrity of the blockchain.
        
        Returns:
            True if the blockchain is valid, False otherwise
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if the current block's hash is valid
            if current_block.hash != current_block.calculate_hash():
                return False
            
            # Check if the current block points to the correct previous hash
            if current_block.previous_hash != previous_block.hash:
                return False
        
        return True
    
    def get_chain_length(self):
        """Get the current length of the blockchain."""
        return len(self.chain)
    
    def get_block(self, index):
        """
        Get a specific block by index.
        
        Args:
            index: The index of the block to retrieve
            
        Returns:
            The block at the specified index or None if not found
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None
    
    def get_mining_status(self):
        """Get the current mining status."""
        return self.mining_status
    
    def to_dict(self):
        """Convert the blockchain to a dictionary for serialization."""
        return {
            'chain': [block.to_dict() for block in self.chain],
            'pending_transactions': self.pending_transactions,
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward
        }
    
    def to_json(self):
        """Convert the blockchain to JSON format."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str):
        """Create a Blockchain instance from a JSON string."""
        data = json.loads(json_str)
        blockchain = cls()
        
        # Clear the default genesis block
        blockchain.chain = []
        
        # Recreate the chain from the JSON data
        for block_dict in data['chain']:
            blockchain.chain.append(Block.from_dict(block_dict))
        
        blockchain.pending_transactions = data['pending_transactions']
        blockchain.difficulty = data['difficulty']
        blockchain.mining_reward = data['mining_reward']
        
        return blockchain
    
    def __str__(self):
        """String representation of the blockchain."""
        return self.to_json()


# For testing the module directly
if __name__ == "__main__":
    # Create a new blockchain
    blockchain = Blockchain()
    print("Blockchain initialized with genesis block.")
    
    # Add some transactions
    blockchain.add_transaction("Alice", "Bob", 50)
    blockchain.add_transaction("Bob", "Charlie", 25)
    print("Added transactions to pending list.")
    
    # Mine the block
    print("Mining block...")
    blockchain.mine_pending_transactions("Miner1")
    
    # Wait for mining to complete
    while blockchain.mining_in_progress:
        time.sleep(0.5)
        print(f"Mining status: {blockchain.get_mining_status()['status']}, "
              f"Progress: {blockchain.get_mining_status()['progress']}%")
    
    print("\nMining completed!")
    print(f"Blockchain length: {blockchain.get_chain_length()}")
    print(f"Latest block hash: {blockchain.get_latest_block().hash}")
    
    # Check balances
    print("\nBalances:")
    print(f"Alice: {blockchain.get_balance('Alice')}")
    print(f"Bob: {blockchain.get_balance('Bob')}")
    print(f"Charlie: {blockchain.get_balance('Charlie')}")
    print(f"Miner1: {blockchain.get_balance('Miner1')}")
    
    # Validate the blockchain
    print(f"\nIs blockchain valid? {blockchain.is_chain_valid()}")
