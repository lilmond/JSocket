import threading
import socket
import json

class JSocketClient(socket.socket):
    _message_sequence = 0

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
    
    def start(self):
        self.connect((self.host, self.port))
        self._handler()
    
    def _handler(self):
        self.on_connect()

        try:
            while True:
                full_data = b""

                while True:
                    chunk = super().recv(1)

                    if not chunk:
                        raise Exception("Connection was closed unexpectedly.")
                    
                    full_data += chunk

                    if full_data.endswith(b"\r\n\r\n"):
                        break
                
                self.on_message(json.loads(full_data))
        except Exception:
            return
        finally:
            self.on_close()
        
    def _ack_message(self, message: dict):
        message_sequence = message.get("sequence")

        ack_message = {"op": "ACK_MESSAGE", "sequence": message_sequence}

        self.send_message(message=ack_message)

    def on_connect(self):
        print(f"Connected to the server.")

    def on_close(self):
        print(f"Disconnected from the server.")

    def on_message(self, message):
        print(f"Message from the server:\n{message}")

        if not "op" in message:
            self._ack_message(message=message)

    def send_message(self, message: dict):
        self._message_sequence += 1

        message["sequence"] = self._message_sequence

        self.send(json.dumps(message).encode() + b"\r\n\r\n")

def main():
    client = JSocketClient("127.0.0.1", 4444)
    threading.Thread(target=client.start, daemon=True).start()

    while True:
        message = input("Message: ")
        message_json = {"message": message}

        client.send_message(message_json)

if __name__ == "__main__":
    main()
