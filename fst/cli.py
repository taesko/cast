import argparse
import sqlite3
import os
import sys
import functools

import fst.tmpl
import fst.db
from fst import dirdiff
from fst.trace import trace, info, warn, error


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
            conformed = dirdiff.is_subset(template['path'], i['path'])
            print("{} -> {}".format(i['path'], conformed))
        print("")
    if print_struct:
        if multiple_flags:
            print("Structure:")
        for path in fst.dirdiff.flattened_subdirs(template['path']):
            print(path)
        print("")


def print_instance_info(cursor, instance, template, print_conformity,
                        print_struct, print_relationships):
    if print_conformity:
        if dirdiff.is_subset(instance['path'], template['path']):
            print("OK")
        else:
            print("NOT OK")
    if print_struct:
        for path in fst.dirdiff.flattened_subdirs(instance['path']):
            print(path)


def add(cursor, templates, instances, args):
    fst.tmpl.add_template(
        cursor=cursor,
        path=args.template,
        name=args.add
    )


def remove(cursor, templates, instances, args):
    fst.tmpl.rm_template(
        cursor=cursor,
        path=args.template,
        name=args.template
    )


def connect(cursor, templates, instances, args):
    assert_user(len(templates) == 1,
                "template {} does not exist.".format(template['name']),
                "CLI-USR-CON-001")
    fst.tmpl.register(
        cursor=cursor,
        instance_path=args.connect,
        template=templates[0]
    )


def disconnect(cursor, templates, instances, args):
    fst.tmpl.deregister(
        cursor=cursor,
        instance=args.instance,
        template=args.template
    )


def list_command(cursor, templates, instances, args):
    print_struct = 'struct' in args.list
    print_conformity = 'status' in args.list
    print_relationships = 'rel' in args.list
    info('Executing list command with flags: print_struct=%s '
         'print_conformity=%s print_relationships=%s and '
         'target=%s',
         print_struct,
         print_conformity,
         print_relationships,
         'template' if args.template else 'instance')
    if args.template:
        print_template_info(
            cursor,
            template=templates[0],
            instances=instances,
            print_struct = print_struct,
            print_conformity = print_conformity,
            print_relationships=print_relationships
        )
    elif args.instance:
        print_instance_info(
            cursor,
            instance=instances[0],
            template=templates[0],
            print_struct = print_struct,
            print_conformity = print_conformity,
            print_relationships=print_relationships
        )
    else:
        assert 0


COMMANDS = {
    "add": add,
    "remove": remove,
    "connect": connect,
    "disconnect": disconnect,
    "list": list_command
}


def cli():
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
    parser.add_argument("-a", "--add", help="Add a new template with name.")
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
        help=("Register a relationship between target and arg. "
              "Arg can be a path or a name of a template."),
    )
    parser.add_argument(
        "-d",
        "--disconnect",
        help="Remove a relationship between target and arg.",
    )
    parser.add_argument(
        "-u",
        "--update",
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
    if not (args.template or args.instance):
        parser.error("A template or instance needs to be specified.")

    cursor = fst.db.conn.cursor()
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
            (T.path = ?  OR T.name = ?  OR I.path = ?)
        """,
        [args.template, args.template, args.instance],
    )
    templates = []
    instances = []
    for row in cursor.fetchall():
        trace('row keys and values of main select: %s, %s', row.keys(), tuple(row))
        template = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("t_")
        }
        instance = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("i_")
        }
        templates.append(template)
        if instance['id']:
            for other_instance in instances:
                if other_instance["id"] == instance["id"]:
                    break
            else:
                instances.append(instance)
    trace("Templates: %r", templates)
    trace("Instances: %r", instances)
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
            msg = getattr(exc, "msg", exc.args[0])
            code = getattr(exc, "code", "CLI001")
            print("Error: {} ({})".format(msg, code))
            sys.exit(1)

    if args.hook:
        print("Error: Not implemented. (CLI002)", file=sys.stderr)
        sys.exit(1)
