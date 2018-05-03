import logging
import os
import pathlib

logging.getLogger().setLevel(logging.DEBUG)
logging.basicConfig(format='{levelname}: {message}', style='{')


def get_real_file(path, default_text=''):
    if os.path.isfile(path):
        if os.access(path, os.R_OK | os.W_OK):
            return path
        else:
            raise PermissionError(f"can't read/write to {path} - insufficient permissions")
    else:
        if os.access(path.parent, os.R_OK | os.W_OK):
            path.write_text(default_text, encoding='ascii')
            return path
        else:
            raise PermissionError(f"can't create file {path} - insufficient permissions")


def get_real_dir(path):
    if os.path.isdir(path):
        if os.access(path, os.R_OK | os.W_OK):
            return path
        else:
            raise PermissionError(f"can't read/write to {path} - insufficient permissions")
    else:
        if os.access(path.parent, os.R_OK | os.W_OK):
            path.mkdir()
            return path
        else:
            raise PermissionError(f"can't create directory {path} - insufficient permissions")


USER_HOME = pathlib.Path(os.environ['HOME'])
USER_CONFIG_DIR = get_real_dir(pathlib.Path(os.environ.get('XDG_CONFIG_HOME', USER_HOME / '.config')) / 'fscast')
USER_CONFIG_FILE = get_real_file(USER_CONFIG_DIR / 'config.json', default_text='{}')
USER_TEMPLATE_DIR = get_real_dir(USER_CONFIG_DIR / 'templates')
LOG_FILE = get_real_file(USER_CONFIG_DIR / 'backup.log')
LOG_FILE_HANDLER = logging.FileHandler(filename=LOG_FILE)
LOG_FILE_HANDLER.setFormatter(logging.Formatter(fmt="{module}.{funcName} {lineno} {levelname} - {message}", style='{'))
LOG_FILE_HANDLER.setLevel(logging.DEBUG)
logging.getLogger().addHandler(LOG_FILE_HANDLER)
