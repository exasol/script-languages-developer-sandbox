
import random
import string


def get_random_str(length: int) -> str:
    """
    Creates a random string of given length.
    """
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str
