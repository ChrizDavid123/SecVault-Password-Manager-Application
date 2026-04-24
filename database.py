# Current Master Password: ninja
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
import sqlite3

def initialize_database(user_key=None):
    """
    Initializes the database connection and creates tables based on the ERD.
    Note: user_key is passed here to maintain compatibility with your 
    authentication logic, though standard SQLite isn't encrypted by default.
    """
    conn = sqlite3.connect("secvault_data.db")
    cursor = conn.cursor()

    # 1. Category Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Category (
            CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL UNIQUE
        )
    ''')

    # 2. Event Type Table (e.g., View, Edit, Delete, Login)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EventType (
            EventID INTEGER PRIMARY KEY AUTOINCREMENT,
            EventType TEXT NOT NULL UNIQUE
        )
    ''')

    # 3. Vault Entry Table (Linked to Category)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VaultEntry (
            EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
            Service TEXT NOT NULL,
            Username TEXT NOT NULL,
            Password TEXT NOT NULL,
            CategoryID INTEGER,
            FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
        )
    ''')

    # 4. Vault Log (Tracks actions on specific entries)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VaultLog (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            EntryID INTEGER,
            EventID INTEGER,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (EntryID) REFERENCES VaultEntry(EntryID),
            FOREIGN KEY (EventID) REFERENCES EventType(EventID)
        )
    ''')

    # 5. Authentication Log (Tracks app logins)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AuthenticationLog (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            EventID INTEGER,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (EventID) REFERENCES EventType(EventID)
        )
    ''')

    # Seed initial data for Categories and Event Types
    _seed_data(cursor)
    
    conn.commit()
    return conn

def _seed_data(cursor):
    """Populates lookup tables if they are empty."""
    categories = [('Work',), ('Personal',), ('Wifi',), ('Social',)]
    cursor.executemany('INSERT OR IGNORE INTO Category (Name) VALUES (?)', categories)

    event_types = [('Login Success',), ('Login Failed',), ('View Password',), 
                   ('Update Password',), ('Delete Password',), ('Create Entry',)]
    cursor.executemany('INSERT OR IGNORE INTO EventType (EventType) VALUES (?)', event_types)

if __name__ == "__main__":
    # Test initialization
    initialize_database()
    print("Database and tables created successfully.")