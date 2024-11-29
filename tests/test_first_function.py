from magicli import first_function


def _private_function(): ...
def function_to_call(): ...
def second_function(): ...


def test_no_function():
    assert first_function({}) is None


def test_exclude_private_functions():
    assert first_function(globals()) is not _private_function


def test_exclude_imported_functions():
    assert first_function(globals()) is not first_function


def test_function():
    assert first_function(globals()) is function_to_call
