import socket
import threading
import json
import time
import logging
from seirchain.config import config
from .p2p import P2PManager
from .protocol import MessageHandler

logger = logging.getLogger(__name__)

class Node:
    def __init__(self, host='0.0.0.0', port=None, ledger=None, wallet_manager=None):
        self.host = host
        self.port = port if port is not None else config.P2P_PORT
        self.running = False
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Dependencies
        self.ledger = ledger
        self.wallet_manager = wallet_manager

        # Subsystems
        self.message_handler = MessageHandler(self, ledger, wallet_manager)
        self.p2p_manager = P2PManager(self, self.message_handler)

        # Bootstrap nodes
        self.bootstrap_nodes = [
            ("127.0.0.1", self.port),  # Local node
            # Add production nodes here
        ]


    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            logger.info(f"Node listening on {self.host}:{self.port}")

            # Start connection handler
            accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            accept_thread.start()

            # Start P2P manager
            self.p2p_manager.start()

            # Connect to bootstrap nodes
            self.connect_to_bootstrap_nodes()

        except OSError as e:
            logger.error(f"Failed to start node: {str(e)}")
            self.stop()

    def accept_connections(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                self.p2p_manager.add_peer(client_socket, addr)
            except OSError:
                break

    def connect_to_bootstrap_nodes(self):
        """Connect to predefined bootstrap nodes"""
        for host, port in self.bootstrap_nodes:
            if (host, port) != (self.host, self.port):  # Don't connect to self
                threading.Thread(
                    target=self.connect_to_peer,
                    args=(host, port),
                    daemon=True
                ).start()

    def connect_to_peer(self, host, port):
        """Connect to another peer"""
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((host, port))
            self.p2p_manager.add_peer(peer_socket, (host, port))
            return True
        except (ConnectionRefusedError, socket.gaierror) as e:
            logger.warning(f"Connection to peer {host}:{port} failed: {e}")
            return False

    def broadcast(self, data):
        """Broadcast data to all peers"""
        try:
            if isinstance(data, object) and hasattr(data, '__dict__'):
                message = json.dumps(data.__dict__)
            else:
                message = json.dumps(data)
            self.p2p_manager.broadcast(message)
        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    def stop(self):
        self.running = False
        try:
            self.server_socket.close()
        except Exception as e:
            logger.error(f"Error closing server socket: {e}")
        self.p2p_manager.stop()
        logger.info("Node stopped")

    def __repr__(self):
        return f"<Node {self.host}:{self.port}>"
