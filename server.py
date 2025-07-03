import socket
import threading
import time
from protocols import Protocol
from database import Database
import logging
import os

class Server:
    # Initialize server class
    def __init__(self, host='0.0.0.0', port=12345):
        # Setup connection
        self.host = host # listen from all ports
        self.port = port

        # Setup server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Setup clients manager
        self.clients = {}  # {client_socket: user_id}

        # Setup running state
        self.running = True

        # Setup database
        self.database = Database()

        # Setup thread locks (prevent race condition)
        self.lock = threading.Lock()

        # Setup logger
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Setup folder for receiving files
        os.makedirs('files', exist_ok=True)
        

    # Start server
    def start(self):
        try:
            # Bind server to given host and port | Listen to all incoming requests
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.logger.info(f"Server started on {self.host}:{self.port}")

            while self.running:
                self.server_socket.settimeout(1.0)  # Allow periodic check for shutdown

                try:
                    # Accept incoming client requests and fetch client data
                    client_socket, addr = self.server_socket.accept()
                    self.logger.info(f"New connection from {addr}")

                    # Create and start client thread
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    client_thread.daemon = True
                    client_thread.start()

                except socket.timeout:
                    continue

                except Exception as e:
                    self.logger.error(f"Error accepting connection: {e}")

        except Exception as e:
            self.logger.error(f"Server error: {e}")

        finally:
            self.stop()

    # Shut server down
    def stop(self):
        # Set running state to False
        self.running = False

        with self.lock:
            for client_socket in self.clients:
                try:
                    client_socket.close() # close client socket

                except Exception as e:
                    self.logger.error(f"Error closing client socket: {e}")

            self.clients.clear() # clear client handler

        # Close server socket
        self.server_socket.close()
        self.database.close()
        self.logger.info("Server stopped")

    # Client handling logic
    def handle_client(self, client_socket, addr):
        try:
            while self.running:
                # Set timeout to avoid premature disconnection
                client_socket.settimeout(10.0)
                try:
                    message = Protocol.decode_message(client_socket, use_timeout=True)
                    if message is None:
                        # Check if socket is closed by client
                        try:
                            data = client_socket.recv(1, socket.MSG_PEEK)

                            if not data:
                                self.logger.info(f"Client {addr} disconnected (socket closed)")
                                break

                            else:
                                self.logger.debug(f"Client {addr} still connected, received empty message")
                                continue

                        except socket.error as e:
                            self.logger.info(f"Client {addr} disconnected (socket error: {e})")
                            break

                    self.logger.info(f"Processing message from {addr}: {message['type']}")
                    self.process_message(client_socket, message)

                except socket.timeout:
                    self.logger.debug(f"Client {addr} socket timeout, continuing to wait")
                    continue  # Keep connection open

                except Exception as e:
                    self.logger.error(f"Error processing message from {addr}: {e}")
                    # Check if socket is still open
                    try:
                        client_socket.recv(1, socket.MSG_PEEK)
                        self.logger.debug(f"Client {addr} socket still open, continuing")
                        continue

                    except socket.error:
                        self.logger.info(f"Client {addr} disconnected (socket error after exception: {e})")
                        break

        except Exception as e:
            self.logger.error(f"Error in handle_client {addr}: {e}")

        finally:
            self.remove_client(client_socket)
            try:
                client_socket.close()

            except Exception as e:
                self.logger.error(f"Error closing client socket {addr}: {e}")

    # Remove (kick) client logic and close its connection
    def remove_client(self, client_socket):
        with self.lock:
            if client_socket in self.clients:
                self.logger.info(f"Removing client {client_socket.getpeername()}")
                del self.clients[client_socket]

    # Handle incoming message (message type, sender/receiver information, etc.)
    def process_message(self, client_socket, message):
        try:
            msg_type = message["type"]
            data = message["data"]

            # Determine message type and call corresponding method
            if msg_type == Protocol.MESSAGE_TYPES["login"]:
                self.handle_login(client_socket, data)

            elif msg_type == Protocol.MESSAGE_TYPES["register"]:
                self.handle_register(client_socket, data)

            elif msg_type == Protocol.MESSAGE_TYPES["message"]:
                self.handle_message(client_socket, data)

            elif msg_type == Protocol.MESSAGE_TYPES["file"]:
                self.handle_file(client_socket, data)

            elif msg_type == Protocol.MESSAGE_TYPES["contact_list"]:
                self.handle_contact_list(client_socket)

            else:
                client_socket.send(Protocol.create_error_message("Unknown message type"))

        except Exception as e:
            self.logger.error(f"Error in process_message for {client_socket.getpeername()}: {e}")
    
    # User login handling logic
    def handle_login(self, client_socket, data):
        # Fetch user information from the frontend form
        username = data["username"]
        password = data["password"]

        # Call database method to login user and fetch user id
        user_id = self.database.authenticate_user(username, password)

        if user_id:
            with self.lock:
                # Set client to client handler dictionary
                self.clients[client_socket] = user_id

            client_socket.send(Protocol.create_success_message(f"User {username} logged in"))
            self.logger.info(f"User {username} logged in from {client_socket.getpeername()}")

        else:
            client_socket.send(Protocol.create_error_message("Invalid username or password"))

    # User register handling logic
    def handle_register(self, client_socket, data):
        # Fetch user information from the frontend form
        username = data["username"]
        password = data["password"]

        # Call database method and check if user was added successfully
        if self.database.add_user(username, password):
            client_socket.send(Protocol.create_success_message(f"User {username} registered"))
            self.logger.info(f"User {username} registered from {client_socket.getpeername()}")

        else:
            client_socket.send(Protocol.create_error_message("Username already exists"))

    # Message handling logic
    def handle_message(self, client_socket, data):
        sender_id = self.clients.get(client_socket)

        if not sender_id:
            client_socket.send(Protocol.create_error_message("Not authenticated"))
            return
        
        sender = self.database.get_username(sender_id)
        receiver = data["receiver"]
        content = data["content"]
        
        receiver_id = self.database.get_user_id(receiver)

        if receiver_id:
            # Call database method to store message if there is a valid receiver id
            self.database.store_message(sender_id, receiver_id, content)

            for sock, uid in self.clients.items():
                if uid == receiver_id:
                    sock.send(Protocol.create_text_message(sender, receiver, content))

        else:
            client_socket.send(Protocol.create_error_message(f"User {receiver} not found"))

    # File handling logic
    def handle_file(self, client_socket, data):
        sender_id = self.clients.get(client_socket)

        if not sender_id:
            client_socket.send(Protocol.create_error_message("Not authenticated"))
            return
        
        filename, file_data = Protocol.decode_file(client_socket)
        
        if not filename:
            client_socket.send(Protocol.create_error_message("Invalid file data"))
            return

        receiver = data.get("receiver")
        receiver_id = self.database.get_user_id(receiver) if receiver else None
        
        if receiver_id:
            # Browse to files
            file_path = os.path.join('files', filename)
        
            # Start writing file to the local file
            with open(file_path, 'wb') as f:
                f.write(file_data)
        
            self.database.store_file(sender_id, receiver_id, filename)
        
            for sock, uid in self.clients.items():
                if uid == receiver_id:
                    sock.send(Protocol.create_file_message(self.database.get_username(sender_id), receiver, filename, file_data))

        else:
            client_socket.send(Protocol.create_error_message(f"User {receiver} not found"))

    def handle_contact_list(self, client_socket):
        """Handle contact list requests."""
        user_id = self.clients.get(client_socket)
        if not user_id:
            client_socket.send(Protocol.create_error_message("Not authenticated"))
            return
        contacts = self.database.get_contacts(user_id)
        client_socket.send(Protocol.encode_message(
            Protocol.MESSAGE_TYPES["contact_list"],
            {"contacts": contacts}
        ))
   

if __name__ == "__main__":
    server = Server()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()