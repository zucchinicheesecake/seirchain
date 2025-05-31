import unittest
from unittest.mock import MagicMock, patch
from seirchain.network.node import Node

class TestNode(unittest.TestCase):
    def setUp(self):
        self.node = Node(host='127.0.0.1', port=0)

    @patch('socket.socket')
    def test_start_and_stop(self, mock_socket):
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        self.node.start()
        self.assertTrue(self.node.running)
        self.node.stop()
        self.assertFalse(self.node.running)
        mock_socket_instance.close.assert_called()

    def test_broadcast(self):
        self.node.p2p_manager = MagicMock()
        data = {'key': 'value'}
        self.node.broadcast(data)
        self.node.p2p_manager.broadcast.assert_called()

    def test_connect_to_peer_failure(self):
        result = self.node.connect_to_peer('invalid_host', 12345)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
