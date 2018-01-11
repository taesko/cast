import collections
import logging
import os
import pathlib
import shutil

import sys

from cast import conform, exceptions
from cast.template import registry

logger = logging.getLogger(__name__)


class TemplatePath:
    """ Represents a path to a directory inside a template and can be used to
    compute the corresponding path for instances.

    >>> from cast.template.core import Template
    >>> tp = TemplatePath(Template('album_template'), 'some/child/dir')

    Use the method path_for_instance(instance_root) to compute the instance path and return a pathlib.Path obj
    or use __call__ of this object with the same argument.
    >>> tp("path/to/an/instance")
    PosixPath("../path/to/an/instance/some/child/dir")

    The class' instance is iterable and yields all instance paths.
    >>> for instance_path in tp:
    >>>     print(instance_path)
    ../path/to/instance_1/some/child/dir
    ../path/to/instance_2/some/child/dir

    The class' instance compares equal with other's who are from the same template and resolve to the same directory.
    >>> tp == TemplatePath(Template('album_template'), 'some/other_child/../child/dir')
    """

    def __init__(self, template, rel_path):
        """ Initialize with a template object and a relative path.

        Raises ValueError if the joined path of the template's root and rel_path is
        outside the template's root.

        :type template: cast.template.core.Template
        :type rel_path: str
        """
        self.template = template
        self.rel_path = pathlib.PurePath(rel_path)
        joined = pathlib.Path(self.template.path, self.rel_path).resolve()
        if self.template.path not in joined.parents:
            raise ValueError("path is not inside template")
        else:
            self.joined = joined

    def __iter__(self):
        for instance in self.template:
            yield self(instance)

    def __fspath__(self):
        return os.fspath(self.joined)

    def __call__(self, instance_root):
        return self.path_for_instance(instance_root)

    def __eq__(self, other):
        return self.joined == other.joined

    def __repr__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.template, self.rel_path)

    def __str__(self):
        return str(self.joined)

    def exists(self):
        return os.path.exists(self)

    def path_for_instance(self, instance_root):
        return pathlib.Path(instance_root, self.rel_path)


MoveInfo = collections.namedtuple('MoveInfo', ['src', 'dst', 'error'])


def aggregate_all_paths(template_path):
    template = template_path.template
    for instance in template:
        if not conform.is_conformed(dir_path=instance, template_path=template.path):
            raise exceptions.NotConformedDirError(directory=instance, template=template.name)
        yield template_path(instance)


def move(template_src_path, template_dst_path):
    """ Move/rename directories in a template and apply the changes to instances.

    Returns a two tuple of two dictionaries who's keys are the absolute paths to the instances.
    The first dict maps the successfully modified instances to the new path of the moved file.
    The second maps the failed instances to the OSError exception that occurred.

    This function only raises an exception(OSError) if it can't move the directories of
    the template - failures for instances pass silently(but are logged).

    :rtype: dict[str, MoveInfo]
    """
    if not template_src_path.template == template_dst_path.template:
        raise ValueError("Paths aren't from the same template")
    template = template_src_path.template
    for instance in template:
        if not conform.is_conformed(dir_path=instance, template_path=template.path):
            raise exceptions.NotConformedDirError(directory=instance, template=template.name)
    with registry.modify_template_structure(template.name):
        shutil.move(template_src_path, template_dst_path)

    source = template_src_path
    destination = template_dst_path
    result = {}

    for instance in template:
        src = source(instance)
        dst = destination(instance)
        try:
            final_destination = (src, shutil.move(src, dst))
            error = None
        except OSError as e:
            logger.exception("can't move %r to %r", src, dst)
            logger.critical("instance %r of %r is probably no longer conformed", instance, template)
            final_destination = dst
            error = e
        result[instance] = MoveInfo(src=src, dst=final_destination, error=error)
    return result


def _remove(template_path, remove_function, only_in_template):
    template = template_path.template
    with registry.modify_template_structure(template.name):
        remove_function(template_path)
    if only_in_template:
        return {}
    failed = {}
    for instance in template:
        path = template_path(instance)
        try:
            remove_function(path)
        except OSError:
            logger.exception("can't remove %r", path)
            logger.critical("instance %r of template %r is probably no longer conformed", instance, template.name)
            failed[path] = sys.exc_info()
    return failed


def remove(template_path):
    """ Removes a single file from the template."""
    return _remove(template_path, remove_function=os.remove)


def remove_dir(template_path, rmtree=False, only_in_template=False):
    """ Removes a directory from the template directory and in all of it's instances

    :type template_path: TemplatePath
    :type rmtree: bool
    """
    def remove_function(path):
        if rmtree:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
    return _remove(template_path, remove_function=remove_function, only_in_template=only_in_template)


def make_dir(template_path):
    if template_path.exists():
        raise FileExistsError("cannot create directory '{!s}': file exists".format(template_path))
    paths = list(aggregate_all_paths(template_path))
    with registry.modify_template_structure(template_path.template.name):
        os.mkdir(template_path)
    failed = {}
    for path in paths:
        try:
            os.mkdir(path)
        except OSError:
            failed[path] = sys.exc_info()
    return failed
