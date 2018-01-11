import contextlib
import hashlib
import json
import logging
import os
import pathlib

import shutil

from cast import exceptions, dirdiff, conform, CAST_DIR

CONFIG_FILE = CAST_DIR / 'config.json'
TEMPLATE_DIR = CAST_DIR / 'templates'
TEMPLATE_DIR.mkdir(exist_ok=True)
logger = logging.getLogger(__name__)


# TODO keep the template directory and the config file synced


def load_json():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, mode='r') as f:
            return json.load(f)
    else:
        return {}


def dump_json(obj):
    with open(CONFIG_FILE, mode='w') as f:
        json.dump(obj, f)


def register_template(name, path):
    # TODO do not register duplicates
    def cleanup():
        """ Things went wrong"""
        templ_path = template_path(name)
        if os.path.isdir(templ_path):
            logger.warning("removing template folder of %s", name)
            shutil.rmtree(templ_path)

    if name in all_template_names():
        raise exceptions.TemplateExistsError(template_name=name)
    try:
        copied_root = conform.copy_dir_tree(source_dir_path=path,
                                            destination_dir_path=TEMPLATE_DIR, destination_name=name)[0]
    except Exception:
        logger.exception("can't copy dir tree from %s to template folder", path)
        cleanup()
        raise
    assert os.path.normpath(template_path(name)) == os.path.normpath(copied_root)
    try:
        hash_ = template_hash(name)
        instances = []
        all_templates = load_json()
        obj = {'hash': hash_, 'instances': []}
        all_templates[name] = obj
        dump_json(all_templates)
    except Exception:
        logger.exception("unknown exception occurred while registering template %s in the config file", name)
        cleanup()
        raise
    else:
        logger.info("registered new template %s from %s with hash %s and instances %s", name, path, hash_, instances)


def deregister_template(name):
    if name not in all_template_names():
        raise exceptions.TemplateNotFoundError(name)
    shutil.rmtree(TEMPLATE_DIR / name)
    all_templates = load_json()
    del all_templates[name]
    dump_json(all_templates)
    logger.info("unregistered template %s", name)


def register_instance(name, path):
    # TODO do not register the template as it's own instance
    # TODO do not register an instance of another template
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError("instance {} is not an existing path".format(path))
    elif not os.path.isdir(path):
        raise NotADirectoryError("instance {} is not a directory".format(path))
    elif name not in all_template_names():
        raise exceptions.TemplateNotFoundError(name)
    elif not conform.is_conformed(dir_path=path, template_path=TEMPLATE_DIR / name):
        raise exceptions.NotConformedDirError(directory=path, template=name)
    else:
        with modify_template_config(name) as dct:
            if path not in dct['instances']:
                dct['instances'].append(path)
                dct['instances'].sort()
                logger.info("registered new instance %s for template %s", path, name)
            else:
                logger.info("attempted to register %s for template %s but it was already registered", path, name)


def deregister_instance(name, path):
    path = os.path.abspath(path)
    if name not in all_template_names():
        raise exceptions.TemplateNotFoundError(name)
    with modify_template_config(name) as dct:
        try:
            dct['instances'].remove(path)
        except ValueError:
            logger.warning("failed to deregister instance %s of template %s. instance was not registered", path, name)
        else:
            logger.info("unregistered instance %s of template %s", path, name)


def all_template_names():
    """ Returns a list of all template names

    :rtype: list[str]
    """
    return load_json().keys()


def template_path(name):
    return TEMPLATE_DIR / name


def template_config(name):
    """ Returns a dict of the template's configuration

    The dict has 2 string keys:
    hash - the hash of the templates' directory structure
    instances - a list of paths to the instances of the template

    :type name: str
    :rtype: dict
    """
    all_templates = load_json()
    if name not in all_templates:
        raise exceptions.TemplateNotFoundError(template_name=name)
    return all_templates[name]


@contextlib.contextmanager
def modify_template_config(name):
    """ Context manager that yields a dict of the template's configuration and saves any changes to it.

    :type name: str
    :rtype: dict
    """
    if name not in all_template_names():
        raise exceptions.TemplateNotFoundError(name)
    all_templates = load_json()
    logger.info("opening config of template %s for modification. current state: %s", name, all_templates[name])
    yield all_templates[name]
    logger.info("updating config of template %s to %s", name, all_templates[name])
    dump_json(all_templates)


@contextlib.contextmanager
def modify_template_structure(name):
    path = template_path(name)
    pre_mod = [os.path.join(path, p) for p in dirdiff.flattened_subdirs(path)]
    try:
        yield path
    except Exception:
        logger.exception("an exception occurred while modifying structure of template %s", name)
        logger.info("rolling back the template structure to: %s", pre_mod)
        shutil.rmtree(str(path))
        logger.info("removed template tree. recreating pre-modification one...")
        os.mkdir(path)
        for subdir in pre_mod:
            os.mkdir(subdir)
        logger.info("rollback successful.")
        raise
    update_template_hash(name)


def update_template_hash(name):
    """ Updates the directory tree hash of the template in the config file

    :param name: name of the template
    """
    with modify_template_config(name) as dct:
        dct['hash'] = template_hash(name)
        logger.info("updated hash of template %s", name)


def template_hash(name):
    """ Returns the hash of the directory tree of the template

    :type name: str
    :rtype: str
    """
    dir_path = template_path(name)
    dirs = dirdiff.flattened_subdirs(dir_path)
    tree_string = ''.join(dirs)
    return hashlib.sha1(tree_string.encode('utf-8')).hexdigest()
