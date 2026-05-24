import random
import time


def human_delay(min_sec=1, max_sec=3):
    time.sleep(random.uniform(min_sec, max_sec))


def random_scroll(page):
    for _ in range(random.randint(3, 7)):
        page.mouse.wheel(0, random.randint(300, 1000))
        human_delay(0.5, 1.5)