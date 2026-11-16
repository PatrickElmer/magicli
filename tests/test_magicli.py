import sys
from unittest import mock

import pytest

from magicli import magicli

MODULE_NAME = "magicli_testmod"


def magicli_testmod():
    "-V, --version"
    print("name")


def command():
    "-v, --version"
    print("command")


@pytest.fixture
def install_module(monkeypatch):
    """Factory that registers a fake module in `sys.modules` so `magicli` imports it."""

    def install(*functions, version=None, all_=None):
        module = type(sys)(MODULE_NAME)
        module.__doc__ = "docstring"
        module.__version__ = version
        for function in functions:
            setattr(module, function.__name__, function)
        module.__all__ = all_ or [function.__name__ for function in functions]
        monkeypatch.setitem(sys.modules, MODULE_NAME, module)
        return module

    return install


@pytest.fixture
def module(install_module):
    return install_module(magicli_testmod, command)


@pytest.fixture
def run(monkeypatch):
    """Runs `magicli` with the given command-line arguments."""

    def run_magicli(*argv, prog=MODULE_NAME):
        monkeypatch.setattr(sys, "argv", [prog, *argv])
        magicli()

    return run_magicli


def test_first_function_called(module, run, capsys):
    run()
    assert capsys.readouterr().out == "name\n"


def test_command_called(module, run, capsys):
    run("command")
    assert capsys.readouterr().out == "command\n"


def test_wrong_command_not_called(module, run):
    with pytest.raises(SystemExit) as error:
        run("wrong_command")
    assert error.value.code.startswith("wrong_command: unknown command")


def test_module_without_functions(install_module, run):
    install_module()
    with pytest.raises(SystemExit) as error:
        run()
    assert error.value.code == "docstring"


def test_module_not_found(run):
    with pytest.raises(SystemExit) as error:
        run(prog="magicli_nonexistent_module")
    assert error.value.code == "magicli_nonexistent_module: command not found"


@mock.patch("builtins.input", return_value="n")
def test_module_is_magicli(_, project, run):
    project("pyproject.toml", "module.py")
    with pytest.raises(SystemExit) as error:
        run(prog="magicli")
    assert error.value.code == 1


def test_short_option_with_wrong_type(module, run):
    with pytest.raises(SystemExit) as error:
        run("-ab")
    assert error.value.code.startswith("-a: invalid short option")


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version(install_module, run, capsys, flag):
    install_module(magicli_testmod, command, version="1.2.3")
    with pytest.raises(SystemExit) as error:
        run(flag)
    assert error.value.code is None
    assert capsys.readouterr().out == "1.2.3\n"


def test_version_flag_not_in_docstring(install_module, run):
    install_module(magicli_testmod, command, version="1.2.3")
    with pytest.raises(SystemExit) as error:
        run("-v")
    assert error.value.code.startswith("-v: invalid short option")


def test_version_with_command(install_module, run, capsys):
    install_module(magicli_testmod, command, version="1.2.3")
    with pytest.raises(SystemExit) as error:
        run("command", "-v")
    assert error.value.code is None
    assert capsys.readouterr().out == "1.2.3\n"


def test_help_message_for_unknown_command(monkeypatch, run):
    module = type(sys)(MODULE_NAME)
    module.magicli_testmod = lambda: None
    module.command = lambda: None
    module.command_2 = lambda: None
    module.__all__ = ["magicli_testmod", "command", "command_2"]
    monkeypatch.setitem(sys.modules, MODULE_NAME, module)
    with pytest.raises(SystemExit) as error:
        run("unknown_command")
    assert (
        error.value.code
        == f"""\
unknown_command: unknown command

usage:
  <lambda>
  {MODULE_NAME} <command>

commands:
  command
  command_2\
"""
    )


def test_help_kwarg_displays_help_message(module, run, capsys, monkeypatch):
    monkeypatch.setattr(magicli_testmod, "__doc__", None)
    with pytest.raises(SystemExit):
        run("--help")
    assert (
        capsys.readouterr().out
        == f"""\
usage:
  {MODULE_NAME}
  {MODULE_NAME} <command>

commands:
  command
"""
    )
