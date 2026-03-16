import uuid
import string

ALPHABET = string.ascii_uppercase + string.digits
BASE = len(ALPHABET)

def generate_order_code():
    num = uuid.uuid4().int

    code = []
    for _ in range(6):
        num, rem = divmod(num, BASE)
        code.append(ALPHABET[rem])

    return ''.join(code)