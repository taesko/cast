import argparse
import sqlite3
import os
import sys
import functools

import fst.conform
import fst.db
import fst.dirdiff
import fst.tmpl
from fst.err import *
from fst.trace import trace, info, warn, error


def add(cursor, templates, instances, args):
    fst.tmpl.add_template(
        cursor=cursor,
        path=args.add,
        name=args.template
    )


def remove(cursor, templates, instances, args):
    fst.tmpl.rm_template(
        cursor=cursor,
        path=args.template,
        name=args.template
    )


def connect(cursor, templates, instances, args):
    assert_user(
        len(templates) == 1,
        "template {} does not exist.".format(args.template),
        "CLI-USR-CON-001"
    )
    fst.tmpl.connect(
        cursor=cursor,
        instance_path=args.connect,
        template=templates[0]
    )


def disconnect(cursor, templates, instances, args):
    fst.tmpl.disconnect(
        cursor=cursor,
        instance=args.instance,
        template=args.template
    )


def list_command(cursor, templates, instances, args):
    print_struct = 'struct' in args.list
    print_conformity = 'status' in args.list
    print_relationships = 'rel' in args.list
    info('Executing list command with flags: print_struct=%s '
         'print_conformity=%s print_relationships=%s',
         print_struct,
         print_conformity,
         print_relationships)
    if args.template:
        assert len(templates) == 1
        print_template_info(
            cursor,
            template=templates[0],
            instances=instances,
            print_struct = print_struct,
            print_conformity = print_conformity,
            print_relationships=print_relationships
        )
    elif args.instance:
        assert len(templates) == 1
        assert len(instances) == 1
        print_instance_info(
            cursor,
            template=templates[0],
            instance=instances[0],
            print_struct = print_struct,
            print_conformity = print_conformity,
            print_relationships=print_relationships
        )
    else:
        print_all_info(
            cursor,
            templates=templates,
            instances=instances,
            print_struct=print_struct,
            print_conformity=print_conformity,
            print_relationships=print_relationships
        )


def update(cursor, templates, instances, args):
    for t in templates:
        children = [i for i in instances if i['template_id'] == t['id']]
        for child in children:
            fst.conform.conform_dir_to_template(
                dir_path=child['path'],
                template_path=t['path']
            )

COMMANDS = {
    "add": add,
    "remove": remove,
    "connect": connect,
    "disconnect": disconnect,
    "list": list_command,
    "update": update
}


def print_template_info(cursor, template, instances, print_struct,
                        print_conformity, print_relationships):
    flag_count = sum([print_struct, print_conformity, print_relationships])
    multiple_flags = flag_count > 0
    if print_relationships:
        if multiple_flags:
            print("Instances:")
        for i in instances:
            print(i['path'])
        print("")
    if print_conformity:
        if multiple_flags:
            print("Status of relationships:")
        for i in instances:
            conformed = fst.dirdiff.is_subset(template['path'], i['path'])
            status = {
                True: 'OK',
                False: 'NOT OK'
            }
            print("{} -> {}".format(i['path'], status[conformed]))
        print("")
    if print_struct:
        if multiple_flags:
            print("Structure:")
        for path in fst.fst.dirdiff.flattened_subdirs(template['path']):
            print(path)
        print("")


def print_instance_info(cursor, instance, template, print_conformity,
                        print_struct, print_relationships):
    if print_conformity:
        if fst.dirdiff.is_subset(instance['path'], template['path']):
            print("OK")
        else:
            print("NOT OK")
    if print_struct:
        for path in fst.dirdiff.flattened_subdirs(instance['path']):
            print(path)


def print_all_info(cursor, templates, instances, print_conformity, print_struct,
                   print_relationships):
    for t in templates:
        children = [i for i in instances if i['template_id'] == t['id']]
        print("{} ({}) -> {}".format(t['name'], t['path'], ' : '.join(children)))


