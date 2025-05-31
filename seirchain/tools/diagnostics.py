import time
import psutil
import os
from datetime import datetime

def system_health_report(ledger, miner, node, wallet_manager):
    """Generate comprehensive system diagnostics"""
    # Get system resources
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    net = psutil.net_io_counters()
    process = psutil.Process(os.getpid())
    
    # Ledger metrics
    triad_count = len(ledger.triads) if hasattr(ledger, 'triads') else 0
    tx_pool_size = len(ledger.transaction_pool) if hasattr(ledger, 'transaction_pool') else 0
    max_depth = max(t.depth for t in ledger.triads) if triad_count > 0 else 0
    
    # Node metrics
    peer_count = len(node.peers) if hasattr(node, 'peers') else 0
    node_status = "running" if node.running else "stopped"
    
    # Miner metrics
    miner_status = "running" if miner.mining else "stopped"
    miner_threads = len(miner.threads) if hasattr(miner, 'threads') else 0
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_usage": f"{cpu}%",
            "memory_used": f"{mem.used / (1024**3):.2f} GB",
            "memory_available": f"{mem.available / (1024**3):.2f} GB",
            "disk_used": f"{disk.used / (1024**3):.2f} GB",
            "disk_free": f"{disk.free / (1024**3):.2f} GB",
            "network_sent": f"{net.bytes_sent / (1024**2):.2f} MB",
            "network_received": f"{net.bytes_recv / (1024**2):.2f} MB",
            "process_memory": f"{process.memory_info().rss / (1024**2):.2f} MB"
        },
        "ledger": {
            "triad_count": triad_count,
            "transaction_pool_size": tx_pool_size,
            "max_depth": max_depth,
            "genesis_triad": ledger.triads[0].triad_id[:12] + "..." if triad_count > 0 else "None"
        },
        "miner": {
            "status": miner_status,
            "active_threads": miner_threads,
            "last_triad_mined": miner.last_mined_triad[:12] + "..." if hasattr(miner, 'last_mined_triad') else "None"
        },
        "node": {
            "status": node_status,
            "peer_count": peer_count,
            "listen_address": f"{node.host}:{node.port}"
        },
        "wallets": {
            "total_wallets": len(wallet_manager.wallets),
            "genesis_balance": wallet_manager.get_wallet("0"*40).balance
        }
    }

def fractal_integrity_check(ledger):
    """Verify the mathematical integrity of the Triad Matrix"""
    if not hasattr(ledger, 'triads') or len(ledger.triads) == 0:
        return False
        
    # Validate genesis triad
    genesis = ledger.triads[0]
    if genesis.depth != 0 or genesis.parent_hashes:
        return False
        
    # Validate subsequent triads
    for triad in ledger.triads[1:]:
        if triad.depth <= 0:
            return False
        if len(triad.parent_hashes) != 3:  # Must have 3 parents in fractal structure
            return False
            
        # Validate parent references exist
        for parent_hash in triad.parent_hashes:
            if not any(t.hash == parent_hash for t in ledger.triads):
                return False
                
    return True

def save_report(report, filename="diagnostics_report.json"):
    """Save diagnostics report to file"""
    import json
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    return f"Report saved to {filename}"
