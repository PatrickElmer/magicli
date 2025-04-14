import pytest
from magicli import get_kwargs


@pytest.mark.parametrize(
    "prompt, result, function",
    [
        ("", {}, lambda: ...),
        ("one", {"arg": "one"}, lambda arg: ...),
        ("one two", {"arg": "one", "arg2": "two"}, lambda arg, arg2: ...),
        ("a-b", {"a_b": "a-b"}, lambda a_b: ...),
        ("a_b", {"a_b": "a_b"}, lambda a_b: ...),
        ("---e-f-", {"_e_f_": True}, lambda _e_f_=False: ...),
        ("--flag", {"flag": True}, lambda flag=False: ...),
        ("--flag", {"flag": False}, lambda flag=True: ...),
        ("--flag", {"flag": True}, lambda flag=None: ...),
        ("--option=2", {"option": 2}, lambda option=1: ...),
        ("--option 2", {"option": 2}, lambda option=1: ...),
    ],
)
def test_io(prompt, result, function):
    assert get_kwargs(prompt.split(), function) == result


def test_short_option():
    def f(aaa: str=""):
        """-a, --aaa  Docstring."""
        ...

    prompt = "-a string".split()
    assert get_kwargs(prompt, f) == {"aaa": "string"}


def test_short_option_bool():
    def f(aaa: bool=False):
        """/
        -a, --aaa  Docstring a.
        -b, --bbb  Docstring b.
        """
        ...

    assert get_kwargs(["-a"], f) == {"aaa": True}


def test_short_options():
    def f(aaa: str="", bbb: bool=False):
        """/
        -a, --aaa  Docstring a.
        -b, --bbb  Docstring b.
        """
        ...

    prompt = "-a string -b".split()
    result = {
        "aaa": "string",
        "bbb": True,
    }
    assert get_kwargs(prompt, f) == result


def test_short_option_failure():
    def f(aaa: bool=False): ...

    assert get_kwargs(["--aaa"], f) == {"aaa": True}
    with pytest.raises(KeyError):
        get_kwargs(["-a"], f)


def test_int():
    def f(arg: int): ...
    assert get_kwargs(["1"], f) == {"arg": 1}


def test_bool():
    def f(arg: bool): ...

    assert get_kwargs(["1"], f) == {"arg": True}
    assert get_kwargs(["0"], f) == {"arg": True}
    assert get_kwargs([""], f) == {"arg": False}


def test_str():
    def f(arg: str): ...

    assert get_kwargs(["1"], f) == {"arg": "1"}
    assert get_kwargs(["a"], f) == {"arg": "a"}


def test_kwarg_int():
    def f(kwarg: int = 0): ...

    assert get_kwargs(["--kwarg", "1"], f) == {"kwarg": 1}


def test_kwarg_bool():
    def f(kwarg: bool = False): ...

    assert get_kwargs(["--kwarg"], f) == {"kwarg": True}


def test_kwarg_bool_2():
    def f(kwarg: bool = True): ...

    assert get_kwargs(["--kwarg"], f) == {"kwarg": False}


def test_kwarg_str():
    def f(kwarg: str = ""): ...

    assert get_kwargs(["--kwarg", "1"], f) == {"kwarg": "1"}
    assert get_kwargs(["--kwarg", "a"], f) == {"kwarg": "a"}


def test_kwarg_float():
    def f(kwarg: float = 1.2): ...

    assert isinstance(get_kwargs(["--kwarg", "1"], f)["kwarg"], float)
    assert isinstance(get_kwargs(["--kwarg", "2.3"], f)["kwarg"], float)


def test_none():
    def f(flag=None): ...

    assert get_kwargs(["--flag"], f) == {"flag": True}


@pytest.mark.parametrize(
    "prompt, error, function",
    [
        ("arg", IndexError, lambda: ...),
        ("--kwarg", KeyError, lambda: ...),
        ("--kwarg 1", KeyError, lambda: ...),
        ("--kwarg", TypeError, lambda kwarg=0: ...),
        ("--kwarg a", ValueError, lambda kwarg=0: ...),
        ("", IndexError, lambda arg: ...),
    ],
)
def test_errors(prompt, error, function):
    with pytest.raises(error):
        get_kwargs(prompt.split(), function)


def test_two_values_for_kwarg():
    def function(a, bc="de"): ...

    argv = ["the test", "--bc", "af", "x"]
    with pytest.raises(KeyError) as e:
        get_kwargs(argv, function)


def test_same_kwarg_twice():
    def function(a, bc="de"): ...

    argv = ["--bc", "xx", "the test", "--bc", "af"]
    with pytest.raises(KeyError) as e:
        get_kwargs(argv, function)


def test_arg_in_the_middle():
    def function(a, bb=2, cc=3): ...

    argv = "--bb 4 . --cc 6".split()
    assert get_kwargs(argv, function) == {"a": ".", "bb": 4, "cc": 6}
