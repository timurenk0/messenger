import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from protocols import Protocol
import logging

class Client:
    def __init__(self, host='your_server_ip_address', port=12345):
        # Setup connection
        self.host = host
        self.port = port

        # Setup client
        self.sock = None
        self.username = None

        # Setup state
        self.running = False
        self.receive_thread = None

        # Setup logger
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Setup GUI
        self.root = tk.Tk()
        self.root.title("LAN Messenger")
        self.root.geometry("600x400")
        self.setup_login_window()

    # Create login window with form
    def setup_login_window(self):
        """Set up the login/register window."""
        self.clear_window()
        self.root.geometry("300x200")

        tk.Label(self.root, text="LAN Messenger Login").pack(pady=10)
        tk.Label(self.root, text="Username").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)
        tk.Label(self.root, text="Password").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.handle_login).pack(pady=5)
        tk.Button(self.root, text="Register", command=self.handle_register).pack(pady=5)

    # Setup main window with chat
    def setup_main_window(self):
        self.clear_window()
        self.root.geometry("600x400")

        # Message display
        self.message_text = tk.scrolledtext.ScrolledText(self.root, height=15, wrap=tk.WORD)
        self.message_text.pack(pady=10, padx=10, fill="both", expand=True)
        self.message_text.config(state='disabled')

        # Message input
        frame = tk.Frame(self.root)
        frame.pack(pady=5, padx=10, fill="x")
        tk.Label(frame, text="To:").pack(side="left")
        self.receiver_entry = tk.Entry(frame, width=15)
        self.receiver_entry.pack(side="left", padx=5)
        tk.Label(frame, text="Message:").pack(side="left")
        self.message_entry = tk.Entry(frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(frame, text="Send", command=self.send_message).pack(side="left")

        # Buttons
        tk.Button(self.root, text="Send File", command=self.send_file).pack(pady=5)
        tk.Button(self.root, text="View Contacts", command=self.view_contacts).pack(pady=5)
        tk.Button(self.root, text="Exit", command=self.exit).pack(pady=5)

        # Start receive thread after setting up main window
        self.start_receive_thread()

    # Pretty self explanatory...
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # Connect client to the server
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)  # Timeout for initial connection
            self.sock.connect((self.host, self.port))

            # Set running state to True
            self.running = True
            self.logger.info("Connected to server")

            return True
        
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self.root.after(0, lambda: messagebox.showerror("Connection Error", f"Failed to connect to server: {e}. Is the server running?"))
            self.sock = None

            return False

    # Start user thread
    def start_receive_thread(self):
        if self.running and self.sock:
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            self.logger.info("Started receive thread")

    # Check is user is connected to the socket
    def is_connected(self):
        return self.sock is not None and self.running
    
    # Receive message handling logic for user
    def receive_messages(self):
        while self.running:
            try:
                message = Protocol.decode_message(self.sock, use_timeout=False)

                if not message:
                    self.logger.info("Disconnected from server: no data received")
                    self.running = False
                    self.root.after(0, lambda: self.handle_disconnection("Disconnected from server: connection closed by server"))
                    break

                self.handle_server_message(message)

            except socket.error as e:
                self.logger.error(f"Socket error receiving message: {e}")
                self.running = False
                self.root.after(0, lambda: self.handle_disconnection(f"Connection error: {e}"))
                break

            except Exception as e:
                self.logger.error(f"Unexpected error receiving message: {e}")
                self.running = False
                self.root.after(0, lambda: self.handle_disconnection(f"Unexpected error: {e}"))
                break

    # Disonnect user handling logic
    def handle_disconnection(self, message):
        if self.sock:
            try:
                self.sock.close()

            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")

            self.sock = None

        self.running = False
        self.root.after(0, lambda: messagebox.showerror("Error", message))
        self.root.after(0, self.setup_login_window)

    # Server incoming messages handling logic
    def handle_server_message(self, message):
        msg_type = message["type"]
        data = message["data"]
        self.logger.info(f"Received message: {message}")

        # Check incoming message type
        if msg_type == Protocol.MESSAGE_TYPES["success"]:
            self.root.after(0, lambda: messagebox.showinfo("Success", data["message"]))

        elif msg_type == Protocol.MESSAGE_TYPES["error"]:
            self.root.after(0, lambda: messagebox.showerror("Error", data["message"]))

        elif msg_type == Protocol.MESSAGE_TYPES["message"]:
            self.root.after(0, lambda: self.display_message(f"{data['sender']}: {data['content']}\n"))

        elif msg_type == Protocol.MESSAGE_TYPES["file"]:
            filename, file_data = Protocol.decode_file(self.sock)

            if filename:
                save_path = os.path.join("received_files", f"received_{filename}")
                os.makedirs("received_files", exist_ok=True)

                # Start writing incoming files
                with open(save_path, 'wb') as f:
                    f.write(file_data)

                self.root.after(0, lambda: self.display_message(f"Received file: {filename} (saved to {save_path})\n"))

        elif msg_type == Protocol.MESSAGE_TYPES["contact_list"]:
            contacts = "\n".join(data["contacts"])
            self.root.after(0, lambda: messagebox.showinfo("Contacts", f"Contacts:\n{contacts}"))

    # Display message in GUI
    def display_message(self, text):
        self.message_text.config(state='normal')
        self.message_text.insert(tk.END, text)
        self.message_text.config(state='disabled')
        self.message_text.see(tk.END)

    # User login handling logic + button event listener function
    def handle_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        if not self.is_connected() and not self.connect():
            return
        
        try:
            self.sock.send(Protocol.create_login_message(username, password))
            message = Protocol.decode_message(self.sock, use_timeout=True)

            if message and message["type"] == Protocol.MESSAGE_TYPES["success"]:
                self.username = username
                self.setup_main_window()

            else:
                self.root.after(0, lambda: messagebox.showerror("Error", message["data"]["message"] if message else "No response from server"))

                if self.sock:
                    self.sock.close()
                    self.sock = None

        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send login request: {e}"))

            if self.sock:
                self.sock.close()
                self.sock = None

    # User register handling logic + button event listener function
    def handle_register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        if not self.is_connected() and not self.connect():
            return
        
        try:
            self.sock.send(Protocol.create_register_message(username, password))
            message = Protocol.decode_message(self.sock, use_timeout=True)

            if message and message["type"] == Protocol.MESSAGE_TYPES["success"]:
                self.root.after(0, lambda: messagebox.showinfo("Success", "Registration successful! Please log in."))

            else:
                self.root.after(0, lambda: messagebox.showerror("Error", message["data"]["message"] if message else "No response from server"))

            if self.sock:
                self.sock.close()
                self.sock = None

        except Exception as e:
            self.logger.error(f"Register error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send register request: {e}"))

            if self.sock:
                self.sock.close()
                self.sock = None

    # Send text message handling logic + button event listener function
    def send_message(self):
        if not self.is_connected():
            self.root.after(0, lambda: messagebox.showerror("Error", "Not connected to server"))
            return
        
        receiver = self.receiver_entry.get()
        content = self.message_entry.get()

        if not receiver or not content:
            messagebox.showerror("Error", "Please enter receiver and message")
            return
        
        try:
            self.sock.send(Protocol.create_text_message(self.username, receiver, content))
            self.message_entry.delete(0, tk.END)
            
        except Exception as e:
            self.logger.error(f"Send message error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send message: {e}"))

    # Send file message handling logic + button event listener function
    def send_file(self):
        if not self.is_connected():
            self.root.after(0, lambda: messagebox.showerror("Error", "Not connected to server"))
            return
        
        file_path = filedialog.askopenfilename()

        if not file_path:
            return
        
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        if file_size > Protocol.MAX_FILE_SIZE:
            messagebox.showerror("Error", "File size exceeds 2MB limit")
            return
        
        with open(file_path, 'rb') as f:
            file_data = f.read()

        receiver = self.receiver_entry.get()

        if not receiver:
            messagebox.showerror("Error", "Please enter receiver")
            return
        
        try:
            self.sock.send(Protocol.create_file_message(receiver, filename, file_data))

        except Exception as e:
            self.logger.error(f"Send file error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to send file: {e}"))

    # Display contacts list handling logic + button event listener function
    def view_contacts(self):
        if not self.is_connected():
            self.root.after(0, lambda: messagebox.showerror("Error", "Not connected to server"))
            return
        
        try:
            self.sock.send(Protocol.create_contact_list_request())

        except Exception as e:
            self.logger.error(f"View contacts error: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to request contacts: {e}"))


    def exit(self):
        """Exit the application."""
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                self.logger.error(f"Error closing socket: {e}")
            self.sock = None
        self.root.quit()

    # Run the GUI
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    client = Client()
    client.run()