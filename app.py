#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Interactive Cryptocurrency Lab - Web Interface
--------------------------------------------
This module provides a web-based user interface for interacting with
the cryptocurrency lab components.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
import time
from datetime import datetime
import threading

# Import our cryptocurrency modules
from blockchain import Blockchain, Block
from wallet import Wallet, WalletManager
from transaction import Transaction, TransactionManager

# Initialize Flask app
app = Flask(__name__)

# Create application state
blockchain = Blockchain()
wallet_manager = WalletManager(blockchain)
transaction_manager = TransactionManager(blockchain, wallet_manager)

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Load existing wallets if available
try:
    wallet_manager.load_wallets('data/wallets.json')
except:
    # Create a default miner wallet if no wallets exist
    if not wallet_manager.list_wallets():
        miner_wallet = wallet_manager.create_wallet()
        print(f"Created default miner wallet: {miner_wallet.address}")
        wallet_manager.save_wallets('data/wallets.json')

# Routes
@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('index.html', 
                          blockchain_length=blockchain.get_chain_length(),
                          pending_transactions=len(blockchain.pending_transactions),
                          wallets=wallet_manager.list_wallets(),
                          mining_status=blockchain.get_mining_status())

@app.route('/blockchain')
def view_blockchain():
    """View the entire blockchain."""
    return render_template('blockchain.html', 
                          blockchain=blockchain,
                          blocks=[block.to_dict() for block in blockchain.chain])

@app.route('/block/<int:index>')
def view_block(index):
    """View a specific block."""
    block = blockchain.get_block(index)
    if block:
        return render_template('block.html', block=block.to_dict())
    return "Block not found", 404

@app.route('/wallets')
def view_wallets():
    """View all wallets."""
    wallet_data = []
    for address in wallet_manager.list_wallets():
        wallet = wallet_manager.get_wallet(address)
        wallet_data.append({
            'address': wallet.address,
            'balance': blockchain.get_balance(wallet.address)
        })
    return render_template('wallets.html', wallets=wallet_data)

@app.route('/wallet/<address>')
def view_wallet(address):
    """View a specific wallet."""
    wallet = wallet_manager.get_wallet(address)
    if wallet:
        transactions = transaction_manager.get_transaction_history(address)
        return render_template('wallet.html', 
                              wallet={'address': wallet.address, 
                                     'balance': blockchain.get_balance(wallet.address)},
                              transactions=[tx.to_dict() for tx in transactions])
    return "Wallet not found", 404

@app.route('/create_wallet', methods=['GET', 'POST'])
def create_wallet():
    """Create a new wallet."""
    if request.method == 'POST':
        wallet = wallet_manager.create_wallet()
        wallet_manager.save_wallets('data/wallets.json')
        return redirect(url_for('view_wallet', address=wallet.address))
    return render_template('create_wallet.html')

@app.route('/transactions')
def view_transactions():
    """View all transactions."""
    pending = transaction_manager.get_pending_transactions()
    history = transaction_manager.get_transaction_history()
    return render_template('transactions.html', 
                          pending=[tx.to_dict() for tx in pending],
                          history=[tx.to_dict() for tx in history])

@app.route('/create_transaction', methods=['GET', 'POST'])
def create_transaction():
    """Create a new transaction."""
    if request.method == 'POST':
        sender = request.form.get('sender')
        recipient = request.form.get('recipient')
        amount = float(request.form.get('amount'))
        
        try:
            transaction = transaction_manager.create_transaction(sender, recipient, amount)
            transaction_manager.submit_transaction_to_blockchain(transaction.transaction_id)
            return redirect(url_for('view_transactions'))
        except ValueError as e:
            return render_template('create_transaction.html', 
                                  wallets=wallet_manager.list_wallets(),
                                  error=str(e))
    
    return render_template('create_transaction.html', 
                          wallets=wallet_manager.list_wallets())

@app.route('/mine', methods=['GET', 'POST'])
def mine_block():
    """Mine a new block."""
    if request.method == 'POST':
        miner_address = request.form.get('miner_address')
        if blockchain.mining_in_progress:
            return render_template('mine.html', 
                                  wallets=wallet_manager.list_wallets(),
                                  error="Mining already in progress")
        
        blockchain.mine_pending_transactions(miner_address)
        return redirect(url_for('mining_status'))
    
    return render_template('mine.html', wallets=wallet_manager.list_wallets())

