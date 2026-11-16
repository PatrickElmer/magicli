import pytest

from magicli import help_from_function, help_from_module


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg]"


def test_help_from_module(fake_module):
    module = fake_module(command=f1)
    assert (
        help_from_module(module)
        == f"""\
usage:
  {module.__name__} command

commands:
  command\
"""
    )


def test_help_from_module_with_version(fake_module):
    module = fake_module(command=f1, version="0.1.2")
    assert (
        help_from_module(module)
        == f"""\
{module.__name__} 0.1.2

usage:
  {module.__name__} command

commands:
  command\
"""
    )


def test_help_message_for_unknown_command(fake_module, run):
    module = fake_module(
        magicli_testmod=lambda: None, command=lambda: None, command_2=lambda: None
    )
    with pytest.raises(SystemExit) as error:
        run("unknown_command")
    assert (
        error.value.code
        == f"""\
unknown_command: unknown command

usage:
  <lambda>
  {module.__name__} <command>

commands:
  command
  command_2\
"""
    )


def test_help_kwarg_displays_help_message(module, run, capsys, monkeypatch):
    monkeypatch.setattr(module.magicli_testmod, "__doc__", None)
    with pytest.raises(SystemExit):
        run("--help")
    assert (
        capsys.readouterr().out
        == f"""\
usage:
  {module.__name__}
  {module.__name__} <command>

commands:
  command
"""
    )


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version(module, run, capsys, flag):
    module.__version__ = "1.2.3"
    with pytest.raises(SystemExit) as error:
        run(flag)
    assert error.value.code is None
    assert capsys.readouterr().out == "1.2.3\n"


def test_version_flag_not_in_docstring(module, run):
    module.__version__ = "1.2.3"
    with pytest.raises(SystemExit) as error:
        run("-v")
    assert error.value.code.startswith("-v: invalid short option")


def test_version_with_command(module, run, capsys):
    module.__version__ = "1.2.3"
    with pytest.raises(SystemExit) as error:
        run("command", "-v")
    assert error.value.code is None
    assert capsys.readouterr().out == "1.2.3\n"
