import logging
import sys
from functools import partial
from unittest import mock

import pytest
from fixtures import pyproject

from magicli import magicli


def name():
    "-V, --version"
    logging.info("name")


def command():
    "-v, --version"
    logging.info("command")


def create_module(name, version=None, functions=None):
    module = type(sys)(name)
    module.__doc__ = "docstring"
    module.__version__ = version
    for function in functions or []:
        function.__module__ = name
        setattr(module, function.__name__, function)
    return module


module = partial(create_module, functions=[name, command])
module_version = partial(module, version="1.2.3")
module_empty = partial(create_module, functions=None)


def module_with_two_commands(name):
    module = type(sys)(name)
    for command in ["name", "command", "command_2"]:
        function = lambda: None
        function.__module__ = name
        setattr(module, command, function)
    return module


def module_with_required_arguments(name):
    module = type(sys)(name)

    def entry_point(a, b):
        logging.info("%s %s", a, b)

    entry_point.__module__ = name
    setattr(module, name, entry_point)
    return module


@mock.patch("importlib.import_module", side_effect=module)
def test_module_imported(mocked):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")


@mock.patch("importlib.import_module", side_effect=module)
def test_first_function_called(mocked, caplog):
    sys.argv = ["name"]
    magicli()
    mocked.assert_called_once_with("name")
    assert caplog.messages[0] == "name"


@mock.patch("importlib.import_module", side_effect=module)
def test_command_called(mocked, caplog):
    sys.argv = ["name", "command"]
    magicli()
    mocked.assert_called_once_with("name")
    assert caplog.messages[0] == "command"


@mock.patch("importlib.import_module", side_effect=module)
def test_wrong_command_not_called(mocked):
    sys.argv = ["name", "wrong_command"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code.startswith("wrong_command: unknown command")


@mock.patch("importlib.import_module", side_effect=module_with_required_arguments)
def test_required_arguments_as_options(mocked, caplog):
    sys.argv = ["name", "--a", "1", "--b", "2"]
    magicli()
    assert caplog.messages[0] == "1 2"


@mock.patch("importlib.import_module", side_effect=module_with_required_arguments)
def test_required_arguments_mixed(mocked, caplog):
    sys.argv = ["name", "1", "--b", "2"]
    magicli()
    assert caplog.messages[0] == "1 2"


@mock.patch("importlib.import_module", side_effect=module_with_required_arguments)
def test_missing_required_argument(mocked):
    sys.argv = ["name", "--b", "2"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code.startswith("a: positional argument missing")


@mock.patch("importlib.import_module", side_effect=module_empty)
def test_module_without_functions(mocked):
    sys.argv = ["name"]
    with pytest.raises(SystemExit):
        magicli()


def test_module_not_found():
    sys.argv = ["_"]
    with pytest.raises(SystemExit):
        magicli()


@mock.patch("builtins.input", return_value="n")
def test_module_is_magicli(pyproject):
    sys.argv = ["magicli"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == 1


@mock.patch("importlib.import_module", side_effect=module)
def test_short_option_with_wrong_type(mocked):
    sys.argv = ["name", "-ab"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code.startswith("-a: invalid short option")


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version(mocked, caplog):
    for version in ["--version", "-V"]:
        sys.argv = ["name", version]
        with pytest.raises(SystemExit) as error:
            magicli()
        assert error.value.code is None
        assert caplog.messages[0] == "1.2.3"

    sys.argv = ["name", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code.startswith("-v: invalid short option")


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version_with_command(mocked, caplog):
    sys.argv = ["name", "command", "-v"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code is None
    assert caplog.messages[0] == "1.2.3"


@mock.patch("importlib.import_module", side_effect=module_with_two_commands)
def test_help_message_for_unknown_command(mocked):
    sys.argv = ["name", "unknown_command"]
    with pytest.raises(SystemExit) as error:
        magicli()
    assert error.value.code == """\
unknown_command: unknown command

usage:
  <lambda>
  name <command>

commands:
  command
  command_2\
"""

@mock.patch("importlib.import_module", side_effect=module)
def test_help_kwarg_displays_help_message(mocked, caplog):
    sys.argv = ["name", "--help"]
    name.__doc__ = None
    with pytest.raises(SystemExit):
        magicli()
    doc = """usage:
  name
  name <command>

commands:
  command"""
    assert caplog.messages[0] != name.__doc__
    assert caplog.messages[0] == doc
