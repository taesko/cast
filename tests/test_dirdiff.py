import os
import pytest

import cast.dirdiff
from tests.utils import MAIN_TEMPLATE, CONFORMED_INSTANCE, UNCONFORMED_INSTANCE


@pytest.mark.parametrize('dir_1,dir_2,output', [
    (MAIN_TEMPLATE.path, CONFORMED_INSTANCE.path, (set(),
                                                   {'empty_root_dir', 'root_dir'},
                                                   {'extra_empty_root_dir', 'extra_root_dir'})),
    (MAIN_TEMPLATE.path, UNCONFORMED_INSTANCE.path, ({'empty_root_dir'},
                                                     {'root_dir'},
                                                     {'unconformed_empty_root_dir'}))
])
def test_difference(dir_1, dir_2, output):
    assert cast.dirdiff.difference(dir_1, dir_2) == output
    assert cast.dirdiff.difference(dir_2, dir_1) == tuple(reversed(output))


@pytest.mark.parametrize('dir_path, output', [
    (MAIN_TEMPLATE.path, sorted(MAIN_TEMPLATE.flat)),
    (CONFORMED_INSTANCE.path, sorted(CONFORMED_INSTANCE.flat)),
    (UNCONFORMED_INSTANCE.path, sorted(UNCONFORMED_INSTANCE.flat)),
    pytest.param('README.md', '',
                 marks=pytest.mark.xfail(raises=NotADirectoryError)),
    pytest.param('README.rst', '',
                 marks=pytest.mark.xfail(raises=FileNotFoundError))
])
def test_flattened_subdirs(dir_path, output):
    assert cast.dirdiff.flattened_subdirs(dir_path, appended=False) == output
    output = sorted(os.path.join(dir_path, p) for p in output)
    assert cast.dirdiff.flattened_subdirs(dir_path, appended=True) == output


@pytest.mark.parametrize('target,origin,output', [
    (CONFORMED_INSTANCE.path, MAIN_TEMPLATE.path, []),
    (UNCONFORMED_INSTANCE.path, MAIN_TEMPLATE.path, sorted(['empty_root_dir',
                                                            'root_dir/empty_nested_dir',
                                                            'root_dir/nested_dir/empty_doubly_nested_dir']))
])
def test_missing_from(target, origin, output):
    assert cast.dirdiff.missing_from(target=target, origin=origin, append_to_target=False) == output


@pytest.mark.parametrize('dir_1,dir_2,output', [
    (MAIN_TEMPLATE.path, CONFORMED_INSTANCE.path, True),
    (MAIN_TEMPLATE.path, UNCONFORMED_INSTANCE.path, False)
])
def test_issubset(dir_1, dir_2, output):
    assert cast.dirdiff.issubset(dir_1, dir_2) == output
