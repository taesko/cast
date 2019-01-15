import logging


logging.basicConfig(
    format="%(asctime)-15s %(module)s %(lineno)d %(message)s",
    level=logging.DEBUG,
)

trace = logging.debug
info = logging.info
warn = logging.warn
error = logging.error
exception = logging.exception
