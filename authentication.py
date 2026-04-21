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
    auth_store.write_text(dumps({
        "hash": b64encode(key).decode(),
        "salt": b64encode(salt).decode()
    }))
    return key # Return key to decrypt database

# Check if the key to decrypt database is correct
def verify_key(password):
    # If auth_store.json does not exist
    if not auth_store.exists():
        derived_key = store_key(password, salt=token_bytes(16))
    else:
        data = loads(auth_store.read_text())
        derived_key = derive_key(password, b64decode(data["salt"]))

        # Check if entered master password is correct
        try:
            compare_digest(derived_key, b64decode(data["hash"]))
        except ValueError:
            print("Uh oh! Masterpassword is wrong") # Add to GUI as error popup
        
    return derived_key