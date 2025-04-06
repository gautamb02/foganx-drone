import logging
import os

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.log")

logger = logging.getLogger("Log")
logger.setLevel(logging.DEBUG)  

file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG) 

terminal_handler = logging.StreamHandler()
# terminal_handler.setLevel(logging.WARNING)  # Log WARNING, ERROR, CRITICAL to the terminal
terminal_handler.setLevel(logging.DEBUG)  # Log WARNING, ERROR, CRITICAL to the terminal

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s"
)

file_handler.setFormatter(formatter)
terminal_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(terminal_handler)