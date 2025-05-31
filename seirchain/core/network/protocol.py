import json
import logging
from seirchain.data_types import Triad, Transaction
from seirchain.config import config

logger = logging.getLogger(__name__)

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
            logger.error(f"Invalid JSON message: {raw_message[:100]}...")
        except KeyError as e:
            logger.error(f"Message missing key: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")

    def handle_transaction(self, tx_data):
        try:
            tx = Transaction(
                transaction_data=tx_data['transaction_data'],
                tx_hash=tx_data['tx_hash'],
                timestamp=tx_data['timestamp']
            )
            # Validate transaction before adding
            if not self.validate_transaction(tx):
                logger.warning(f"Invalid transaction rejected: {tx.tx_hash}")
                return

            # Add to transaction pool
            self.ledger.add_transaction(tx)
            logger.info(f"Transaction added to pool: {tx.tx_hash}")

            # Broadcast to other peers
            self.node.broadcast({
                'type': 'transaction',
                'data': tx_data
            })
        except Exception as e:
            logger.error(f"Transaction handling error: {str(e)}")

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
                logger.info(f"Triad added to ledger: {triad.triad_id}")
                # Broadcast to other peers
                self.node.broadcast({
                    'type': 'triad',
                    'data': triad_data
                })
            else:
                logger.warning(f"Invalid triad rejected: {triad.triad_id}")
        except Exception as e:
            logger.error(f"Triad handling error: {str(e)}")

    def validate_triad(self, triad):
        """Basic triad validation"""
        # 1. Verify hash meets difficulty requirement
        target_prefix = "0" * config.DIFFICULTY
        if not triad.hash_value.startswith(target_prefix):
            logger.debug(f"Triad hash {triad.hash_value} does not meet difficulty {config.DIFFICULTY}")
            return False

        # 2. Verify parent triads exist
        for parent_id in triad.parent_hashes:
            if parent_id not in self.ledger._triad_map:
                logger.debug(f"Parent triad {parent_id} not found for triad {triad.triad_id}")
                return False

        # Additional validation can be added here (e.g., transaction validation)

        return True

    def validate_transaction(self, transaction):
        """Basic transaction validation"""
        # Check for required fields
        required_fields = ['from_addr', 'to_addr', 'amount', 'fee', 'timestamp']
        for field in required_fields:
            if not hasattr(transaction, field):
                logger.debug(f"Transaction missing field: {field}")
                return False

        # Check amount and fee are non-negative
        if transaction.amount <= 0 or transaction.fee < 0:
            logger.debug(f"Transaction amount or fee invalid: amount={transaction.amount}, fee={transaction.fee}")
            return False

        # Check addresses are valid hex strings of length 40 or 64
        if not self._is_valid_address(transaction.from_addr) or not self._is_valid_address(transaction.to_addr):
            logger.debug(f"Transaction has invalid address: from={transaction.from_addr}, to={transaction.to_addr}")
            return False

        # Additional checks like signature verification can be added here

        return True

    def _is_valid_address(self, address):
        if not isinstance(address, str):
            return False
        if len(address) not in (40, 64):
            return False
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
