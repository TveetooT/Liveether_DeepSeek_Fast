import logging
import sys
from logging.handlers import RotatingFileHandler
from config import Config

def setup_logging():
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Консольный вывод
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Файловый вывод с ротацией
    file_handler = RotatingFileHandler(
        'logs/bot.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger