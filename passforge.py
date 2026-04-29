import secrets 
import string
from zxcvbn import zxcvbn

# Generates passwords using Secrets and String modules
def password_generator():
    alphabet = string.ascii_letters + string.digits
    while True:
        # An alphanumeric password of 20 characters is generated
        password = ''.join(secrets.choice(alphabet) for i in range(20))
        # Checks if the password has atleast one lowercase, one uppercase, and three numericals
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3):
            break

    return password