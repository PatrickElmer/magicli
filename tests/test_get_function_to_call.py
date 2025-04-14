import pytest
from magicli import get_function_to_call


def root(): ...
def command(): ...
def _private(): ...


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


def test_private_function_not_called():
    function, argv = get_function_to_call(["app", "_private"], globals())
    assert function != _private
    assert function, argv == (root, ["_private"])


def test_get_second_function():
    function, _ = get_function_to_call(["app", "command"], globals())
    assert function == command


def test_all_public():
    global __all__
    __all__ = ["command"]
    function, _ = get_function_to_call(["app"], globals())
    assert function == command


def test_all_private():
    global __all__
    __all__ = ["_private"]
    function, _ = get_function_to_call(["app"], globals())
    assert function == _private
