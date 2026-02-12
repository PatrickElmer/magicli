"""
Magicli generates command-line interfaces from Python modules
by introspecting its functions and automatically parsing command-
line arguments based on function signatures.
"""

import sys
import importlib
import inspect
from pathlib import Path


def magicli():
    """
    Parses command-line arguments and calls the appropriate function.
    """
    if not sys.argv:
        raise SystemExit(1)

    name = Path(sys.argv[0]).name
    argv = sys.argv[1:]

    if name == "magicli":
        raise SystemExit(call(cli, argv))

    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError:
        raise SystemExit(f"{name}: command not found")

    name = name.replace("-", "_")

    if function := is_command(argv, module):
        call(function, argv[1:], name)
    elif inspect.isfunction(function := module.__dict__.get(name)):
        call(function, argv)
    else:
        raise SystemExit(help_message(help_from_module, module))


def is_command(argv, module):
    """
    Checks if the first argument is a valid command in the module and returns
    the function to call if `argv[0]` is public and not excluded in `__all__`,
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


def args_and_kwargs(argv, function):
    """
    Parses command-line arguments into positional and keyword arguments.
    """
    parameters = inspect.signature(function).parameters
    parameter_list = list(parameters.values())
    args, kwargs = [], {}

    for key in (argv := iter(argv)):
        key = key.replace("-", "_")
        if key.startswith("__"):
            key, value = parse_kwarg(key[2:], argv, parameters)
            kwargs[key] = value
        elif key.startswith("_"):
            docstring = inspect.getdoc(function) or ""
            parse_short_options(key[1:], docstring, argv, parameters, kwargs)
        else:
            args.append(get_type(parameter_list[len(args)])(key))

    return args, kwargs


def parse_short_options(short_options, docstring, argv, parameters, kwargs):
    """
    Converts short options into long options and casts into correct types.
    """
    for short in short_options:
        long = short_to_long_option(short, docstring)
        if not long in parameters:
            raise SystemExit(f"--{long}: invalid long option")
        cast_to = get_type(parameters[long])
        if cast_to is bool:
            kwargs[long] = not parameters[long].default
        elif cast_to is type(None):
            kwargs[long] = True
        elif short == short_options[-1]:
            kwargs[long] = cast_to(next(argv))
        else:
            raise SystemExit(f"-{short}: invalid type")


def short_to_long_option(short, docstring):
    """
    Converts a one character short option to a long option accoring to the help message.
    """
    template = f"-{short}, --"
    if (start := docstring.find(template)) != -1:
        start += len(template)
        for i, char in enumerate(docstring[start:], start):
            if char in {" ", "\n"}:
                return docstring[start:i]
        if len(docstring) - start > 1:
            return docstring[start:]
    raise SystemExit(f"-{short}: invalid short option")


def parse_kwarg(key, argv, parameters):
    """
    Parses a single keyword argument from command-line arguments.
    Handles '=' syntax for inline values. Casts `NoneType` values to `True`
    and boolean values to `not default`.
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
    Falls back to `str` if neither is available.
    """
    if parameter.annotation is not parameter.empty:
        return parameter.annotation
    if parameter.default is not parameter.empty:
        return type(parameter.default)
    return str


def help_message(help_function, obj, *args):
    """
    Generates a help message for a function or module.
    Returns the object's docstring if available, otherwise generates the help message
    using the provided `help_function`.
    """
    return inspect.getdoc(obj) or help_function(obj, *args) or 1


def help_from_function(function, name=None):
    """
    Generates a help message for a function based on its signature.
    Displays the function name, required positional arguments, and
    optional keyword arguments with their default values.
    """
    message = [name] if name else []
    message.append(function.__name__)
    message.extend(map(format_kwarg, inspect.signature(function).parameters.values()))
    return format_message([["usage:", " ".join(message)]])


def format_kwarg(kwarg):
    """Formats a parameter as positional or optional argument."""
    return kwarg.name if kwarg.default is kwarg.empty else f"[--{kwarg.name}]"


def help_from_module(module):
    """
    Generates a help message for a module and lists available commands.
    Lists all public functions that are not excluded in `__all__`.
    """
    message = []

    if version := get_version(module):
        message.append([f"{module.__name__} {version}"])

    message.append(["usage:", f"{module.__name__} command"])

    if commands := get_commands(module):
        message.append(["commands:"] + commands)

    return format_message(message)


def format_message(blocks):
    """Formats blocks of text with proper indentation."""
    return "\n\n".join("\n  ".join(block) for block in blocks)


def get_commands(module):
    """Returns list of public commands, unless not present in `__all__`."""
    return [
        name
        for name, _ in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and name in module.__dict__.get("__all__", [name])
    ]


def get_version(module):
    """
    Returns the version of a module from its metadata or `__version__` attribute.
    """
    try:
        return importlib.metadata.version(module.__name__)
    except importlib.metadata.PackageNotFoundError:
        return module.__dict__.get("__version__")


def get_project_name():
    """
    Detect project name from project structure.
    """
    flat_layout = [path.stem for path in Path().glob("*.py")]
    src_layout = [
        path for path in Path().iterdir() if (Path(path) / "__init__.py").exists()
    ]

    if len(names := flat_layout + src_layout) == 1:
        return names[0]

    if name := input("CLI name: "):
        return name

    raise SystemExit(1)


def cli():
    """
    Generates a "pyproject.toml" configuration file for a module and sets up the project script.
    The CLI name must be the same as the module name.
    """
    pyproject = Path("pyproject.toml")
    if (
        pyproject.exists()
        and input("Overwrite existing pyproject.toml? (yN) ").strip().lower() != "y"
    ):
        raise SystemExit(1)

    name = get_project_name()
    pyproject.write_text(
        f"""\
[build-system]
requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
dynamic = ["version"]
dependencies = ["magicli<3"]

[project.scripts]
{name} = "magicli:magicli"
"""
    )

    return """pyproject.toml created.
Set the version either through `git tag` or `__version__`."""
