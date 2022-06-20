import uuid


def get_random_str(length: int) -> str:
    """
    Creates a random string of given length.
    """
    return uuid.uuid4().hex[:length]
