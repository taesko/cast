import os
import pytest

from fist import exceptions
from fist.template import registry, core

from tests.utils import MAIN_TEMPLATE, CONFORMED_INSTANCE, UNCONFORMED_INSTANCE

if MAIN_TEMPLATE.name not in registry.all_template_names():
    assert os.path.exists(MAIN_TEMPLATE.path)
    registry.register_template(MAIN_TEMPLATE.name, path=MAIN_TEMPLATE.path)


@pytest.mark.parametrize('name, path, error', [
    (MAIN_TEMPLATE.name, MAIN_TEMPLATE.path, exceptions.TemplateExistsError),
    (MAIN_TEMPLATE.name, MAIN_TEMPLATE.path, None),
    (MAIN_TEMPLATE.name + 'not a dir', 'fist/__init__.py', NotADirectoryError),
    (MAIN_TEMPLATE.name + 'not a file', 'not_a_setup.py', FileNotFoundError),
    (MAIN_TEMPLATE.name, 'fist/__init__.py', (NotADirectoryError, exceptions.TemplateExistsError)),
    (MAIN_TEMPLATE.name + 'not a file', 'not_a_setup.py', (FileNotFoundError, exceptions.TemplateExistsError)),
])
def test_template_registration(name, path, error):
    if error:
        with pytest.raises(error):
            registry.register_template(name, path=path)
    else:
        if core.exists(name):
            name = name + 'testing registration'
        with pytest.raises(exceptions.TemplateNotFoundError):
            registry.deregister_template(name)
        registry.register_template(name, path=path)
        assert core.exists(name)
        registry.deregister_template(name)
        assert not core.exists(name)


@pytest.mark.parametrize('name, instance, error', [
    (MAIN_TEMPLATE.name, CONFORMED_INSTANCE.path, None),
    (MAIN_TEMPLATE.name, UNCONFORMED_INSTANCE.path, exceptions.NotConformedDirError),
    ('unexisting template asdfgh', CONFORMED_INSTANCE.path, exceptions.TemplateNotFoundError),
    (MAIN_TEMPLATE.name, 'not_a_real_setup.py', FileNotFoundError),
    (MAIN_TEMPLATE.name, 'fist/__init__.py', NotADirectoryError)
])
def test_instance_registration(name, instance, error):
    if error:
        with pytest.raises(error):
            registry.register_instance(name=name, path=instance)
    elif core.isinstance_(dir_path=instance, name=name):
        registry.deregister_instance(name=name, path=instance)
        assert not core.isinstance_(dir_path=instance, name=name)
        registry.register_instance(name=name, path=instance)
        assert core.isinstance_(dir_path=instance, name=name)
    else:
        registry.register_instance(name=name, path=instance)
        assert core.isinstance_(dir_path=instance, name=name)
        registry.deregister_instance(name=name, path=instance)
        assert not core.isinstance_(dir_path=instance, name=name)
