from magicli import help_from_function
from magicli import help_from_module


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg --kwarg=1"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg --kwarg=1"


def test_help_from_module():
    import sys

    module = type(sys)("name")
    module.command = f1
    assert (
        help_from_module(module)
        == """\
usage:
  name command

commands:
  command\
"""
    )
