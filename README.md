# Messenger

A simple server-client based LAN chat application built with Python. It features user registration, login, private messaging, file transfer, and contact management using a custom communication protocol. All data (users, contacts, messages) is stored locally using SQLite3.

## How to Run

### 1. Clone the repo
```
git clone https://github.com/timurenk0/messenger.git
cd messenger
```

### 2. Initialize venv 
```
python -m venv venv

# Run virtual environment
venv\Scripts\activate
```

### 3. Run the application
```
python server.py # on the server device
python client.py # on any other device in the same local network
```

---

## ✨ Features

- 🧑‍🤝‍🧑 User Authentication — Register and log in using a username and password
- 📇 Contact Management — Add users to your contact list by username
- 💬 Text Messaging — Real-time chat between connected users
- 📁 File Sharing — Send and receive files via sockets
- 💡 Custom Protocol — Each action (login, message, file, etc.) is handled using defined message types
- 💾 Local Persistence — All user data is stored in a local SQLite3 database

---

## 📁 Project Structure

```
/ messenger
├── client.py # Client-side application
├── server.py # Server-side application
├── protocols.py # Custom protocol definitions
├── database.py # SQLite3 database operations
└── README.md # Project documentation
```