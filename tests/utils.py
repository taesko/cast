import collections
import pathlib
import os

TEST_DIR = pathlib.Path('tests/td_dir')
TEST_TEMPLATES_DIR = TEST_DIR / 'templates'
TEST_INSTANCES_DIR = TEST_DIR / 'instances'


def flat_from_tree(tree_dict):
    result = []
    for dir_name, sub_tree in tree_dict.items():
        result.append(dir_name)
        if sub_tree:
            for sub_dir_path in flat_from_tree(sub_tree):
                result.append(os.path.join(dir_name, sub_dir_path))
    return result


template_tree = {'empty_root_dir': {},
                 'root_dir': {'empty_nested_dir': {},
                              'nested_dir': {'empty_doubly_nested_dir': {}}}
                 }
conformed_tree = {'empty_root_dir': {},
                  'root_dir': {'empty_nested_dir': {},
                               'extra_empty_nested_dir': {},
                               'nested_dir': {'empty_doubly_nested_dir': {}},
                               'extra_nested_dir': {'extra_empty_doubly_nested_dir': {}}
                               },
                  'extra_empty_root_dir': {},
                  'extra_root_dir': {'extra_empty_nested_dir': {}}
                  }
unconformed_tree = {
    'unconformed_empty_root_dir': {},
    'root_dir': {'unconformed_empty_nested_dir': {},
                 'nested_dir': {'unconformed_empty_doubly_nested_dir': {}}}
}

TestTemplate = collections.namedtuple('TestTemplate', ['name', 'path', 'tree', 'flat'])
TestInstance = collections.namedtuple('TestInstance', ['path', 'tree', 'flat'])
MAIN_TEMPLATE = TestTemplate(name='test_template', path=TEST_TEMPLATES_DIR / 'test_template',
                             tree=template_tree,
                             flat=sorted(flat_from_tree(template_tree)))
CONFORMED_INSTANCE = TestInstance(path=TEST_INSTANCES_DIR / 'test_template' / 'conformed',
                                  tree=conformed_tree,
                                  flat=sorted(flat_from_tree(conformed_tree)))
UNCONFORMED_INSTANCE = TestInstance(path=TEST_INSTANCES_DIR / 'test_template' / 'unconformed',
                                    tree=unconformed_tree,
                                    flat=sorted(flat_from_tree(unconformed_tree)))


def setup_object(obj):
    root = obj.path
    os.makedirs(obj.path, exist_ok=True)
    for path in flat_from_tree(obj.tree):
        os.makedirs(os.path.join(root, path), exist_ok=True)


def setup_all():
    TEST_DIR.mkdir(exist_ok=True)
    TEST_TEMPLATES_DIR.mkdir(exist_ok=True)
    TEST_INSTANCES_DIR.mkdir(exist_ok=True)
    (TEST_INSTANCES_DIR / MAIN_TEMPLATE.name).mkdir(exist_ok=True)
    setup_object(MAIN_TEMPLATE)
    setup_object(CONFORMED_INSTANCE)
    setup_object(UNCONFORMED_INSTANCE)


setup_all()
