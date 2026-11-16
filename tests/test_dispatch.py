import pytest


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


def test_module_without_functions(fake_module, run):
    fake_module()
    with pytest.raises(SystemExit) as error:
        run()
    assert error.value.code == "docstring"


def test_module_not_found(run):
    with pytest.raises(SystemExit) as error:
        run(prog="magicli_nonexistent_module")
    assert error.value.code == "magicli_nonexistent_module: command not found"


def test_short_option_with_wrong_type(module, run):
    with pytest.raises(SystemExit) as error:
        run("-ab")
    assert error.value.code.startswith("-a: invalid short option")


def test_imported_function_is_not_a_command_without_all(fake_module, run, capsys):
    def own():
        print("own")

    def imported():
        print("imported")

    module = fake_module(own, imported, all_=False)
    module.__doc__ = None
    own.__module__ = module.__name__
    run("own")
    assert capsys.readouterr().out == "own\n"
    with pytest.raises(SystemExit) as error:
        run("imported")
    assert error.value.code == (
        f"usage:\n  {module.__name__} command\n\ncommands:\n  own"
    )
