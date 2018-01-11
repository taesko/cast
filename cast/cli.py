import pathlib

import click
import os


import cast.conform
from cast import exceptions, cliprint
from cast.template import registry
from cast.template.core import Template
from cast.template import path as tpath


# TODO fix problems with functions raising uncatched exceptions when working with outdated templates

class CliGroup(click.Group):
    def list_commands(self, ctx):
        """ Override"""
        return ['reg', 'dereg', 'add', 'rm', 'mv', 'conform', 'info']


@click.group(cls=CliGroup)
def cli():
    pass


@cli.command()
@click.argument('name')
@click.argument('dir_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('-c', '--conform-dir/--no-conform-dir',
              help="if the directory does not conform to template - create the missing subdirectories")
def reg(name, dir_path, conform_dir):
    """ Register the directory as an instance of the template with :name:.

    If the directory does not conform to the template's structure this action fails.
    Use the -c/--conform-dir flag to have cast create missing directories."""
    try:
        registry.register_instance(name=name, path=dir_path)
    except exceptions.TemplateNotFoundError:
        raise click.BadParameter("template {!r} doesn't exist".format(name), param_hint='name')
    except exceptions.NotConformedDirError:
        if conform_dir:
            path = Template(name).path
            cast.conform.conform_dir_to_template(dir_path=dir_path, template_path=path)
            registry.register_instance(name=name, path=dir_path)
        else:
            raise click.BadParameter("{!r} is not conformed to template {!r}".format(dir_path, name),
                                     param_hint='dir_path')


