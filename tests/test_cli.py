import pathlib

import pytest
from click.testing import CliRunner

from fist import cli, conform
from fist.template import registry
from fist.template import path as tpath
from fist.template.core import Template
from fist.template import core as tcore
from tests.utils import MAIN_TEMPLATE, CONFORMED_INSTANCE, UNCONFORMED_INSTANCE


@pytest.fixture(scope='function', autouse=True)
def setup():
    if MAIN_TEMPLATE.name not in registry.all_template_names():
        registry.register_template(MAIN_TEMPLATE.name, MAIN_TEMPLATE.path)
    if CONFORMED_INSTANCE not in Template(MAIN_TEMPLATE.name):
        registry.register_instance(MAIN_TEMPLATE.name, CONFORMED_INSTANCE.path)


ADD_ERROR = "Usage: add [OPTIONS] NAME [DIR_PATHS]...\n\nError: Invalid value for {hint}: {msg}\n"


@pytest.mark.parametrize('name,dir_paths,output', [
    (MAIN_TEMPLATE.name, [str(MAIN_TEMPLATE.path)],
     ADD_ERROR.format(hint='name', msg="a {!r} template already exists.".format(MAIN_TEMPLATE.name))),
    (MAIN_TEMPLATE.name + 'qwertyasdfgh', ['fist/__init__.py'],
     ADD_ERROR.format(hint='dir_path', msg="{!r} is not a directory.".format('fist/__init__.py'))),
    ('qwerty', ['not_a_real_setup.py'],
     ADD_ERROR.format(hint='dir_path', msg="{!r} is not an existing path.".format('not_a_real_setup.py')))
])
def test_add_template(name, dir_paths, output):
    runner = CliRunner()
    result = runner.invoke(cli.add, [name, *dir_paths])
    assert result.output == output


def test_add_dirs():
    pass


REG_ERROR = "Usage: reg [OPTIONS] NAME DIR_PATH\n\nError: Invalid value for {hint}: {msg}\n"


@pytest.mark.parametrize('name,dir_path,output', [
    (MAIN_TEMPLATE.name, 'fist',
     REG_ERROR.format(hint='dir_path',
                      msg="{!r} is not conformed to template {!r}".format('fist', MAIN_TEMPLATE.name)))
])
def test_reg(name, dir_path, output):
    runner = CliRunner()
    result = runner.invoke(cli.reg, [name, dir_path])
    assert result.output == output


DEREG_ERROR = "Usage: dereg [OPTIONS] DIR_PATH\n\nError: Invalid value for {hint}: {msg}\n"


@pytest.mark.parametrize('dir_path, output', [
    (str(UNCONFORMED_INSTANCE.path),
     DEREG_ERROR.format(hint='dir_path',
                        msg="{!r} is not an instance of any template".format(str(UNCONFORMED_INSTANCE.path))))
])
def test_dereg(dir_path, output):
    runner = CliRunner()
    result = runner.invoke(cli.dereg, [dir_path])
    assert result.output == output


def test_conform():
    test_conform_dir = pathlib.Path('tests/td_dir/instances/test_conform')
    test_conform_dir.mkdir()
    t_name = MAIN_TEMPLATE.name
    instance_1 = (test_conform_dir / 'instance_1')
    instance_1.mkdir(exist_ok=True)
    runner = CliRunner()
    runner.invoke(cli.conform, [t_name, str(instance_1)])
    assert conform.is_conformed(dir_path=instance_1, template_path=MAIN_TEMPLATE.path)


@pytest.fixture(scope='session')
def tcli_mv_dir():
    test_mv_dir = pathlib.Path('tests/td_dir/test_cli_mv')
    test_mv_dir.mkdir()
    return test_mv_dir


@pytest.fixture(scope='session')
def tcli_mv_template(tcli_mv_dir):
    name = MAIN_TEMPLATE.name + 'test_cli_mv'
    src_path = MAIN_TEMPLATE.path
    instances = [tcli_mv_dir / 'instance_1']
    registry.register_template(name=name, path=src_path)
    for path in instances:
        path.mkdir()
        conform.conform_dir_to_template(dir_path=path, template_path=registry.template_path(name))
        registry.register_instance(name=name, path=path)
    yield name
    registry.deregister_template(name=name)


# noinspection PyUnusedLocal
@pytest.mark.parametrize('src, dst', [
    ('empty_root_dir', 'moved_empty_root_dir')
])
def test_mv(src, dst, tcli_mv_dir, tcli_mv_template):
    template = Template(tcli_mv_template)
    tp_src = tpath.TemplatePath(template=template, rel_path=src)
    tp_dst = tpath.TemplatePath(template=template, rel_path=dst)
    for instance in template:
        assert tp_src(instance).exists()
        assert not tp_dst(instance).exists()
    runner = CliRunner()
    result = runner.invoke(cli.mv, [tcli_mv_template, src, dst, '-v'], input='y')
    output_lines = result.output.splitlines()
    report_lines = output_lines[len(list(template)) + 3:]
    for line, i_path in zip(report_lines, template):
        if 'ERROR' in line:
            assert tp_src(i_path).exists()
            assert not tp_dst(i_path).exists()
        else:
            assert not tp_src(i_path).exists()
            assert tp_dst(i_path).exists()


@pytest.fixture(scope='function')
def tcli_rm_template():
    name = MAIN_TEMPLATE.name + ' test_rm_template'
    registry.register_template(name, path=MAIN_TEMPLATE.path)
    yield name
    if tcore.exists(name):
        registry.deregister_template(name)


RM_TEMPLATE_USAGE_ERROR = ("Usage: rm [OPTIONS] NAME [REL_PATHS]...\n\n"
                           "Error: Invalid value for name: template {!r} doesn't exist.\n")


@pytest.mark.parametrize('name', [
    MAIN_TEMPLATE.name + ' test_rm_template'
])
def test_rm_template(name, tcli_rm_template):
    prompt = ("You are about to remove the template {!r}. "
              "It's instances will not be removed but they will be unregistered."
              "\nDo you want to continue? [y/N]: ".format(name))
    yes_prompt = prompt + 'y\n'
    no_prompt = prompt + 'n\n' + 'Aborted!\n'

    runner = CliRunner()
    result = runner.invoke(cli.rm, [name], input='n')
    assert result.output == no_prompt
    assert tcore.exists(name)

    result = runner.invoke(cli.rm, [name], input='y')
    assert result.output == yes_prompt
    assert not tcore.exists(name)

    result = runner.invoke(cli.rm, [name], input='y')
    assert result.output == yes_prompt + RM_TEMPLATE_USAGE_ERROR.format(name)

    result = runner.invoke(cli.rm, [name], input='n')
    assert result.output == no_prompt
