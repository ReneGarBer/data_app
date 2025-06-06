import logging
from functools import wraps
from datetime import datetime

def logs(func):
    @wraps(func)
    def wrapper(*args):
        filename = args[0].config.get("logs","default_log.log")
        logger = logging.getLogger(func.__name__)
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(filename)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(logging.StreamHandler())
        start_time = datetime.now()
        try:
            result = func(*args)
            for logs in result:
                logger.info(logs)
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=False)
            #raise
        finally:
            end_time = datetime.now()
            logger.info(f"Termina - End time:{end_time}\tDuration: {end_time - start_time}")
            logger.handlers.clear()

    return wrapper