import json
from seirchain.data_types import Triad, Transaction

class MessageHandler:
    def __init__(self, node, ledger, wallet_manager):
        self.node = node
        self.ledger = ledger
        self.wallet_manager = wallet_manager

    def handle_message(self, raw_message, peer_socket):
        try:
            message = json.loads(raw_message)
            msg_type = message.get('type')

            if msg_type == 'transaction':
                self.handle_transaction(message['data'])
            elif msg_type == 'triad':
                self.handle_triad(message['data'])
            elif msg_type == 'ping':
                peer_socket.sendall(json.dumps({'type': 'pong'}).encode() + b'\n')

        except json.JSONDecodeError:
            print(f"Invalid JSON message: {raw_message[:100]}...")
        except KeyError as e:
            print(f"Message missing key: {str(e)}")

    def handle_transaction(self, tx_data):
        try:
            tx = Transaction(
                transaction_data=tx_data['transaction_data'],
                tx_hash=tx_data['tx_hash'],
                timestamp=tx_data['timestamp']
            )
            # Add to transaction pool
            self.ledger.add_transaction(tx)
            # Broadcast to other peers
            self.node.broadcast({
                'type': 'transaction',
                'data': tx_data
            })
        except Exception as e:
            print(f"Transaction handling error: {str(e)}")

    def handle_triad(self, triad_data):
        try:
            triad = Triad(
                triad_id=triad_data['triad_id'],
                depth=triad_data['depth'],
                hash_value=triad_data['hash_value'],
                parent_hashes=triad_data['parent_hashes']
            )
            # Add to ledger if valid
            if self.validate_triad(triad):
                self.ledger.add_triad(triad)
                # Broadcast to other peers
                self.node.broadcast({
                    'type': 'triad',
                    'data': triad_data
                })
        except Exception as e:
            print(f"Triad handling error: {str(e)}")

    def validate_triad(self, triad):
        """Basic triad validation"""
        # 1. Verify hash meets difficulty requirement
        if not triad.hash_value.startswith("00000"):
            return False

        # 2. Verify parent triads exist
        for parent_id in triad.parent_hashes:
            if not any(t.triad_id == parent_id for t in self.ledger.triads):
                return False

        return True
