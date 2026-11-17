def test_first_function_called(module, run):
    assert run().out == "name\n"


def test_command_called(module, run):
    assert run("command").out == "command\n"


def test_wrong_command_not_called(module, run):
    assert run("wrong_command").code.startswith("wrong_command: unknown command")


def test_module_without_functions(fake_module, run):
    fake_module(doc="docstring")
    assert run().code == "docstring"


def test_module_not_found(run):
    result = run(prog="magicli_nonexistent_module")
    assert result.code == "magicli_nonexistent_module: command not found"


def test_short_option_with_wrong_type(module, run):
    assert run("-ab").code.startswith("-a: invalid short option")


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
