import sqlite3
import os
import hashlib

from fst.err import *
import fst.dirdiff
import fst.conform


def register(cursor, instance_path, template):
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


def deregister(cursor, instance):
    cursor.execute(
        """
        UPDATE instances SET active=0
        WHERE path=? AND active=1
        """,
        [instance],
    )
    assert_user(
        cursor.rowcount,
        "No registered instance to path {}".format(instance),
        "TMPUSRU001",
    )
    return


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
            "Template to path=? or name=? already exists".format(path, name),
            "TMPUSRAT002",
            from_exc=err,
        )

    return


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
        "Templates with path=? or name=? does not exist".format(path, name),
        "TMPUSRRT001",
    )
