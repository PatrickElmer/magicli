import pytest


@pytest.mark.parametrize(
    ("argv", "out"),
    [((), "name\n"), (("command",), "command\n")],
    ids=["main_function", "command"],
)
def test_function_called(module, run, argv, out):
    assert run(*argv).out == out


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (("wrong_command",), "wrong_command: unknown command"),
        (("-ab",), "-a: invalid short option"),
    ],
    ids=["unknown_command", "unknown_short_option"],
)
def test_invalid_argv(module, run, argv, error):
    assert run(*argv).code.startswith(error)


def test_module_without_functions(fake_module, run):
    fake_module(doc="docstring")
    assert run().code == "docstring"


def test_module_not_found(run):
    result = run(prog="magicli_nonexistent_module")
    assert result.code == "magicli_nonexistent_module: command not found"


def test_imported_function_is_not_a_command_without_all(fake_module, run):
    def own():
        print("own")

    def imported():
        print("imported")

    module = fake_module(own, imported, all_=False)
    own.__module__ = module.__name__
    assert run("own").out == "own\n"
    assert run("imported").code == (
        f"usage:\n  {module.__name__} command\n\ncommands:\n  own"
    )
