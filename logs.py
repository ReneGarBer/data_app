import logging
from functools import wraps
from datetime import datetime

def logs(func):
    @wraps(func)
    def wrapper(*args,**kwargs):
        filename = kwargs.get("logfile","default_log.log")
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
            logger.info(f"{result}")
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            raise
        finally:
            end_time = datetime.now()
            logger.info(f"End time:{end_time}\tDuration: {end_time - start_time}")
            logger.handlers.clear()

    return wrapper