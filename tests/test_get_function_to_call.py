import pytest
from magicli import get_function_to_call


def root(): ...
def command(): ...


@pytest.mark.parametrize(
    "sys_argv, function, argv",
    [
        (["root", "command", "arg"], command, ["arg"]),
        (["root", "arg"], root, ["arg"]),
        (["root", "root"], root, ["root"]),
        (["first", "arg"], root, ["arg"]),
        (["path/to/file.py", "arg"], root, ["arg"]),
        # argv[0] can call a function that is not the first
        (["command", "arg"], command, ["arg"]),
    ],
)
def test_success(sys_argv, function, argv):
    _function, _argv = get_function_to_call(sys_argv, globals())
    assert _function == function
    assert _argv == argv


def test_no_argv():
    with pytest.raises(ValueError):
        get_function_to_call([], globals())
