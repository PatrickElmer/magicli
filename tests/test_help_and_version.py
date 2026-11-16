import sys

from magicli import help_from_function, help_from_module

MODULE_NAME = "magicli_testmod"


def f1(arg, kwarg=1): ...


def create_module():
    module = type(sys)(MODULE_NAME)
    module.command = f1
    module.__all__ = ["command"]
    return module


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg]"


def test_help_from_module():
    assert (
        help_from_module(create_module())
        == f"""\
usage:
  {MODULE_NAME} command

commands:
  command\
"""
    )


def test_help_from_module_with_version():
    module = create_module()
    module.__version__ = "0.1.2"
    assert (
        help_from_module(module)
        == f"""\
{MODULE_NAME} 0.1.2

usage:
  {MODULE_NAME} command

commands:
  command\
"""
    )
