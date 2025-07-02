import json
import struct
import socket


class Protocol:
    # Set maximum file size that user can send at once = 2MB
    MAX_SIZE = 2048 * 1024

    # Set message types to differntiate methods
    MESSAGE_TYPES = {
        "login": "LOGIN",
        "register": "REGISTER",
        "message": "MESSAGE",
        "file": "FILE",
        "contact_list": "CONTACT_LIST",
        "error": "ERROR",
        "success": "SUCCESS"
    }

    # Encode message into JSON string for future socket transfering
    @staticmethod
    def encode_message(message_type, data):
        message = {
            "type": message_type,
            "data": data
        }

        message_json = json.dumps(message).encode("utf-8")
        length = struct.pack("!I", len(message_json))

        return length + message_json
    
    # Decode message from a socket (from JSON format)
    @staticmethod
    def decode_message(sock, use_timeout=False):
        try:
            if use_timeout:
                sock.settimeout(5.0) # Set timeout in case of synchronous calls
            
            # Receive bytes responsible for the incoming message length to set buffer size
            data_length = sock.recv(4)

            if not data_length:
                return None
            
            # Set buffer size
            length = struct.unpack("!I", data_length)[0]
            message_data = sock.recv(length) # Fetch exactly needed number of bytes

            if not message_data:
                return None
            
            return json.loads(message_data.decode("utf-8"))
        
        except (socket.timeout, socket.error, json.JSONDecodeError) as e:
            return None
        
        finally:
            if use_timeout:
                sock.settimeout(None) # Reset timeout

    # Encode file similar to messages
    @staticmethod
    def encode_file(filename, file_data, receiver=None):
        # Check if file size is more than the maximum set size (2MB)
        if len(file_data) > Protocol.MAX_FILE_SIZE:
            raise ValueError("File size exceeds 2MB limit")
        
        data = {
            "filename": filename,
            "file_size": len(file_data)
        }

        if receiver:
            data["receiver"] = receiver

        metadata = Protocol.encode_message(Protocol.MESSAGE_TYPES["file"], data)

        return metadata + file_data

    # Decode file similar to messages
    @staticmethod
    def decode_file(sock):
        message = Protocol.decode_message(sock, use_timeout=False)

        if not message or message["type"] != Protocol.MESSAGE_TYPES["file"]:
            return None, None
        
        file_size = message["data"]["file_size"]
        filename = message["data"]["filename"]
        file_data = b""
        
        # Send file data until every "chunk" of data is send
        while len(file_data) < file_size:
            chunk = sock.recv(file_size - len(file_data))
        
            if not chunk:
                raise ConnectionError("Incomplete file data received")
        
            file_data += chunk
        
        return filename, file_data

    # Create login request (handshake) message
    @staticmethod
    def create_login_message(username, password):
        return Protocol.encode_message(
            Protocol.MESSAGE_TYPES["login"],
            {"username": username, "password": password}
        )

    # Create register request (handshake) message
    @staticmethod
    def create_register_message(username, password):
        """Create a registration request message."""
        return Protocol.encode_message(
            Protocol.MESSAGE_TYPES["register"],
            {"username": username, "password": password}
        )

    # Create send text message request (handshake) message
    @staticmethod
    def create_text_message(sender, receiver, content):
        """Create a text message."""
        return Protocol.encode_message(
            Protocol.MESSAGE_TYPES["message"],
            {"sender": sender, "receiver": receiver, "content": content}
        )

    # Create send file message request (handshake) message
    @staticmethod
    def create_file_message(receiver, filename, file_data):
        """Create a file message."""
        return Protocol.encode_file(filename, file_data, receiver=receiver)

    # Create error message request (handshake) message
    @staticmethod
    def create_error_message(error_message):
        """Create an error response message."""
        return Protocol.encode_message(
            Protocol.MESSAGE_TYPES["error"],
            {"message": error_message}
        )

    # Create success message request (handshake) message
    @staticmethod
    def create_success_message(message):
        """Create a success response message."""
        return Protocol.encode_message(
            Protocol.MESSAGE_TYPES["success"],
            {"message": message}
        )