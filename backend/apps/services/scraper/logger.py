import logging


logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("scraper.log")
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)

handler.setFormatter(formatter)
logger.addHandler(handler)


def log(message):
    logger.info(message)


def error(message):
    logger.error(message)