# Current Master Password: ninja
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
from sqlcipher3 import dbapi2 as sqlite
from datetime import datetime

def initialize_database(key):
    """Initializes and returns the connection to the encrypted database."""
    try:
        conn = sqlite.connect('SecVault.db')
        cursor = conn.cursor()
        
        # Set the encryption key using the raw key bytes
        cursor.execute(f"PRAGMA key = \"x'{key.hex()}'\";")

        # 1. TABLE: Category (Matches your OptionMenu: Work, Personal, Wifi)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Category (
                CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE
            )
        ''')

        # 2. TABLE: Event_Type (For security auditing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Event_Type (
                EventID INTEGER PRIMARY KEY AUTOINCREMENT,
                EventType TEXT NOT NULL UNIQUE
            )
        ''')

        # 3. TABLE: Vault_Entry (Matches your GUI Add Window fields)
        # We use CategoryID to link to the Category table (Normalization)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Vault_Entry (
                EntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                Service TEXT NOT NULL,
                Username TEXT NOT NULL,
                Password TEXT NOT NULL,
                CategoryID INTEGER,
                FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
            )
        ''')

        # 4. TABLE: Vault_Log (Audit trail for password changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Vault_Log (
                LogID INTEGER PRIMARY KEY AUTOINCREMENT,
                EntryID INTEGER,
                EventID INTEGER,
                Timestamp TEXT NOT NULL,
                FOREIGN KEY (EntryID) REFERENCES Vault_Entry(EntryID),
                FOREIGN KEY (EventID) REFERENCES Event_Type(EventID)
            )
        ''')

        # 5. TABLE: Authentication_Log (Login/Logout/Key Change tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Authentication_Log (
                LogID INTEGER PRIMARY KEY AUTOINCREMENT,
                EventID INTEGER,
                Timestamp TEXT NOT NULL,
                FOREIGN KEY (EventID) REFERENCES Event_Type(EventID)
            )
        ''')

        seed_lookup_data(conn)
        log_auth_event(conn, "LOGIN")
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database Initialization Error: {e}")
        return None

def seed_lookup_data(conn):
    """Populates categories and events if they don't exist."""
    cursor = conn.cursor()
    categories = [('Work',), ('Personal',), ('Wifi',)]
    cursor.executemany("INSERT OR IGNORE INTO Category (Name) VALUES (?)", categories)
    
    events = [('LOGIN',), ('LOGOUT',), ('ADD_ENTRY',), ('DELETE_ENTRY',), ('UPDATE_ENTRY',), ('KEY_CHANGE',)]
    cursor.executemany("INSERT OR IGNORE INTO Event_Type (EventType) VALUES (?)", events)
    conn.commit()

# --- Security Logging ---

def log_auth_event(conn, event_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute("INSERT INTO Authentication_Log (EventID, Timestamp) VALUES (?, ?)", (result[0], now))
        conn.commit()

def log_vault_action(conn, entry_id, event_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    result = cursor.fetchone()
    if result:
        cursor.execute("INSERT INTO Vault_Log (EntryID, EventID, Timestamp) VALUES (?, ?, ?)", 
                       (entry_id, result[0], now))
        conn.commit()

# --- Administrative Functions (Preserved) ---

def change_key(conn, new_key_raw):
    """Changes the database master key and logs the event."""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA rekey = \"x'{new_key_raw.hex()}'\";")
        log_auth_event(conn, "KEY_CHANGE")
        conn.commit()
    except Exception as e:
        print(f"Rekey Error: {e}")

def delete_entry(conn, target_id):
    """Deletes an entry and logs the action."""
    try:
        log_vault_action(conn, target_id, "DELETE_ENTRY")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Vault_Entry WHERE EntryID = ?", (target_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Delete Error: {e}")
        return False