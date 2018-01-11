import os
import pathlib
import logging.config

import cast.logconf

CAST_DIR = pathlib.Path(os.environ['HOME'], '.cast')
CAST_DIR.mkdir(exist_ok=True)

logging.config.dictConfig(cast.logconf.CONFIG)

