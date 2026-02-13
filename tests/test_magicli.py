import sys
from unittest import mock
from magicli import magicli
import pytest


ANSWER = None


def function_1():
    global ANSWER
    ANSWER = 1


def function_2():
    global ANSWER
    ANSWER = 2


def _create_module(name):
    module = type(sys)(name)
    module.name = function_1
    module.command = function_2
    module.__doc__ = "docstring"
    return module


@mock.patch("importlib.import_module", side_effect=_create_module)
def test_module_imported(mocked):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")


@mock.patch("importlib.import_module", side_effect=_create_module)
def test_first_function_called(mocked):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")
    assert ANSWER == 1


@mock.patch("importlib.import_module", side_effect=_create_module)
def test_command_called(mocked):
    sys.argv = ["name", "command"]
    magicli()
    mocked.assert_called_once_with("name")
    assert ANSWER == 2


@mock.patch("importlib.import_module", side_effect=_create_module)
def test_wrong_command_not_called(mocked):
    sys.argv = ["name", "wrong_command"]
    with pytest.raises(SystemExit):
        magicli()


def test_empty_sys_argv():
    sys.argv = []
    with pytest.raises(SystemExit):
        magicli()


def _create_empty_module(name):
    return type(sys)(name)


@mock.patch("importlib.import_module", side_effect=_create_empty_module)
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


def _create_module_with_docstring(name):
    module = type(sys)(name)
    module.name = lambda aa="", bb=None: None
    module.name.__doc__ = "-a, --aa\n-b, --bb"
    return module


@mock.patch("importlib.import_module", side_effect=_create_module_with_docstring)
def test_short_option_with_wrong_type(mocked):
    sys.argv = ["name", "-ab"]
    with pytest.raises(SystemExit):
        magicli()


def _create_module_with_versions(name):
    module = type(sys)(name)
    module.name = function_1
    module.name.__doc__ = "--version"
    module.command = function_2
    module.command.__doc__ = "-v, --version"
    module.__doc__ = "docstring"
    module.__version__ = "1.2.3"
    return module


@mock.patch("importlib.import_module", side_effect=_create_module_with_versions)
def test_version(mocked):
    sys.argv = ["name", "--version"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == "1.2.3"

    sys.argv = ["name", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == "-v: invalid short option"


@mock.patch("importlib.import_module", side_effect=_create_module_with_versions)
def test_version_with_command(mocked):
    sys.argv = ["name", "command", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == "1.2.3"
