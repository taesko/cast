import logging
import os
import subprocess
import sys

import click

from cast import dirdiff
from cast.template import core


logger = logging.getLogger(__name__)


def print_registered(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    for t in core.Template.all():
        click.echo('{} -> {}'.format(t.name, ':'.join(t.instances)))
    ctx.exit()


def print_tree(dir_path):
    """ Print the directory tree in a pretty format."""
    if not os.path.exists(dir_path):
        raise FileNotFoundError("dir_path {} doesn't exist".format(dir_path))
    elif not os.path.isdir(dir_path):
        raise NotADirectoryError("dir_path {} is not a valid directory".format(dir_path))
    try:
        subprocess.run(["tree", str(dir_path)], stdout=sys.stdout)
    except OSError as e:
        logger.exception("Couldn't execute 'tree' command")
        # very ugly implementation
        # TODO prettify
        lines = []
        for rel_subdir in dirdiff.flattened_subdirs(dir_path):
            indent = 2 + 2 * rel_subdir.count(os.path.sep)
            fill = '-'
            name = os.path.basename(rel_subdir)
            lines.append("{} {}".format(fill * indent, name))
        click.echo('\n'.join(lines))


def print_dir_listing(dir_path):
    """ Print the directory contents in a pretty format."""
    if not os.path.exists(dir_path):
        raise FileNotFoundError("dir_path {} doesn't exist".format(dir_path))
    elif not os.path.isdir(dir_path):
        raise NotADirectoryError("dir_path {} is not a valid directory".format(dir_path))
    subprocess.run(["ls", dir_path], stdout=sys.stdout)


def print_structure(dir_path, structure='tree'):
    click.echo("Structure:\n")
    if structure == 'tree':
        print_tree(dir_path=dir_path)
    elif structure == 'list':
        print_dir_listing(dir_path=dir_path)
    else:
        raise ValueError("Unrecognized parameter {} for argument :structure".format(structure))


def print_template_status(template_name, verbosity=0):
    status = core.Status(name=template_name)
    click.echo("Conformity: {}, Hash: {}".format(status.conformity_status(), status.hash_status()))
    if verbosity:
        click.echo("Instances:\n")
        for instance, st_code in status:
            click.echo("\t'{}': {}".format(instance, st_code))


def print_instance_status(dir_path, verbosity=0):
    status_code = core.Status.of_instance(dir_path)
    if verbosity:
        template = core.Template.for_instance(dir_path)
        msg = "Template {}: {}".format(template.name, status_code)
    else:
        msg = status_code
    click.echo(msg)
