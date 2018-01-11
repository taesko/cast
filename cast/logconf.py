import os

CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "brief": {
            "datefmt": "",
            "style": "%"
        },
        "verbose": {
            "format": "%(levelname)s: %(module)s.%(funcName)s - %(message)s",
            "style": "%"
        }
    },
    "handlers": {
        "console_error": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "INFO",
        },
        "file_debug": {
            "class": "logging.FileHandler",
            "filename": os.path.join(os.environ['HOME'], '.cast/logs.txt'),
            "formatter": "verbose",
            "level": "DEBUG"
        },
    },
    "loggers": {
        "cast": {
            "level": "DEBUG",
            "handlers": ["file_debug"]
        }
    }
}
