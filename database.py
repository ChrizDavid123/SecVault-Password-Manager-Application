# Current Master Password: ninja
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
from sqlcipher3 import dbapi2 as sqlite
from datetime import datetime
from tabulate import tabulate
import hashlib

def initialize_database(key):
    """Initializes and returns the connection to the encrypted database."""
    try:
        conn = sqlite.connect('SecVault.db')
        cursor = conn.cursor()
        
        # Set the encryption key
        cursor.execute(f"PRAGMA key = \"x'{key.hex()}'\";")

        # 1. TABLE: Category
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Category (
                CategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
                Name TEXT NOT NULL UNIQUE
            )
        ''')

        # 2. TABLE: Event_Type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Event_Type (
                EventID INTEGER PRIMARY KEY AUTOINCREMENT,
                EventType TEXT NOT NULL UNIQUE
            )
        ''')

        # 3. TABLE: Vault_Entry (Matches GUI fields)
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

        # 4. TABLE: Vault_Log
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

        # 5. TABLE: Authentication_Log
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
        print(f"Database Error: {e}")
        return None

def seed_lookup_data(conn):
    cursor = conn.cursor()
    categories = [('Work',), ('Personal',), ('Wifi',)]
    cursor.executemany("INSERT OR IGNORE INTO Category (Name) VALUES (?)", categories)
    
    events = [('LOGIN',), ('LOGOUT',), ('ADD_ENTRY',), ('DELETE_ENTRY',), ('UPDATE_ENTRY',), ('KEY_CHANGE',)]
    cursor.executemany("INSERT OR IGNORE INTO Event_Type (EventType) VALUES (?)", events)
    conn.commit()

def log_auth_event(conn, event_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    res = cursor.fetchone()
    if res:
        cursor.execute("INSERT INTO Authentication_Log (EventID, Timestamp) VALUES (?, ?)", (res[0], now))
        conn.commit()

def log_vault_action(conn, entry_id, event_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("SELECT EventID FROM Event_Type WHERE EventType = ?", (event_name,))
    res = cursor.fetchone()
    if res:
        cursor.execute("INSERT INTO Vault_Log (EntryID, EventID, Timestamp) VALUES (?, ?, ?)", (entry_id, res[0], now))
        conn.commit()

# --- ADMIN FUNCTIONS ---

def change_key(conn, new_key_raw):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA rekey = \"x'{new_key_raw.hex()}'\";")
    log_auth_event(conn, "KEY_CHANGE")
    conn.commit()

def delete_entry(conn, target_id):
    log_vault_action(conn, target_id, "DELETE_ENTRY")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Vault_Entry WHERE EntryID = ?", (target_id,))
    conn.commit()

# --- DEMONSTRATION BLOCK (Runs only when file is executed directly) ---

if __name__ == "__main__":
    print("--- SECVAULT DATABASE ENGINE DEMO ---")
    
    # 1. Setup dummy key
    test_key = hashlib.sha256(b"demo_password").digest()
    
    # 2. Init
    conn = initialize_database(test_key)
    if conn:
        print("[+] Database Initialized & Tables Created.")
        
        # 3. Simulate GUI adding an entry
        cursor = conn.cursor()
        cursor.execute("SELECT CategoryID FROM Category WHERE Name = 'Work'")
        work_id = cursor.fetchone()[0]
        
        cursor.execute("INSERT INTO Vault_Entry (Service, Username, Password, CategoryID) VALUES (?,?,?,?)", 
                       ("DemoService", "Admin", "Pass123!", work_id))
        new_id = cursor.lastrowid
        log_vault_action(conn, new_id, "ADD_ENTRY")
        print(f"[+] Demo entry added (ID: {new_id}).")

        # 4. Show the data (JOIN query)
        print("\n--- CURRENT VAULT ENTRIES ---")
        cursor.execute('''
            SELECT v.EntryID, v.Service, v.Username, c.Name 
            FROM Vault_Entry v 
            JOIN Category c ON v.CategoryID = c.CategoryID
        ''')
        print(tabulate(cursor.fetchall(), headers=["ID", "Service", "User", "Category"], tablefmt="grid"))

        # 5. Show Security Logs
        print("\n--- SECURITY AUDIT LOG ---")
        cursor.execute('''
            SELECT a.LogID, e.EventType, a.Timestamp 
            FROM Authentication_Log a 
            JOIN Event_Type e ON a.EventID = e.EventID
        ''')
        print(tabulate(cursor.fetchall(), headers=["LogID", "Event", "Time"], tablefmt="simple"))
        
        conn.close()
        print("\n[!] Demo Complete.")