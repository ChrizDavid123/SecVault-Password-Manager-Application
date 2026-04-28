from sqlcipher3 import dbapi2 as sqlite
# from tabulate import tabulate
from datetime import datetime
from pathlib import Path
from secrets import token_bytes


db_path = Path("SecVault.db")

def initialize_database(key):
    conn = sqlite.connect('SecVault.db')
    
    # Set the encryption keys
    conn.execute(f"PRAGMA key = \"x'{key.hex()}'\";")
    cursor = conn.cursor()

    # 1. TABLE: Category (Lookup table)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Category (
            CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL UNIQUE
        )
    ''')

    # Insert category values into Category table
    categories = [('Work',), ('Personal',), ('WiFi',)]
    cursor.executemany("INSERT OR IGNORE INTO Category (Name) VALUES (?)", categories)

    # 2. TABLE: Event_Type (Lookup table for Log types)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Event_Type (
            EventID INTEGER PRIMARY KEY AUTOINCREMENT,
            EventType TEXT NOT NULL UNIQUE
        )
    ''')

    # Insert event type values into Event_Type table
    events = [('LOGIN',), ('LOGOUT',), ('ADD_ENTRY',), ('DELETE_ENTRY',), ('UPDATE_ENTRY',)]
    cursor.executemany("INSERT OR IGNORE INTO Event_Type (EventType) VALUES (?)", events)

    # 3. TABLE: Vault_Entry (The main credentials)
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

    # 4. TABLE: Vault_Log (Tracking changes to entries)
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

    # 5. TABLE: Authentication_Log (Login/Logout tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Authentication_Log (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            EventID INTEGER,
            Timestamp TEXT NOT NULL,
            FOREIGN KEY (EventID) REFERENCES Event_Type(EventID)
        )
    ''')

    conn.commit()

    return conn

def access_database(key):
    try:
        conn = sqlite.connect('SecVault.db')
        conn.execute(f"PRAGMA key = \"x'{key.hex()}'\";")
        log_auth_event(conn, "LOGIN")
        return conn
    except Exception as e:
         print(f"Access Denied: {e}")


def log_auth_event(conn, event_name):
    """Records security access (Login/Logout) per the diagram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    # Get the EventID for the specific action
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    event_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Authentication_Log (EventID, Timestamp) VALUES (?, ?)", (event_id, now))
    print(f"{event_id} | Timestamp: {now}") # Testing
    conn.commit()


def log_vault_action(conn, entry_id, event_name):
    """Records actions taken on specific vault entries."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    event_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Vault_Log (EntryID, EventID, Timestamp) VALUES (?, ?, ?)", 
                   (entry_id, event_id, now))
    print(f"{event_id} at {entry_id} | Timestamp: {now}") # Testing
    conn.commit()


def show_auth_logs(conn):
    """Displays the Authentication Log table."""
    cursor = conn.cursor()
    query = '''
        SELECT a.LogID, e.EventType, a.Timestamp 
        FROM Authentication_Log a
        JOIN Event_Type e ON a.EventID = e.EventID
    '''
    cursor.execute(query)
    # rows = cursor.fetchall()
    # print(tabulate(rows, headers=["ID", "Action", "Time"], tablefmt="fancy_grid"))



def delete_vault(conn):
    # A random key that won't be stored won't be saved in order to make data recovery impossible
    disposal_key = token_bytes(32)
    conn.execute(f"PRAGMA key = \"x'{disposal_key.hex()}'\";")
    conn.close()

    db_path.unlink()
    print("Database deleted!")