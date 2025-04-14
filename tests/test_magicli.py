import inspect
import pytest

from magicli import magicli


frame_globals = inspect.currentframe().f_globals
__version__ = "0.0.0"


def foo():
    """foo help"""
    print(foo.__name__ * 2)


def bar():
    """bar help"""
    print(bar.__name__ * 2)


def baz(arg): ...


def custom_version(version=False):
    """None"""
    print("Version:", __version__)


def custom_help(help=False):
    """None"""
    if help:
        print("Help: " + custom_help.__name__)


def generated_help_message(arg, kwarg="default"):
    """Help message for generated_help_message."""
    ...


def hello(name="world"):
    print("hello", name)


def _cli(prompt, capsys=None):
    magicli(frame_globals=frame_globals, argv=prompt.split())
    return capsys.readouterr().out.rstrip()


@pytest.mark.parametrize(
    "prompt, output",
    [
        ("foo", foo.__name__ * 2),
        ("foo --help", foo.__doc__),
        ("foo bar", bar.__name__ * 2),
        ("foo bar --help", bar.__doc__),
        ("foo custom-version --version", "Version: " + __version__),
        ("foo custom-help --help", "Help: " + custom_help.__name__),
    ],
)
def test_success(prompt, output, capsys):
    assert output == _cli(prompt, capsys)


@pytest.mark.parametrize(
    "prompt, output",
    [
        ("foo foofoo", "foo help"),
        ("foo x", "foo help"),
        ("foo baz", ""),
        ("foo generated-help-message", generated_help_message.__doc__),
    ],
)
def test_failure(prompt, output, capsys):
    with pytest.raises(SystemExit):
        output == _cli(prompt, capsys)


def test_fail_on_arg_as_kwarg(capsys):
    assert _cli("say hello", capsys) == "hello world"
    with pytest.raises(SystemExit):
        _cli("say hello magicli", capsys)


def test_show_version(capsys):
    assert _cli("foo --version", capsys) == __version__
