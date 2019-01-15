import os
import os.path
import collections

ContentDiff = collections.namedtuple("ContentDiff", ["left", "common", "right"])


def difference(dir_1, dir_2):
    """ Returns the difference between two directories.

    The return value is a namedtuple with 'left', 'common' and 'right' fields
    specifying the paths only in the left argument, in both and only in the
    right one respectively.
    """
    left_contents = set(
        p for p in os.listdir(dir_1) if os.path.isdir(os.path.join(dir_1, p))
    )
    right_contents = set(
        p for p in os.listdir(dir_2) if os.path.isdir(os.path.join(dir_2, p))
    )
    common_names = left_contents.intersection(right_contents)
    left_contents -= common_names
    right_contents -= common_names

    return ContentDiff(left_contents, common_names, right_contents)


def is_subset(dir_1, dir_2):
    """ Returns a boolean whether a directory's entire structure is in another.

    Check is purely path based.
    """
    diff = difference(dir_1, dir_2)
    if not diff.left:
        return True
    elif diff.common == diff.left:
        for name in diff.common:
            left_path = os.path.join(dir_1, name)
            right_path = os.path.join(dir_2, name)
            if not is_subset(left_path, right_path):
                return False
        return True
    else:
        return False


def missing_from(target, origin, append_to_target=False):
    """ Returns a list of paths to directories that origin has,
    but :target: does not.

    By default the paths are relative but if the absolute flag is True
    they are appended to the target path.

    The list is sorted in ascending order and if the :append_to_target: flag is
    set to True it can be safely fed in sequence to os.mkdir to make the target
    directory a superset of origin.
    """
    missing = set(flattened_subdirs(origin)) - set(flattened_subdirs(target))
    if append_to_target:
        result = sorted(os.path.join(target, p) for p in missing)
    else:
        result = sorted(missing)
    return result


def flattened_subdirs(directory, appended=False):
    """ Returns a sorted and unnested list of all subdirectories under the root.

    The paths may or may not be relative - depending on the passed argument.
    They are simply appended to it so a relative argument yields relative paths
    to the current working directory and an absolute, absolute paths.
    """

    def implementation(dir_path):
        sd = []
        for name in sorted(os.listdir(dir_path)):
            path = os.path.join(dir_path, name)
            if os.path.isdir(path):
                sd.append(path)
                sd.extend(implementation(path))
        return sd

    if appended:
        return implementation(dir_path=directory)
    else:
        return [
            os.path.relpath(path=p, start=directory)
            for p in implementation(directory)
        ]
