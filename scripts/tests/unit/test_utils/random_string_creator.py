import random
import string


def get_random_string(length):
    """
    Creates a random lowercase string.
    :param length: int - length of the string.
    :return: string - random ascii lowercase string
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))