def pull_relationships(cursor, template, instance):
    pull_all = not template and not instance
    cursor.execute(
        """
        SELECT
            T.id AS t_id,
            T.name AS t_name,
            T.path AS t_path,
            T.checksum AS t_checksum,
            T.active AS t_active,
            I.id AS i_id,
            I.path AS i_path,
            I.template_id AS i_template_id,
            I.active AS i_active
        FROM templates AS T
        LEFT JOIN instances AS I ON T.id=I.template_id
        WHERE
            T.active=1 AND
            (I.active=1 OR I.active IS NULL) AND
            (T.path = ?  OR T.name = ?  OR I.path = ? OR true=?)
        """,
        [template, template, instance, pull_all],
    )
    templates = []
    instances = []
    for row in cursor.fetchall():
        template = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("t_")
        }
        instance = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("i_")
        }
        if all(template['id'] != t['id'] for t in templates):
            templates.append(template)
        if instance and instance['id'] is not None:
            for other_instance in instances:
                assert other_instance["id"] != instance["id"]
            instances.append(instance)
    trace("Templates: %r", templates)
    trace("Instances: %r", instances)

    return {
        'templates': templates,
        'instances': instances
    }


def main():
    parser = argparse.ArgumentParser(
        description="Modify multiple directories through the use of templates."
    )
    parser.add_argument(
        "-i",
        "--instance",
        help="Path to instance."
    )
    parser.add_argument(
        "-t",
        "--template",
        help="Path or name of template."
    )
    parser.add_argument(
        "-l",
        "--list",
        choices=["struct", "status", "rel"],
        action="append",
        help="List structure.",
    )
    parser.add_argument(
        "-a",
        "--add",
        help="Add a new template from path. The -t argument specifies the name."
    )
    parser.add_argument(
        "-r",
        "--remove",
        help="Remove the template.",
        action='store_true'
    )
    parser.add_argument("--rename", help="Set name of template.")
    parser.add_argument(
        "-c",
        "--connect",
        help=(
            "Connects a template to a path. The -t argument provides the"
            " template. This flag's argument must be path to an instance."),
    )
    parser.add_argument(
        "-d",
        "--disconnect",
        help="Remove a relationship between target and arg.",
    )
    parser.add_argument(
        "-u",
        "--update",
        action='store_true',
        help="If target is a template all of it's instances"
        "are updated. Otherwise if it's an instance it alone"
        "is updated to it's template.",
    )
    parser.add_argument(
        "--hook",
        nargs=argparse.REMAINDER,
        help="Execute a command hook.",
    )

    args = parser.parse_args()
    trace("Command line args: %r", args)
    if not (args.template or args.instance) and not args.list:
        parser.error("A template or instance needs to be specified.")

    try:
        cursor = fst.db.conn.cursor()
        rels = pull_relationships(
            cursor,
            template=args.template,
            instance=args.instance
        )
    except fst.err.FSTErr as err:
        fst.trace.exception('Error occurred. User input is: %r', args)
        parser.error('{}({})'.format(err.msg, err.code))
    except BaseException as exc:
        fst.trace.exception('Unhandled exception. User input is: %r', args)
        parser.error('An unknown error occurred. Please view the logs and/or'
                     'submit a ticket with them.')

    templates = rels['templates']
    instances = rels['instances']

    for arg_name in vars(args):
        if (arg_name in ("instance", "template") or
            not getattr(args, arg_name, None)):
            continue

        try:
            cursor.execute("BEGIN")
            info("Command to run is: %s", arg_name)
            COMMANDS[arg_name](
                cursor=cursor,
                instances=instances,
                templates=templates,
                args=args
            )
            cursor.execute("COMMIT")
        except Exception as exc:
            cursor.execute("ROLLBACK")
            error("User command failed.", exc_info=exc)
            msg = getattr(exc, "msg", 'Unknown error occurred.')
            code = getattr(exc, "code", "CLIUNHANDLED")
            print("Error: {} ({})".format(msg, code))
            sys.exit(1)

    if args.hook:
        print("Error: Not implemented. (CLI002)", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
