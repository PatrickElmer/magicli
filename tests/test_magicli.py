import sys
from functools import partial
from unittest import mock

import pytest

from magicli import magicli


def name():
    "-V, --version"
    print("name")


def command():
    "-v, --version"
    print("command")


def create_module(name, version=None, functions=None):
    module = type(sys)(name)
    module.__doc__ = "docstring"
    module.__version__ = version
    for function in functions or []:
        setattr(module, function.__name__, function)
    module.__all__ = [function.__name__ for function in functions or []]
    return module


module = partial(create_module, functions=[name, command])
module_version = partial(module, version="1.2.3")
module_empty = partial(create_module, functions=None)


def module_with_two_commands(name):
    module = type(sys)(name)
    setattr(module, "name", lambda: None)
    setattr(module, "command", lambda: None)
    setattr(module, "command_2", lambda: None)
    module.__all__ = ["name", "command", "command_2"]
    return module


@mock.patch("importlib.import_module", side_effect=module)
def test_module_imported(mocked):
    with mock.patch.object(sys, "argv", ["name"]):
        magicli()
    mocked.assert_called_once_with("name")


@mock.patch("importlib.import_module", side_effect=module)
def test_first_function_called(mocked, capsys):
    with mock.patch.object(sys, "argv", ["name"]):
        magicli()
    mocked.assert_called_once_with("name")
    assert capsys.readouterr().out == "name\n"


@mock.patch("importlib.import_module", side_effect=module)
def test_command_called(mocked, capsys):
    with mock.patch.object(sys, "argv", ["name", "command"]):
        magicli()
    mocked.assert_called_once_with("name")
    assert capsys.readouterr().out == "command\n"


@mock.patch("importlib.import_module", side_effect=module)
def test_wrong_command_not_called(mocked):
    with (
        mock.patch.object(sys, "argv", ["name", "wrong_command"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert error.value.code.startswith("wrong_command: unknown command")


@mock.patch("importlib.import_module", side_effect=module_empty)
def test_module_without_functions(mocked):
    with (
        mock.patch.object(sys, "argv", ["name"]),
        pytest.raises(SystemExit),
    ):
        magicli()


def test_module_not_found():
    with (
        mock.patch.object(sys, "argv", ["_"]),
        pytest.raises(SystemExit),
    ):
        magicli()


@mock.patch("builtins.input", return_value="n")
def test_module_is_magicli(_, pyproject):
    with (
        mock.patch.object(sys, "argv", ["magicli"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert error.value.code == 1


@mock.patch("importlib.import_module", side_effect=module)
def test_short_option_with_wrong_type(mocked):
    with (
        mock.patch.object(sys, "argv", ["name", "-ab"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert error.value.code.startswith("-a: invalid short option")


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version(mocked, capsys):
    for version in ["--version", "-V"]:
        with (
            mock.patch.object(sys, "argv", ["name", version]),
            pytest.raises(SystemExit) as error,
        ):
            magicli()
        assert error.value.code is None
        assert capsys.readouterr().out == "1.2.3\n"

    with (
        mock.patch.object(sys, "argv", ["name", "-v"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert error.value.code.startswith("-v: invalid short option")


@mock.patch("importlib.import_module", side_effect=module_version)
def test_version_with_command(mocked, capsys):
    with (
        mock.patch.object(sys, "argv", ["name", "command", "-v"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert error.value.code is None
    assert capsys.readouterr().out == "1.2.3\n"


@mock.patch("importlib.import_module", side_effect=module_with_two_commands)
def test_help_message_for_unknown_command(mocked):
    with (
        mock.patch.object(sys, "argv", ["name", "unknown_command"]),
        pytest.raises(SystemExit) as error,
    ):
        magicli()
    assert (
        error.value.code
        == """\
unknown_command: unknown command

usage:
  <lambda>
  name <command>

commands:
  command
  command_2\
"""
    )


@mock.patch("importlib.import_module", side_effect=module)
def test_help_kwarg_displays_help_message(mocked, capsys, monkeypatch):
    monkeypatch.setattr(name, "__doc__", None)
    with (
        mock.patch.object(sys, "argv", ["name", "--help"]),
        pytest.raises(SystemExit),
    ):
        magicli()
    doc = """usage:
  name
  name <command>

commands:
  command"""
    assert capsys.readouterr().out == doc + "\n"
