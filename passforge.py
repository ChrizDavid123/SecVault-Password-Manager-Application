import secrets 
import string
from zxcvbn import zxcvbn

# Generates passwords using Secrets and String modules
def password_generator():
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(20)) # An alphanumeric password of 20 characters is generated
        if (any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3):
            break

    return password

# Checks password strength using zxcvbn by Dropbox, a reputable third-party module
def strength_checker(password):
    result = zxcvbn(password)

    match int(result['score']):
        case 0 | 1:
            print("Weak")
        case 2 | 3:
            print("Good")
        case 4:
            print("Strong")