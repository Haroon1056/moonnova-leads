import random


PROXIES = [
    "http://user:pass@proxy1:port",
    "http://user:pass@proxy2:port",
    "http://user:pass@proxy3:port",
]


def get_random_proxy():
    """
    Rotate proxies to avoid detection
    """
    return random.choice(PROXIES)