@app.route('/mining_status')
def mining_status():
    """View mining status."""
    return render_template('mining_status.html', status=blockchain.get_mining_status())

# API endpoints for AJAX updates
@app.route('/api/mining_status')
def api_mining_status():
    """Get current mining status as JSON."""
    return jsonify(blockchain.get_mining_status())

@app.route('/api/blockchain_info')
def api_blockchain_info():
    """Get blockchain info as JSON."""
    return jsonify({
        'length': blockchain.get_chain_length(),
        'pending_transactions': len(blockchain.pending_transactions),
        'is_valid': blockchain.is_chain_valid()
    })

@app.route('/api/wallet_balances')
def api_wallet_balances():
    """Get all wallet balances as JSON."""
    balances = {}
    for address in wallet_manager.list_wallets():
        balances[address] = blockchain.get_balance(address)
    return jsonify(balances)

# Create HTML templates
def create_templates():
    """Create HTML templates for the web interface."""
    os.makedirs('templates', exist_ok=True)
    
    # Base template
    with open('templates/base.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Interactive Cryptocurrency Lab{% endblock %}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { padding-top: 20px; }
        .blockchain-block { 
            border: 1px solid #ddd; 
            padding: 10px; 
            margin-bottom: 10px; 
            border-radius: 5px;
        }
        .transaction { 
            border: 1px solid #eee; 
            padding: 8px; 
            margin-bottom: 5px; 
            border-radius: 3px;
        }
        .pending { background-color: #fff3cd; }
        .confirmed { background-color: #d1e7dd; }
        .rejected { background-color: #f8d7da; }
        .monospace { font-family: monospace; }
        .hash { word-break: break-all; }
    </style>
    {% block head %}{% endblock %}
</head>
<body>
    <div class="container">
        <header class="mb-4">
            <nav class="navbar navbar-expand-lg navbar-light bg-light">
                <div class="container-fluid">
                    <a class="navbar-brand" href="/">Crypto Lab</a>
                    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                        <span class="navbar-toggler-icon"></span>
                    </button>
                    <div class="collapse navbar-collapse" id="navbarNav">
                        <ul class="navbar-nav">
                            <li class="nav-item">
                                <a class="nav-link" href="/">Dashboard</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/blockchain">Blockchain</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/wallets">Wallets</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/transactions">Transactions</a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link" href="/mine">Mine</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
        </header>
        
        <main>
            {% block content %}{% endblock %}
        </main>
        
        <footer class="mt-5 pt-3 border-top text-center text-muted">
            <p>Interactive Cryptocurrency Lab &copy; 2025</p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>''')
    
    # Index template
    with open('templates/index.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Dashboard - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Cryptocurrency Lab Dashboard</h1>
        
        <div class="row">
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header">Blockchain Status</div>
                    <div class="card-body">
                        <p><strong>Chain Length:</strong> <span id="chain-length">{{ blockchain_length }}</span></p>
                        <p><strong>Pending Transactions:</strong> <span id="pending-tx">{{ pending_transactions }}</span></p>
                        <p><strong>Mining Status:</strong> <span id="mining-status">{{ mining_status.status }}</span></p>
                        <div class="progress mb-3" id="mining-progress-container" style="display: {% if mining_status.status == 'mining' %}block{% else %}none{% endif %}">
                            <div id="mining-progress" class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: {{ mining_status.progress }}%"></div>
                        </div>
                        <a href="/blockchain" class="btn btn-primary">View Blockchain</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header">Wallets</div>
                    <div class="card-body">
                        <p><strong>Total Wallets:</strong> {{ wallets|length }}</p>
                        <div class="list-group mb-3">
                            {% for address in wallets[:3] %}
                            <a href="/wallet/{{ address }}" class="list-group-item list-group-item-action">
                                <div class="d-flex justify-content-between">
                                    <div class="monospace text-truncate" style="max-width: 180px;">{{ address }}</div>
                                    <span id="balance-{{ address[:8] }}">...</span>
                                </div>
                            </a>
                            {% endfor %}
                        </div>
                        <div class="d-flex justify-content-between">
                            <a href="/wallets" class="btn btn-primary">View All Wallets</a>
                            <a href="/create_wallet" class="btn btn-success">Create Wallet</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header">Transactions</div>
                    <div class="card-body">
                        <p><strong>Pending Transactions:</strong> <span id="pending-tx2">{{ pending_transactions }}</span></p>
                        <div class="d-flex justify-content-between">
                            <a href="/transactions" class="btn btn-primary">View Transactions</a>
                            <a href="/create_transaction" class="btn btn-success">Create Transaction</a>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">Mining</div>
                    <div class="card-body">
                        <p>Mine a new block to confirm pending transactions.</p>
                        <a href="/mine" class="btn btn-warning">Mine Block</a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Update dashboard data every 2 seconds
    function updateDashboard() {
        // Update mining status
        fetch('/api/mining_status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('mining-status').textContent = data.status;
                
                // Update progress bar
                if (data.status === 'mining') {
                    document.getElementById('mining-progress-container').style.display = 'block';
                    document.getElementById('mining-progress').style.width = data.progress + '%';
                } else {
                    document.getElementById('mining-progress-container').style.display = 'none';
                }
            });
        
        // Update blockchain info
        fetch('/api/blockchain_info')
            .then(response => response.json())
            .then(data => {
                document.getElementById('chain-length').textContent = data.length;
                document.getElementById('pending-tx').textContent = data.pending_transactions;
                document.getElementById('pending-tx2').textContent = data.pending_transactions;
            });
        
        // Update wallet balances
        fetch('/api/wallet_balances')
            .then(response => response.json())
            .then(data => {
                for (const [address, balance] of Object.entries(data)) {
                    const balanceElement = document.getElementById('balance-' + address.substring(0, 8));
                    if (balanceElement) {
                        balanceElement.textContent = balance;
                    }
                }
            });
    }
    
    // Update immediately and then every 2 seconds
    updateDashboard();
    setInterval(updateDashboard, 2000);
</script>
{% endblock %}''')
    
    # Blockchain template
    with open('templates/blockchain.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Blockchain - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Blockchain Explorer</h1>
        
        <div class="alert alert-info">
            <p><strong>Chain Length:</strong> {{ blockchain.get_chain_length() }}</p>
            <p><strong>Is Valid:</strong> {{ "Yes" if blockchain.is_chain_valid() else "No" }}</p>
            <p><strong>Mining Difficulty:</strong> {{ blockchain.difficulty }} ({{ blockchain.difficulty }} leading zeros)</p>
        </div>
        
        <h2 class="mb-3">Blocks</h2>
        
        {% for block in blocks|reverse %}
        <div class="blockchain-block">
            <div class="row">
                <div class="col-md-6">
                    <h4>Block #{{ block.index }}</h4>
                    <p><strong>Timestamp:</strong> {{ block.timestamp }}</p>
                    <p><strong>Transactions:</strong> {{ block.transactions|length }}</p>
                    <p><strong>Nonce:</strong> {{ block.nonce }}</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Hash:</strong> <span class="hash">{{ block.hash }}</span></p>
                    <p><strong>Previous Hash:</strong> <span class="hash">{{ block.previous_hash }}</span></p>
                    <a href="/block/{{ block.index }}" class="btn btn-sm btn-primary">View Details</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}''')
    
    # Block template
    with open('templates/block.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Block #{{ block.index }} - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Block #{{ block.index }}</h1>
        
        <div class="card mb-4">
            <div class="card-header">Block Details</div>
            <div class="card-body">
                <p><strong>Timestamp:</strong> {{ block.timestamp }}</p>
                <p><strong>Hash:</strong> <span class="hash">{{ block.hash }}</span></p>
                <p><strong>Previous Hash:</strong> <span class="hash">{{ block.previous_hash }}</span></p>
                <p><strong>Nonce:</strong> {{ block.nonce }}</p>
            </div>
        </div>
        
        <h2 class="mb-3">Transactions ({{ block.transactions|length }})</h2>
        
        {% if block.transactions %}
            {% for tx in block.transactions %}
            <div class="transaction confirmed">
                <div class="row">
                    <div class="col-md-12">
                        <p>
                            <strong>From:</strong> 
                            {% if tx.sender == "SYSTEM" %}
                                <span class="badge bg-info">SYSTEM</span>
                            {% else %}
                                <a href="/wallet/{{ tx.sender }}" class="monospace">{{ tx.sender }}</a>
                            {% endif %}
                        </p>
                        <p>
                            <strong>To:</strong> 
                            <a href="/wallet/{{ tx.recipient }}" class="monospace">{{ tx.recipient }}</a>
                        </p>
                        <p><strong>Amount:</strong> {{ tx.amount }}</p>
                        <p><strong>Timestamp:</strong> {{ tx.timestamp }}</p>
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="alert alert-info">No transactions in this block.</div>
        {% endif %}
        
        <div class="mt-3">
            <a href="/blockchain" class="btn btn-primary">Back to Blockchain</a>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Wallets template
    with open('templates/wallets.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Wallets - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Wallets</h1>
            <a href="/create_wallet" class="btn btn-success">Create New Wallet</a>
        </div>
        
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Address</th>
                        <th>Balance</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for wallet in wallets %}
                    <tr>
                        <td class="monospace">{{ wallet.address }}</td>
                        <td>{{ wallet.balance }}</td>
                        <td>
                            <a href="/wallet/{{ wallet.address }}" class="btn btn-sm btn-primary">View</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Wallet template
    with open('templates/wallet.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Wallet Details - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1 class="mb-4">Wallet Details</h1>
        
        <div class="card mb-4">
            <div class="card-header">Wallet Information</div>
            <div class="card-body">
                <p><strong>Address:</strong> <span class="monospace">{{ wallet.address }}</span></p>
                <p><strong>Balance:</strong> {{ wallet.balance }}</p>
                <div class="d-flex gap-2">
                    <a href="/create_transaction?sender={{ wallet.address }}" class="btn btn-primary">Send Coins</a>
                    <a href="/mine?miner={{ wallet.address }}" class="btn btn-warning">Mine as this Wallet</a>
                </div>
            </div>
        </div>
        
        <h2 class="mb-3">Transaction History</h2>
        
        {% if transactions %}
            {% for tx in transactions %}
            <div class="transaction {{ tx.status }}">
                <div class="row">
                    <div class="col-md-8">
                        {% if tx.sender == wallet.address %}
                            <p><strong>Sent to:</strong> <a href="/wallet/{{ tx.recipient }}" class="monospace">{{ tx.recipient }}</a></p>
                            <p><strong>Amount:</strong> -{{ tx.amount }}</p>
                        {% else %}
                            <p>
                                <strong>Received from:</strong> 
                                {% if tx.sender == "SYSTEM" %}
                                    <span class="badge bg-info">SYSTEM</span>
                                {% else %}
                                    <a href="/wallet/{{ tx.sender }}" class="monospace">{{ tx.sender }}</a>
                                {% endif %}
                            </p>
                            <p><strong>Amount:</strong> +{{ tx.amount }}</p>
                        {% endif %}
                    </div>
                    <div class="col-md-4 text-end">
                        <p><strong>Status:</strong> <span class="badge bg-{{ 'success' if tx.status == 'confirmed' else 'warning' if tx.status == 'pending' else 'danger' }}">{{ tx.status }}</span></p>
                        <p><strong>Timestamp:</strong> {{ tx.timestamp }}</p>
                        {% if tx.block_index is not none %}
                            <p><strong>Block:</strong> <a href="/block/{{ tx.block_index }}">#{{ tx.block_index }}</a></p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="alert alert-info">No transactions for this wallet.</div>
        {% endif %}
        
        <div class="mt-3">
            <a href="/wallets" class="btn btn-primary">Back to Wallets</a>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Create Wallet template
    with open('templates/create_wallet.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Create Wallet - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 offset-md-2">
        <h1 class="mb-4">Create New Wallet</h1>
        
        <div class="card">
            <div class="card-body">
                <p class="mb-4">Click the button below to generate a new wallet with a unique address.</p>
                
                <form method="post">
                    <button type="submit" class="btn btn-success">Generate New Wallet</button>
                    <a href="/wallets" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Transactions template
    with open('templates/transactions.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Transactions - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Transactions</h1>
            <a href="/create_transaction" class="btn btn-success">Create New Transaction</a>
        </div>
        
        <h2 class="mb-3">Pending Transactions</h2>
        
        {% if pending %}
            {% for tx in pending %}
            <div class="transaction pending">
                <div class="row">
                    <div class="col-md-8">
                        <p>
                            <strong>From:</strong> 
                            {% if tx.sender == "SYSTEM" %}
                                <span class="badge bg-info">SYSTEM</span>
                            {% else %}
                                <a href="/wallet/{{ tx.sender }}" class="monospace">{{ tx.sender }}</a>
                            {% endif %}
                        </p>
                        <p><strong>To:</strong> <a href="/wallet/{{ tx.recipient }}" class="monospace">{{ tx.recipient }}</a></p>
                        <p><strong>Amount:</strong> {{ tx.amount }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <p><strong>Status:</strong> <span class="badge bg-warning">Pending</span></p>
                        <p><strong>Timestamp:</strong> {{ tx.timestamp }}</p>
                    </div>
                </div>
            </div>
            {% endfor %}
            
            <div class="mt-3 mb-5">
                <a href="/mine" class="btn btn-warning">Mine These Transactions</a>
            </div>
        {% else %}
            <div class="alert alert-info mb-5">No pending transactions.</div>
        {% endif %}
        
        <h2 class="mb-3">Transaction History</h2>
        
        {% if history %}
            {% for tx in history %}
            <div class="transaction {{ tx.status }}">
                <div class="row">
                    <div class="col-md-8">
                        <p>
                            <strong>From:</strong> 
                            {% if tx.sender == "SYSTEM" %}
                                <span class="badge bg-info">SYSTEM</span>
                            {% else %}
                                <a href="/wallet/{{ tx.sender }}" class="monospace">{{ tx.sender }}</a>
                            {% endif %}
                        </p>
                        <p><strong>To:</strong> <a href="/wallet/{{ tx.recipient }}" class="monospace">{{ tx.recipient }}</a></p>
                        <p><strong>Amount:</strong> {{ tx.amount }}</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <p><strong>Status:</strong> <span class="badge bg-{{ 'success' if tx.status == 'confirmed' else 'warning' if tx.status == 'pending' else 'danger' }}">{{ tx.status }}</span></p>
                        <p><strong>Timestamp:</strong> {{ tx.timestamp }}</p>
                        {% if tx.block_index is not none %}
                            <p><strong>Block:</strong> <a href="/block/{{ tx.block_index }}">#{{ tx.block_index }}</a></p>
                        {% endif %}
                    </div>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <div class="alert alert-info">No transaction history.</div>
        {% endif %}
    </div>
</div>
{% endblock %}''')
    
    # Create Transaction template
    with open('templates/create_transaction.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Create Transaction - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 offset-md-2">
        <h1 class="mb-4">Create New Transaction</h1>
        
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        
        <div class="card">
            <div class="card-body">
                <form method="post">
                    <div class="mb-3">
                        <label for="sender" class="form-label">From (Sender)</label>
                        <select class="form-select" id="sender" name="sender" required>
                            <option value="" disabled {% if not request.args.get('sender') %}selected{% endif %}>Select a wallet</option>
                            {% for address in wallets %}
                            <option value="{{ address }}" {% if request.args.get('sender') == address %}selected{% endif %}>{{ address }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="recipient" class="form-label">To (Recipient)</label>
                        <select class="form-select" id="recipient" name="recipient" required>
                            <option value="" disabled selected>Select a wallet</option>
                            {% for address in wallets %}
                            <option value="{{ address }}">{{ address }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label for="amount" class="form-label">Amount</label>
                        <input type="number" class="form-control" id="amount" name="amount" min="0.1" step="0.1" required>
                    </div>
                    
                    <div class="d-flex justify-content-between">
                        <button type="submit" class="btn btn-success">Create Transaction</button>
                        <a href="/transactions" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Mine template
    with open('templates/mine.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Mine Block - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 offset-md-2">
        <h1 class="mb-4">Mine a New Block</h1>
        
        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}
        
        <div class="card">
            <div class="card-body">
                <p>Mining a block will confirm all pending transactions and reward the miner with newly created coins.</p>
                
                <form method="post">
                    <div class="mb-3">
                        <label for="miner_address" class="form-label">Miner Wallet (to receive rewards)</label>
                        <select class="form-select" id="miner_address" name="miner_address" required>
                            <option value="" disabled {% if not request.args.get('miner') %}selected{% endif %}>Select a wallet</option>
                            {% for address in wallets %}
                            <option value="{{ address }}" {% if request.args.get('miner') == address %}selected{% endif %}>{{ address }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <div class="d-flex justify-content-between">
                        <button type="submit" class="btn btn-warning">Start Mining</button>
                        <a href="/" class="btn btn-secondary">Cancel</a>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}''')
    
    # Mining Status template
    with open('templates/mining_status.html', 'w') as f:
        f.write('''{% extends "base.html" %}

{% block title %}Mining Status - Cryptocurrency Lab{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 offset-md-2">
        <h1 class="mb-4">Mining Status</h1>
        
        <div class="card">
            <div class="card-header">Mining Progress</div>
            <div class="card-body">
                <p><strong>Status:</strong> <span id="status">{{ status.status }}</span></p>
                <p><strong>Block:</strong> <span id="block-index">{{ status.block_index }}</span></p>
                
                <div class="progress mb-3">
                    <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
                         role="progressbar" style="width: {{ status.progress }}%"></div>
                </div>
                
                <div id="mining-details" style="display: {% if status.status == 'completed' %}block{% else %}none{% endif %}">
                    <p><strong>Mining Time:</strong> <span id="mining-time">{{ status.mining_time|default('N/A') }}</span> seconds</p>
                    <p><strong>Block Hash:</strong> <span id="block-hash" class="hash">{{ status.hash|default('N/A') }}</span></p>
                    <p><strong>Transactions:</strong> <span id="tx-count">{{ status.transactions|default('N/A') }}</span></p>
                </div>
                
                <div class="mt-3">
                    <a id="view-block-btn" href="/block/{{ status.block_index }}" class="btn btn-primary" style="display: {% if status.status == 'completed' %}inline-block{% else %}none{% endif %}">View Block</a>
                    <a href="/" class="btn btn-secondary">Back to Dashboard</a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
    // Update mining status every second
    function updateMiningStatus() {
        fetch('/api/mining_status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').textContent = data.status;
                document.getElementById('block-index').textContent = data.block_index;
                document.getElementById('progress-bar').style.width = data.progress + '%';
                
                if (data.status === 'completed') {
                    document.getElementById('mining-details').style.display = 'block';
                    document.getElementById('mining-time').textContent = data.mining_time.toFixed(2);
                    document.getElementById('block-hash').textContent = data.hash;
                    document.getElementById('tx-count').textContent = data.transactions;
                    
                    const viewBlockBtn = document.getElementById('view-block-btn');
                    viewBlockBtn.href = '/block/' + data.block_index;
                    viewBlockBtn.style.display = 'inline-block';
                    
                    // Stop updating if mining is complete
                    clearInterval(updateInterval);
                }
            });
    }
    
    // Update immediately and then every second
    updateMiningStatus();
    const updateInterval = setInterval(updateMiningStatus, 1000);
</script>
{% endblock %}''')

# Main function to run the app
if __name__ == "__main__":
    # Create templates
    create_templates()
    
    # Create a genesis block with initial coins for testing
    if blockchain.get_chain_length() == 1 and not blockchain.pending_transactions:
        # Create a test wallet if none exist
        if not wallet_manager.list_wallets():
            test_wallet = wallet_manager.create_wallet()
            print(f"Created test wallet: {test_wallet.address}")
            wallet_manager.save_wallets('data/wallets.json')
        
        # Add some initial coins to the first wallet
        first_wallet = wallet_manager.get_wallet(wallet_manager.list_wallets()[0])
        blockchain.add_transaction("SYSTEM", first_wallet.address, 100)
        
        # Mine the genesis block
        blockchain.mine_pending_transactions(first_wallet.address)
        print("Created genesis block with initial coins")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
