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
def store_key(password):
    # Derive key from master password
    salt = token_bytes(32)
    key = derive_key(password, salt)

    # Check if there is data in auth_store.json
    if auth_store.exists() and auth_store.stat().st_size:
        data = loads(auth_store.read_text())
    else:
        data = {}
    
    # Write data into auth_store.json
    data["hash"] = b64encode(key).decode()
    data["salt"] = b64encode(salt).decode()
    auth_store.write_text(dumps(data, indent=4))

    # Return key to decrypt database
    return key


# Check if the key to decrypt database is correct
def verify_key(entered_password):
    data = loads(auth_store.read_text())
    candidate_key = derive_key(entered_password, b64decode(data["salt"])) # Derive entered password

    # Compare candidate key derived from entered password against stored hash (the master password set by the user)
    try:
        compare_digest(candidate_key, b64decode(data["hash"]))
        return candidate_key
    except ValueError:
        print("Uh oh! Masterpassword is wrong") # Add to GUI as error popup


# # Set master password (DEPRECATED)
# def set_master_password(password):
#     key = store_key(password, salt=token_bytes(32))
#     return key