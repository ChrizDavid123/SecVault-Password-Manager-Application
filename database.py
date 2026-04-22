# Current Master Password: ninja
# To change master password, delete the SecVault.db file first, otherwise whatever password you input, it wont work!


# -----------------------------------------------
# ---------- MAIN SQL DATABASE PROGRAM ----------
# -----------------------------------------------
from pathlib import Path
from sqlcipher3 import dbapi2 as sqlite
from tabulate import tabulate
from datetime import datetime
from authentication import verify_key, set_master_password

def initialize_database(key):
    """Initializes and returns the connection to the encrypted database."""
    try:
        conn = sqlite.connect('SecVault.db')
        cursor = conn.cursor()
        
        # Set the encryption key
        cursor.execute(f"PRAGMA key = \"x'{key.hex()}'\";")

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
    """Saves a new entry with a standardized category."""
    categories = {
        "1": "Work",
        "2": "Personal",
        "3": "Wifi"
    }

    print("\n--- Select Category ---")
    for key, value in categories.items():
        print(f"[{key}] {value}")

    cat_choice = input("Select category (1-3): ").strip()
    category = categories.get(cat_choice, "Personal")

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
        print(f"\n[!] Securely saved {service} under {category}.")
    except Exception as e:
        print(f"Failed to save: {e}")

def show_vault_table(conn):
    print("\n---------- View Options ----------")
    print("[1] Work | [2] Personal | [3] WiFi | [4] All Passwords")
    choice = input("Selection: ").strip()

    filter_map = {"1": "Work", "2": "Personal", "3": "WiFi"}

    cursor = conn.cursor()

    if choice == "4":
        cursor.execute("SELECT id, category, service, username, password FROM vault")
        title = "ALL REGISTERED PASSWORDS"
    elif choice in filter_map:
        selected = filter_map[choice]
        cursor.execute("SELECT id, category, service, username, password FROM vault WHERE category = ?", (selected,))
        title = f"{selected.upper()} PASSWORDS"
    else: 
        print("Invalid selection. Returning to main menu.")
        return 
    
    rows = cursor.fetchall()
    headers = ["ID", "Category", "Service", "Username", "Password"]
    print("\n---------- {title} ----------")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

def show_logs_table(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, event_type, timestamp FROM access_logs")
    rows = cursor.fetchall()

    headers = ["ID", "Action", "Date & Time"]
    print("\n---------- SECURITY ACCESS LOGS ----------")
    print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))

def change_key(conn):
    key = set_master_password()
    cursor = conn.cursor()
    # Change PRAGMA key
    cursor.execute(f"PRAGMA rekey = \"x'{key.hex()}'\";")
    conn.commit()

def delete_entry(conn):
    """Removes a specific credential by ID."""
    target_id = input("Enter the ID of the entry to delete: ")
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vault WHERE id = ?", (target_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Entry {target_id} deleted successfully.")
        else:
            print("ID not found.")
    except Exception as e:
        print(f"Error: {e}")

def update_entry(conn):
    """Updates the password for a specific service."""
    target_id = input("Enter the ID of the entry to update: ")
    new_password = input("Enter new password: ")
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE vault SET password = ? WHERE id = ?", (new_password, target_id))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Entry {target_id} updated.")
        else:
            print("ID not found.")
    except Exception as e:
        print(f"Error: {e}")
# ----------------------------------------------
# ---------- CODE TO TEST IF IT WORKS ----------
# ----------------------------------------------
# Code below will be adapted to the front-end design
def login():
    auth_store = Path("auth_store.json")

    # User sets master password if hash and salt values are not found in auth_store.json
    if not auth_store.exists() or not auth_store.stat().st_size:
        key = set_master_password()
    else:
        master_password = input("Enter master password to open SecVault: ").strip()
        key = verify_key(master_password)

    db_conn = initialize_database(key)
    return db_conn

def main(db_conn):
    if db_conn:
        print("\n---------- SECVAULT ----------\n")

        while True: 
            print("\n[A] Add | [V] View | [U] Update | [D] Delete | [M] Change Master | [Q] Quit")
            mode = input("Select an option: ").upper()

            match mode:
                case 'A':
                    save_entry(db_conn)
                case 'V':
                    show_vault_table(db_conn)
                case 'U':
                    update_entry(db_conn)
                case 'D':
                    delete_entry(db_conn)
                case 'M':
                    change_key(db_conn)
                    break

        db_conn.close()

if __name__ == "__main__":
    while True:
        db_conn = login()
        main(db_conn)