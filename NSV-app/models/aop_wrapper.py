import time
import logging
from functools import wraps
from abc import ABC

logging.basicConfig(
    filename='logs.txt',
    level=logging.INFO,      
    format='%(asctime)s - %(levelname)s - %(message)s'  
)

class Aspect:
   
    @staticmethod
    def log_execution(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
           
            class_name = args[0].__class__.__name__
            arg_str = ', '.join([str(a) for a in args[1:]] + 
                                [f"{k}={v}" for k, v in kwargs.items()])
            logging.info(f"Executing {class_name}.{func.__name__} with arguments: {arg_str}")
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def measure_time(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            logging.info(f"{func.__name__} took {end_time - start_time:.4f} seconds")
            return result
        return wrapper

    @staticmethod
    def handle_exceptions(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Exception in {func.__name__}: {e}")
                return None
        return wrapper
