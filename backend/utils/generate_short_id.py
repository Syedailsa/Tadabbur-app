import random
import string

def generate_short_id() -> str:
    # This is the closest equivalent to Math.random().toString(36)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
