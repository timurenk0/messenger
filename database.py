import sqlite3 as sq
import logging


class Database:
    def __init__(self):
        # Configure logger for easier debugging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        self.logger = logging.getLogger(__name__)
        self.conn = sq.connect("database.db", check_same_thread=False)
        # Initialize tables
        self.create_tables()
        self.logger.info("Database initialized")

    # Create necessary tables for data management
    def create_tables(self):
        try:
            cursor = self.conn.cursor()

            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users
                    (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT UNIQUE NOT NULL,
                           password TEXT NOT NULL
                    )
            """)

            # Create messages tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages
                    (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           sender_id INTEGER,
                           receiver_id INTEGER,
                           message TEXT NOT NULL,
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (sender_id) REFERENCES users(id),
                           FOREIGN KEY (receiver_id) REFERENCES users(id)
                    )
            """)

            # Create files table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files
                    (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           sender_id INTEGER,
                           receiver_id INTEGER,
                           filename TEXT NOT NULL,
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (sender_id) REFERENCES users(id),
                           FOREIGN KEY (receiver_id) REFERENCES users(id)
                    )
            """)

            self.conn.commit()
            self.logger.info("Database tables created")
        
        except Exception as e:
            self.logger.error(f"Error creating tables: {str(e)}")
            raise

    # Add (register) user to the database
    def add_user(self, username, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))

            self.conn.commit()
            self.logger.info(f"User {username} added to database")
            return True

        except sq.IntegrityError:
            self.logger.error(f"Username {username} already exists")
            return False

        except Exception as e:
             self.logger.error(f"Error adding user {username} : {str(e)}")
             return False

# Authenticate (login) user
def authenticate_user(self, username, password):
     try:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        # Fetch user id 
        user_id = result[0] if result else None

        if user_id:
            self.logger.info(f"User {username} added to the database with ID {user_id}")
        else:
            self.logger.warning(f"Authentication failed for user {username}")
        
        return user_id
     
     except Exception as e:
         self.logger.error(f"Error authenticating user {username}: {str(e)}")
         return None
     
# Fetch username from the database by user id
def get_username(self, user_id):
    try:
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()

        username = result[0] if result else None

        if username:
            self.logger.debug(f"Retrieved username for user {user_id}")
        else:
            self.logger.warning(f"No username found for user {user_id}")
        
        return username
    
    except Exception as e:
        self.logger.error(f"Error retrieving user_id for username {username}: {str(e)}")
        return None

# Store sent messages to the database
def store_message(self, sender_id, receiver_id, message):
    try:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (sender_id, receiver_id, message))

        self.conn.commit()
        self.logger.info(f"Stored message from user {sender_id} to user {receiver_id}")

        return True
    
    except Exception as e:
        self.logger.error(f"Error storing message from user {sender_id}: {str(e)}")
        return False
    
# Store sent files (filenames) to the database
def store_file(self, sender_id, receiver_id, filename):
    try:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO files (sender_id, receiver_id, filename) VALUES (?, ?, ?)", (sender_id, receiver_id, filename))

        self.conn.commit()
        self.logger.info(f"Stored file {filename} sent from user {sender_id} to user {receiver_id}")

        return True
    
    except Exception as e:
        self.logger.error(f"Error storing file {filename} from user {sender_id}: {str(e)}")
        return False
    
# Close the connection with the database
def close(self):
    try:
        self.conn.close()
        self.logger.info("Database connection closed")
    
    except Exception as e:
        self.logger.error(f"Error closing database: {str(e)}")
    
            
            