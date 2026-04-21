# Current Master Password: sosorry
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
from json import dumps, loads
from pathlib import Path
from sqlcipher3 import dbapi2 as sqlite
from tabulate import tabulate
from datetime import datetime
from authentication import verify_key, create_master_password, change_master_password

def initialize_database(key):
    """Initializes and returns the connection to the encrypted database."""
    try:
        conn = sqlite.connect('SecVault.db')
        cursor = conn.cursor()
        
        # Set the encryption key
        cursor.execute(f"PRAGMA key = \"x'{key.hex()}'\";")
        
        # Verify the key works by attempting a simple operation
        # cursor.execute("SELECT count(*) FROM sqlite_master;") # There is already verification happening from authentication.py - joms

        # Table 1: The Vault
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vault (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                category TEXT
            )
        ''')

        # Table 2: Access Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL, -- 'LOGIN' or 'LOGOUT'
                timestamp TEXT NOT NULL
            )
        ''')

        log_event(conn, "LOGIN")

        conn.commit()
        return conn
    except Exception as e:
        print(f"Access Denied: {e}")
        return None

def log_event(conn, event_type):
    """Helper function to record login/logout times."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO access_logs (event_type, timestamp) VALUES (?, ?)", (event_type, now))
    conn.commit()

def save_entry(conn):
    """Saves a new entry based on user input."""
    category = input("Category: ").strip()
    service = input("Service: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vault (service, username, password, category) 
            VALUES (?, ?, ?, ?)
        ''', (service, username, password, category))
        conn.commit()
        print(f"Securely saved {service} to the vault.")
    except Exception as e:
        print(f"Failed to save: {e}")

def show_vault_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, service, username, password FROM vault")
    rows = cursor.fetchall()

    headers = ["ID", "Category", "Service", "Username", "Password"]
    print("\n---------- SECURE CREDENTIALS ----------")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

def show_logs_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, event_type, timestamp FROM access_logs")
    rows = cursor.fetchall()

    headers = ["ID", "Action", "Date & Time"]
    print("\n---------- SECURITY ACCESS LOGS ----------")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

def change_key(conn, key):
    cursor = conn.cursor()
    # Change PRAGMA key
    cursor.execute(f"PRAGMA rekey = \"x'{key.hex()}'\";")
    conn.commit()

# ----------------------------------------------
# ---------- CODE TO TEST IF IT WORKS ----------
# ----------------------------------------------
def login():
    auth_store = Path("auth_store.json")
    data = {} if not auth_store.exists() or not auth_store.stat().st_size else loads(auth_store.read_text())

    if all(data.get(key) is None for key in ["hash", "salt"]):
        create_master_password()
    
    master_password = input("Enter Master Password to open SecVault: ").strip()
    key = verify_key(master_password)

    db_conn = initialize_database(key)
    return db_conn

def main(db_conn):
    if db_conn:
        print("\n---------- SECVAULT ----------\n")

        while True: 
            print("\n[A] Add Password | [V] View Vault | [L] View Logs | [M] Change Master Password | [Q] Quit")
            mode = input("Select an option: ").upper()

            match mode:
                case 'A':
                    save_entry(db_conn)
                case 'V':
                    show_vault_table(db_conn)
                case 'L':
                    show_logs_table(db_conn)
                case 'M':
                    new_key = change_master_password()
                    change_key(db_conn, new_key)
                    log_event(db_conn, "LOGOUT")
                    db_conn.close()
                    break
                case 'Q':
                    log_event(db_conn, "LOGOUT")
                    print("\n---------- Vault Locked. Closing Application... ----------")
                    break

        db_conn.close()

if __name__ == "__main__":
    while True:
        db_conn = login()
        main(db_conn)