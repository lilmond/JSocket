import threading
import socket
import json

class JSocketServer(socket.socket):
    _client_socks = []
    _server_sequence = {} # {client_sock: server's messages sequence to the client}

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
    
    def start(self):
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind((self.host, self.port))
        self.listen()

        while True:
            client_sock, client_address = self.accept()
            threading.Thread(target=self._client_handler, args=[client_sock], daemon=True).start()
    
    def _client_handler(self, client_sock: socket.socket):
        self.client_on_connect(client_sock=client_sock)

        try:
            while True:
                full_data = b""

                while True:
                    chunk = client_sock.recv(1)

                    if not chunk:
                        raise Exception("Connection was closed unexpectedly.")
                    
                    full_data += chunk

                    if full_data.endswith(b"\r\n\r\n"):
                        break
                
                self.client_on_message(client_sock=client_sock, message=json.loads(full_data))
        except Exception:
            return
        
        finally:
            self.client_on_close(client_sock=client_sock)
    
    def _ack_message(self, client_sock: socket.socket, message: dict):
        message_sequence = message.get("sequence")

        ack_message = {"op": "ACK_MESSAGE", "sequence": message_sequence}

        self.send_message(client_sock=client_sock, message=ack_message)
    
    def client_on_connect(self, client_sock: socket.socket):
        print(f"Client Connected: {client_sock}")

        self._client_socks.append(client_sock)
        self._server_sequence[client_sock] = 0

    def client_on_close(self, client_sock: socket.socket):
        print(f"Client Closed: {client_sock}")

        self._client_socks.remove(client_sock)
        del self._server_sequence[client_sock]

    def client_on_message(self, client_sock: socket.socket, message: dict):
        print(f"Client Messaged: {client_sock} Message: {message}")

        if not "op" in message:
            self._ack_message(client_sock=client_sock, message=message)
    
    def send_message(self, client_sock: socket.socket, message: dict):
        self._server_sequence[client_sock] += 1
        server_sequence = self._server_sequence[client_sock]

        message["sequence"] = server_sequence

        client_sock.send(json.dumps(message).encode() + b"\r\n\r\n")
    
    def broadcast_message(self, message: dict):
        for client_sock in self._client_socks:
            self.send_message(client_sock=client_sock, message=message)

def main():
    server = JSocketServer("0.0.0.0", 4444)
    threading.Thread(target=server.start, daemon=True).start()

    while True:
        message = input("Message: ")
        message_json = {"message": message}

        server.broadcast_message(message_json)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit()
