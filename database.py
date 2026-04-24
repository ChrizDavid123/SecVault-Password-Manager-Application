# Current Master Password: ninja
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
from sqlcipher3 import dbapi2 as sqlite
from tabulate import tabulate
from datetime import datetime

def initialize_database(key):
    try:
        conn = sqlite.connect('SecVault.db')
        cursor = conn.cursor()
        
        # Set the encryption keys
        cursor.execute(f"PRAGMA key = \"x'{key.hex()}'\";")

        # 1. TABLE: Category (Lookup table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Category (
                CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE
            )
        ''')

        # 2. TABLE: Event_Type (Lookup table for Log types)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Event_Type (
                EventID INTEGER PRIMARY KEY AUTOINCREMENT,
                EventType TEXT NOT NULL UNIQUE
            )
        ''')

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

        # Seed initial lookup data if empty
        seed_lookup_data(conn)
        
        # Record Login
        log_auth_event(conn, "LOGIN")

        conn.commit()
        return conn
    except Exception as e:
        print(f"Access Denied: {e}")
        return None

def seed_lookup_data(conn):
    """Populates Category and Event_Type tables so Foreign Keys work."""
    cursor = conn.cursor()
    # Categories from your previous list
    categories = [('Work',), ('Personal',), ('WiFi',)]
    cursor.executemany("INSERT OR IGNORE INTO Category (Name) VALUES (?)", categories)
    
    # Event Types for logs
    events = [('LOGIN',), ('LOGOUT',), ('ADD_ENTRY',), ('DELETE_ENTRY',), ('UPDATE_ENTRY',)]
    cursor.executemany("INSERT OR IGNORE INTO Event_Type (EventType) VALUES (?)", events)
    conn.commit()

def log_auth_event(conn, event_name):
    """Records security access (Login/Logout) per the diagram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    # Get the EventID for the specific action
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    event_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Authentication_Log (EventID, Timestamp) VALUES (?, ?)", (event_id, now))
    conn.commit()

def log_vault_action(conn, entry_id, event_name):
    """Records actions taken on specific vault entries."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    event_id = cursor.fetchone()[0]
    
    cursor.execute("INSERT INTO Vault_Log (EntryID, EventID, Timestamp) VALUES (?, ?, ?)", 
                   (entry_id, event_id, now))
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
    rows = cursor.fetchall()
    print(tabulate(rows, headers=["ID", "Action", "Time"], tablefmt="fancy_grid"))