import pathlib
import shutil
import pytest


@pytest.fixture(scope='session', autouse=True)
def test_dir_setup(request):
    td_dir = pathlib.Path('tests/td_dir')

    def cleanup():
        shutil.rmtree(td_dir)

    request.addfinalizer(cleanup)
    return td_dir
