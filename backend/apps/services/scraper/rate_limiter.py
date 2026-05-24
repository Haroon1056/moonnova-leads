import time


class RateLimiter:
    """
    Prevents abuse of scraping system per user
    """

    def __init__(self):
        self.user_last_run = {}

    def allow(self, user_id, delay=5):
        now = time.time()

        if user_id in self.user_last_run:
            if now - self.user_last_run[user_id] < delay:
                return False

        self.user_last_run[user_id] = now
        return True