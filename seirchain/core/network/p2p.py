import threading
import time

class P2PManager:
    def __init__(self, node, message_handler):
        self.node = node
        self.message_handler = message_handler
        self.peer_sockets = {}
        self.receive_threads = {}
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
        for peer_socket in list(self.peer_sockets.values()):
            try:
                peer_socket.close()
            except:
                pass
        self.peer_sockets = {}
        self.receive_threads = {}

    def add_peer(self, peer_socket, addr):
        """Add a new peer connection"""
        peer_id = f"{addr[0]}:{addr[1]}"
        if peer_id in self.peer_sockets:
            return

        self.peer_sockets[peer_id] = peer_socket
        thread = threading.Thread(
            target=self.listen_to_peer,
            args=(peer_socket,),
            daemon=True,
            name=f"P2P-{peer_id}"
        )
        thread.start()
        self.receive_threads[peer_id] = thread
        print(f"Added peer: {peer_id}")

    def listen_to_peer(self, peer_socket):
        """Listen for messages from a peer"""
        buffer = b''
        while self.running:
            try:
                data = peer_socket.recv(4096)
                if not data:
                    break

                buffer += data
                while b'\n' in buffer:
                    raw_message, buffer = buffer.split(b'\n', 1)
                    self.message_handler.handle_message(
                        raw_message.decode().strip(),
                        peer_socket
                    )
            except (ConnectionResetError, OSError):
                break

        self.remove_peer(peer_socket)

    def remove_peer(self, peer_socket):
        """Remove a disconnected peer"""
        for peer_id, sock in list(self.peer_sockets.items()):
            if sock == peer_socket:
                del self.peer_sockets[peer_id]
                del self.receive_threads[peer_id]
                try:
                    peer_socket.close()
                except:
                    pass
                print(f"Peer disconnected: {peer_id}")
                break

    def send_to_peer(self, peer_socket, message):
        """Send a message to a specific peer"""
        try:
            peer_socket.sendall((message + '\n').encode())
        except (BrokenPipeError, ConnectionResetError, OSError):
            self.remove_peer(peer_socket)

    def broadcast(self, message):
        """Broadcast a message to all connected peers"""
        for peer_socket in list(self.peer_sockets.values()):
            self.send_to_peer(peer_socket, message)
