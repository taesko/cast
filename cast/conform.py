import cast.dirdiff
import os
import os.path


def copy_dir_tree(source_dir_path, destination_dir_path, destination_name):
    relative_subdirs = cast.dirdiff.flattened_subdirs(source_dir_path)
    root_path = os.path.join(destination_dir_path, destination_name)
    os.mkdir(root_path)
    paths = [os.path.join(root_path, rel_path) for rel_path in relative_subdirs]
    for path in paths:
        os.mkdir(path)
    return [root_path, *paths]


def is_conformed(dir_path, template_path):
    return cast.dirdiff.issubset(template_path, dir_path)


def conform_dir_to_template(dir_path, template_path):
    """ Finds the missing directories between directory and template and creates them."""
    dir_path = os.path.abspath(dir_path)
    template_path = os.path.abspath(template_path)
    missing_dirs = cast.dirdiff.missing_from(target=dir_path, origin=template_path, append_to_target=True)
    for dir_path in missing_dirs:
        os.mkdir(dir_path)
    return missing_dirs