import os
import json
import inspect

FST_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))
CONFIG = json.loads(open(os.path.join(FST_DIR, "config.json")).read())
