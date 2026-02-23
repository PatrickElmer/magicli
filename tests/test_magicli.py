import sys
from unittest import mock
from functools import partial

import pytest

from magicli import magicli

ANSWER = None


def name():
    "--version"
    global ANSWER
    ANSWER = 1


def command():
    "-v, --version"
    global ANSWER
    ANSWER = 2


def create_module(name, version=None, functions=None):
    module = type(sys)(name)
    module.__doc__ = "docstring"
    module.__version__ = version
    for function in functions or []:
        setattr(module, function.__name__, function)
    return module


module = partial(create_module, functions=[name, command])
module_version = partial(module, version="1.2.3")
module_empty = partial(create_module, functions=None)


@mock.patch("importlib.import_module", side_effect=module)
def test_module_imported(mocked):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")


@mock.patch("importlib.import_module", side_effect=module)
def test_first_function_called(mocked):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")
    assert ANSWER == 1


@mock.patch("importlib.import_module", side_effect=module)
def test_command_called(mocked):
    sys.argv = ["name", "command"]
    magicli()
    mocked.assert_called_once_with("name")
    assert ANSWER == 2


@mock.patch("importlib.import_module", side_effect=module)
def test_wrong_command_not_called(mocked):
    sys.argv = ["name", "wrong_command"]
    with pytest.raises(SystemExit):
        magicli()


def test_empty_sys_argv():
    sys.argv = []
    with pytest.raises(SystemExit):
        magicli()


@mock.patch("importlib.import_module", side_effect=module_empty)
def test_module_without_functions(mocked):
    sys.argv = ["name"]
    with pytest.raises(SystemExit):
        magicli()


def test_module_not_found():
    sys.argv = ["_"]
    with pytest.raises(SystemExit):
        magicli()


@mock.patch("builtins.input", lambda *args: "n")
def test_module_is_magicli():
    sys.argv = ["magicli"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == 1


@mock.patch("importlib.import_module", side_effect=module)
def test_short_option_with_wrong_type(mocked):
    sys.argv = ["name", "-ab"]
    with pytest.raises(SystemExit):
        magicli()


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version(mocked, capsys):
    sys.argv = ["name", "--version"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code is None
    assert capsys.readouterr()[0] == "1.2.3\n"

    sys.argv = ["name", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == "-v: invalid short option"


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version_with_command(mocked, capsys):
    sys.argv = ["name", "command", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code is None
    assert capsys.readouterr()[0] == "1.2.3\n"
