"""
Magicli generates command-line interfaces from Python modules
by introspecting its functions and automatically parsing command-
line arguments based on function signatures.
"""

import sys
import importlib
import inspect
from pathlib import Path


__all__ = ["cli"]


def magicli():
    """
    Parses command-line arguments and calls the appropriate function.
    """
    if not sys.argv:
        raise SystemExit(1)

    name, *argv = sys.argv
    name = Path(name).name.replace("-", "_")

    if name == "magicli":
        raise SystemExit(call(cli, argv))

    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError:
        raise SystemExit(f"{name}: command not found")

    if function := command_is_callable(argv, module):
        call(function, argv[1:], name)
    elif inspect.isfunction(function := module.__dict__.get(name)):
        call(function, argv)
    else:
        raise SystemExit(help_message(help_from_module, module))


def command_is_callable(argv, module):
    """
    Checks if the first argument is a valid command in the module and returns
    the function to call if argv[0] is public and not excluded in `__all__,
    """
    if (
        argv
        and not (command := argv[0].replace("-", "_")).startswith("_")
        and command in module.__dict__.get("__all__", [command])
        and inspect.isfunction(function := module.__dict__.get(command))
    ):
        return function
    return None


def call(function, argv, name=None):
    """
    Converts arguments to function parameters and calls the function.
    Displays a help message if an exception occurs.
    """
    try:
        args, kwargs = args_and_kwargs(argv, function)
        function(*args, **kwargs)
    except Exception:
        raise SystemExit(help_message(help_from_function, function, name))


def help_message(help_function, obj, *args):
    """
    Generates a help message for a function or module.
    Returns the object's docstring if available, otherwise generates the help message
    using the provided help_function.
    """
    return inspect.getdoc(obj) or help_function(obj, *args) or 1


def args_and_kwargs(argv, function):
    """
    Parses command-line arguments into positional and keyword arguments.
    """
    parameters = inspect.signature(function).parameters
    parameter_list = list(parameters.values())

    args, kwargs = [], {}

    argv = iter(argv)
    for key in argv:
        key = key.replace("-", "_")
        if key.startswith("__"):
            key, value = parse_kwarg(key[2:], argv, parameters)
            kwargs[key] = value
        else:
            args.append(get_type(parameter_list[len(args)])(key))

    return args, kwargs


def parse_kwarg(key, argv, parameters):
    """
    Parses a single keyword argument from command-line arguments.
    Handles '=' syntax for inline values. Casts NoneType values to True
    and bool and boolean to not default.
    """
    if "=" in key:
        key, value = key.split("=", 1)
        cast_to = get_type(parameters[key])
    else:
        cast_to = get_type(parameters[key])
        if cast_to is bool:
            return key, not parameters[key].default
        elif cast_to is type(None):
            return key, True
        value = next(argv)
    return key, value if cast_to is str else cast_to(value)


def get_type(parameter):
    """
    Determines the type based on function signature annotations or defaults.
    Falls back to str if neither is available.
    """
    if parameter.annotation is not parameter.empty:
        return parameter.annotation
    if parameter.default is not parameter.empty:
        return type(parameter.default)
    return str


def help_from_function(function, name=None):
    """
    Generates a help message for a function based on its signature.
    Displays the function name, required positional arguments, and
    optional keyword arguments with their default values.
    """
    message = [f"usage:\n  {(f"{name} " if name else "") + function.__name__}"]
    for parameter in inspect.signature(function).parameters.values():
        if parameter.default is parameter.empty:
            message.append(parameter.name)
        else:
            message.append(f"--{parameter.name}={parameter.default!r}")

    return " ".join(message) or None


def help_from_module(module):
    """
    Generates a help message for a module and lists available commands.
    Lists all public functions that are not excluded in `__all__`.
    """
    functions = inspect.getmembers(module, inspect.isfunction)
    if commands := [
        name
        for name, _ in functions
        if not name.startswith("_") and name in module.__dict__.get("__all__", [name])
    ]:
        message = f"usage:\n  {module.__name__} command\n\ncommands:"
        return "\n  ".join([message] + commands)


def cli():
    """
    Generates a pyproject.toml configuration file for a module and sets up the project script.
    The CLI name must be the same as the module name.
    """
    if (
        Path("pyproject.toml").exists()
        and not input("Overwrite existing pyproject.toml? (yN) ").strip().lower() == "y"
    ):
        raise SystemExit(1)

    flat_layout = [path.stem for path in Path().iterdir() if path.suffix == ".py"]
    src_layout = [
        path for path in Path().iterdir() if (Path(path) / "__init__.py").exists()
    ]

    if len(names := flat_layout + src_layout) == 1:
        name = names[0]
    else:
        msg = f"{len(names)} modules found: {', '.join(names)}\n"
        name = input(msg + "CLI name: ")

    if not name in names:
        raise SystemExit("Please choose a valid module name.")

    Path("pyproject.toml").write_text(
        f"""[build-system]
requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
dynamic = ["version"]
dependencies = ["magicli"]

[project.scripts]
{name} = "magicli:magicli"
"""
    )

    return """pyproject.toml created.
Set the version either through `git tag` or `__version__`."""
