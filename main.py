import os
from aiohttp import web
from web.app import create_app
from config import Config
import logging
from logger_config import setup_logging

def main():
    # Создаём папку logs
    os.makedirs("logs", exist_ok=True)
    logger = setup_logging()
    logger.info("Запуск бота Livether")

    app = create_app()
    port = Config.PORT
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()