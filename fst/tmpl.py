import sqlite3
import os
import hashlib
import signal

from fst.err import *
import fst.dirdiff
import fst.conform
from fst.config import CONFIG


def signal_au_daemon(signum):
    try:
        daemon_pid = int(open(CONFIG['au']['pidfile']).read())
        fst.trace.trace('Auto update daemon pid is: %s', daemon_pid)
    except FileNotFoundError:
        fst.trace.warn('Auto update daemon is not running.')
        daemon_pid = None

    def decorator(func):
        def wrapped(*args, **kwargs):
            result = func(*args, **kwargs)
            if daemon_pid:
                os.kill(daemon_pid, signum)
            return result

        return wrapped

    return decorator


@signal_au_daemon(signal.SIGUSR1)
def connect(cursor, instance_path, template):
    assert template['id']
    assert_user(
        os.path.isdir(instance_path),
        "instance {} is not a directory".format(instance_path),
        "TMPUSRR001",
    )
    assert_user(
        os.path.isdir(template['path']),
        "template {} is not a directory".format(template['path']),
        "TMPUSRR002",
    )
    fst.conform.conform_dir_to_template(
        dir_path=instance_path,
        template_path=template['path']
    )
    try:
        cursor.execute(
            """
                -- use a SELECT statement to guard against concurrency problems.
                INSERT INTO instances (path, template_id)
                    SELECT ?, id FROM templates AS T
                    WHERE T.id=? AND T.active=1
            """,
            [instance_path, template['id']],
        )
    except sqlite3.IntegrityError as e:
        assert_user(
            0,
            "instance with path {} already registed (but might be inactive)"
                .format(instance_path),
            "TMPUSRR003",
            from_exc=e
        )
    assert_user(
        cursor.lastrowid is not None,
        "template {} does not exist.".format(template['name'],
            cursor.rowcount),
        "TMPUSRR004",
    )
    return


@signal_au_daemon(signal.SIGUSR1)
def disconnect(cursor, instance):
    cursor.execute(
        """
        UPDATE instances SET active=0
        WHERE path=? AND active=1
        """,
        [instance],
    )
    assert_user(
        cursor.rowcount,
        "Path {} is not a connected instance.".format(instance),
        "TMPUSRU001",
    )
    return


@signal_au_daemon(signal.SIGUSR1)
def add_template(cursor, path, name):
    assert_user(
        os.path.isdir(path), "{} is not a directory".format(path), "TMPUSRAT001"
    )

    md5_hash = hashlib.md5()
    for p in fst.dirdiff.flattened_subdirs(path):
        md5_hash.update(p.encode("utf-8"))
    checksum = md5_hash.hexdigest()

    try:
        cursor.execute(
            """
                INSERT INTO templates (path, name, checksum)
                VALUES (?, ?, ?)
            """,
            [path, name, checksum],
        )
    except sqlite3.IntegrityError as err:
        assert_user(
            0,
            "Template to path={} or name={} already exists".format(path, name),
            "TMPUSRAT002",
            from_exc=err,
        )

    return


@signal_au_daemon(signal.SIGUSR1)
def rm_template(cursor, path=None, name=None):
    assert path or name
    cursor.execute(
        """
        UPDATE templates SET active=0
        WHERE path=? or name=? AND active=1
        """,
        [path, name],
    )
    assert_user(
        cursor.rowcount,
        "Templates with path={} or name={} does not exist".format(path, name),
        "TMPUSRRT001",
    )


def pull_relationships_by_template(cursor, template=None, instance=None):
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
    templates = {}
    for row in cursor.fetchall():
        template = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("t_")
        }
        instance = {
            col[2:]: row[col]
            for col in row.keys() if col.startswith("i_")
        }
        if all(template['id'] != t for t in templates):
            templates[template['id']] = {
                'template_row': template,
                'instances': {},
            }
        if instance and instance['id'] is not None:
            templates[template['id']]['instances'][instance['id']] = instance

    return templates