@cli.command()
@click.argument('dir_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
def dereg(dir_path):
    """ Deregister the instance from it's template """
    template = Template.for_instance(dir_path)
    if template:
        registry.deregister_instance(name=template.name, path=dir_path)
    else:
        raise click.BadParameter("{!r} is not an instance of any template".format(dir_path),
                                 param_hint='dir_path')


@cli.command()
@click.argument('name')
@click.argument('dir_paths', nargs=-1)
@click.option('-m', '--make-dirs', is_flag=True, default=False,
              help=('interpret the paths after the name argument as subdirectories that '
                    'will be created inside template'))
def add(name, dir_paths, make_dirs):
    """ Add new template/new directories to an existing template.

    The first argument is always the name of a template.
    By default the second argument must be one directory path out of which a template will be made with :name:

    If the -m/--make-dirs flag is raised multiple :dir_paths: arguments can be provided and they will be
    added to the template's structure. The paths must be relative.
    Behaviour is similar to: cd template_root && mkdir dir_path_1 dir_path_2...
    """
    if not dir_paths:
        raise click.BadArgumentUsage("at least one dir_paths argument is required")
    elif make_dirs:
        add_dirs(name=name, dir_paths=dir_paths)
    elif len(dir_paths) > 1:
        raise click.BadParameter("multiple source paths given for template. perhaps you skipped an '-m' flag ?",
                                 param_hint='dir_paths')
    else:
        add_template(name, dir_path=dir_paths[0])


def add_template(name, dir_path):
    try:
        registry.register_template(name=name, path=dir_path)
    except exceptions.TemplateExistsError:
        raise click.BadParameter("a {!r} template already exists.".format(name), param_hint='name')
    except FileNotFoundError:
        raise click.BadParameter("{!r} is not an existing path.".format(dir_path), param_hint='dir_path')
    except NotADirectoryError:
        raise click.BadParameter("{!r} is not a directory.".format(dir_path), param_hint='dir_path')


def add_dirs(name, dir_paths):
    template = Template(name)
    template_paths = (tpath.TemplatePath(template=template, rel_path=dp) for dp in dir_paths)
    for tp in template_paths:
        try:
            failed = tpath.make_dir(template_path=tp)
        except FileExistsError:
            click.echo("ERROR: cannot create '{}': file exists".format(tp))
        else:
            if failed:
                click.echo("WARNING: couldn't create '{}' in every instance".format(tp.rel_path))
                for instance, exc_info in failed.items():
                    _, exc, _ = exc_info
                    click.echo("FAILED for instance '{}': {}".format(instance, exc.strerror))


@cli.command()
@click.argument('name')
@click.argument('rel_paths', nargs=-1)
@click.option('-i', '--in-instances', is_flag=True, default=False,
              help='remove(from) instances as well')
@click.option('-r', '--recurse', is_flag=True, default=False)
def rm(name, rel_paths, in_instances, recurse):
    """ Remove an entire template or it's directories.

    If called with a sole argument :name: it will remove that template and all of it's instances will be untracked.
    When called with additional arguments :rel_paths: it will remove those directories under the template's root.

    The -i/--instances-included flag applies the removal to instances as well - removing their directories or
    deleting them entirely.
    """
    if rel_paths:
        rm_dirs(name=name, rel_paths=rel_paths,
                in_instances=in_instances, recurse=recurse)
    else:
        if click.confirm("You are about to remove the template {!r}. "
                         "It's instances will not be removed but they will be unregistered."
                         "\nDo you want to continue?".format(name),
                         abort=True):
            try:
                registry.deregister_template(name)
            except exceptions.TemplateNotFoundError:
                raise click.BadParameter("template {!r} doesn't exist.".format(name), param_hint='name')


def rm_dirs(name, rel_paths, in_instances=False, recurse=False):
    """ Remove directories specified by :rel_paths: of template with :name:.

    If the :in_instances: flag is raised the removal is also applied to every instance of the template.
    If the :recurse: flag is raised the directory is removed recursively deleting **everything**.
    """

    t = Template(name)
    template_paths = [tpath.TemplatePath(template=t, rel_path=rp) for rp in rel_paths]
    # list comprehension does not contain all files that are removed
    # because contents of directories of instances are not included
    # when the :recurse: flag is raised
    # TODO depending on verbosity print every single file that will be deleted
    if in_instances:
        files_to_remove = [path for tp in template_paths for path in tp]
        files_to_remove.extend(map(pathlib.Path, template_paths))
    else:
        files_to_remove = list(map(pathlib.Path, template_paths))
    files_to_remove.sort()
    click.echo("Files to be deleted:")
    for path in files_to_remove:
        click.echo(path)
    click.confirm(abort=True, text='All the above files will be deleted. This action is not reversible.'
                                   'Are you sure you want to continue?')

    for tp in template_paths:
        try:
            if in_instances:
                failed = tpath.remove_dir(tp, rmtree=recurse, only_in_template=False)
                if failed:
                    click.echo("An error occurred while removing {}".format(tp))
                for instance, error in failed.items():
                    click.echo("FAIL for instance {}. ERROR: {}".format(instance, error.msg))
            else:
                tpath.remove_dir(template_path=tp, rmtree=recurse, only_in_template=True)
        except FileNotFoundError:
            click.echo("ERROR: {} does not exist inside the template".format(tp))
        except NotADirectoryError:
            click.echo("ERROR: {} is not a directory inside the template".format(tp))


@cli.command()
@click.argument('name')
@click.argument('src')
@click.argument('dst')
@click.option('-v', '--verbose', count=True)
def mv(name, src, dst, verbose):
    """ For the template with :name: move the directory at :src: to :dst:.
    All instances of the template get adequately updated

    Both src and dst must be paths relative to the template's root.
    """
    t = Template(name)
    src_tp = tpath.TemplatePath(template=t, rel_path=src)
    dst_tp = tpath.TemplatePath(template=t, rel_path=dst)
    moves = [(os.fspath(src_tp), os.fspath(dst_tp))]
    for a, b in zip(src_tp, dst_tp):
        moves.append((a, b))
    click.echo("You are about to move the following files:")
    for src, dst in moves:
        click.echo("{!r} -> {!r}".format(src, dst))
    c = click.confirm("Do you want to continue?", abort=True)
    assert c
    move_info = tpath.move(src_tp, dst_tp)
    for instance_path, mi in move_info.items():
        if not mi.error and verbose:
            click.echo("moved {!r} to: {!r}".format(mi.src, mi.dst))
        elif mi.error:
            click.echo("FAIL for instance {!r}. ERROR: {}".format(instance_path, mi.error.msg))


@cli.command()
@click.argument('template')
@click.argument('dir_path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('-c', '--check-only', is_flag=True, default=False)
def conform(template, dir_path, check_only):
    """ Conforms the directory to the template's structure"""
    try:
        path = Template(name=template).path
    except exceptions.TemplateNotFoundError as e:
        raise click.BadParameter(message=e.msg, param=template)
    if check_only:
        if cast.conform.is_conformed(dir_path=dir_path, template_path=path):
            click.echo("OK")
        else:
            click.echo("NOT OK")
    else:
        cast.conform.conform_dir_to_template(dir_path=dir_path, template_path=path)


@cli.command()
@click.argument('name')
@click.option('-s', '--structure', type=click.Choice(['tree', 'list', 'none']), default='none',
              help=('print the structure of the object. '
                    'Accepts one of three values which determine the style - tree, list and none'))
@click.option('-p', '--is-path', is_flag=True,
              help="interpret the argument as a path even if a template with such name exists")
@click.option('-r', '--registered', is_flag=True, callback=cliprint.print_registered,
              expose_value=False, is_eager=True,
              help=("print every template and it's registered instances. "
                    "If this option is specified no arguments are required"))
@click.option('-v', '--verbose', 'verbosity', count=True)
def info(name, structure, is_path, verbosity):
    """ Print information about the template or instance."""
    if name in registry.all_template_names() and not is_path:
        cliprint.print_template_status(template_name=name, verbosity=verbosity)
        if structure != 'none':
            path = Template(name).path
            click.echo("")
            cliprint.print_structure(path, structure=structure)
    elif not os.path.exists(name):
        raise click.BadParameter('{!r} is not an existing path'.format(name), param_hint='name')
    elif not os.path.isdir(name):
        raise click.BadParameter('{!r} is not an existing directory'.format(name), param_hint='name')
    else:
        cliprint.print_instance_status(dir_path=name, verbosity=verbosity)
        if structure != 'none':
            click.echo("")
            cliprint.print_structure(dir_path=name, structure=structure)
