from json import dumps, loads
from base64 import b64encode, b64decode
from secrets import compare_digest, token_bytes
from pathlib import Path
from argon2.low_level import hash_secret_raw, Type


# Salt and hash values are stored here for verification
auth_store = Path("auth_store.json")

# Derive key from master password
def derive_key(password, salt):
    return hash_secret_raw(
        secret=password.encode(), salt=salt,
        time_cost=2, memory_cost=65536, 
        parallelism=4, hash_len=32, type=Type.ID
    )

# Store key in auth_store.json
def store_key(password, salt):
    key = derive_key(password, salt)
    data = loads(auth_store.read_text()) if auth_store.exists() and auth_store.stat().st_size else {}
    data["hash"] = b64encode(key).decode()
    data["salt"] = b64encode(salt).decode()

    auth_store.write_text(dumps(data, indent=4))
    return key # Return key to decrypt database

# Check if the key to decrypt database is correct
def verify_key(password):
    data = loads(auth_store.read_text())
    derived_key = derive_key(password, b64decode(data["salt"]))

    # Check if entered master password is correct
    try:
        compare_digest(derived_key, b64decode(data["hash"]))
    except ValueError:
        print("Uh oh! Masterpassword is wrong") # Add to GUI as error popup
        
    return derived_key

# Create master password
def create_master_password():
    password = input("Create a Master Password: ").strip()
    key = store_key(password, salt=token_bytes(16))
    return key

# Change master password
def change_master_password():
    data = loads(auth_store.read_text())
    for key in list(data.keys()):
        del data[key]
    key = create_master_password()
    return key