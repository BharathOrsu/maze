import logging

class Logger:
    @staticmethod
    def setup():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    @staticmethod
    def log(message, level="info"):
        logger = logging.getLogger()
        getattr(logger, level)(message)
