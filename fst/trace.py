import os
import logging


root = logging.getLogger()
root.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(asctime)-15s %(module)s %(lineno)d %(message)s"
)
file_handler = logging.FileHandler(
    filename=os.path.join(os.environ['HOME'], '.fst.log')
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
root.addHandler(file_handler)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

trace = logging.debug
info = logging.info
warn = logging.warn
error = logging.error
exception = logging.exception
