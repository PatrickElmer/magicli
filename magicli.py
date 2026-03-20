"""
Magicli generates command-line interfaces from Python modules
by introspecting its functions and automatically parsing command-
line arguments based on function signatures.
"""

import importlib
import inspect
import subprocess
import sys
from functools import partial
from importlib import metadata
from pathlib import Path


def magicli():
    """
    Parses command-line arguments and calls the appropriate function.
    """
    name = Path(sys.argv[0]).name
    argv = sys.argv[1:]

    if name == "magicli":
        raise SystemExit(call(cli, argv, sys.modules["magicli"]))

    module = load_module(name)

    if function := get_function_from_argv(argv, module, name.replace("-", "_")):
        function()
    else:
        raise SystemExit(help_message(help_from_module, module))


def get_function_from_argv(argv, module, name):
    """Returns the module's function to call based on argv."""
    if function := is_command(argv, module):
        return partial(call, function, argv[1:], module, name)
    if inspect.isfunction(function := module.__dict__.get(name)):
        return partial(call, function, argv, module)
    return None


def is_command(argv, module):
    """
    Checks if the first argument is a valid command in the module and returns
    the function to call if `argv[0]` is public and not excluded in `__all__`.
    """
    if (
        argv
        and not (command := argv[0].replace("-", "_")).startswith("_")
        and command in module.__dict__.get("__all__", [command])
        and inspect.isfunction(function := module.__dict__.get(command))
    ):
        return function
    return None


def call(function, argv, module=None, name=None):
    """
    Converts arguments to function parameters and calls the function.
    Displays a help message if an exception occurs.
    """
    try:
        docstring = inspect.getdoc(function) or ""
        parameters = inspect.signature(function).parameters

        check_for_version(argv, parameters, docstring, module)

        args, kwargs = args_and_kwargs(argv, parameters, docstring)
        function(*args, **kwargs)
    except Exception:
        raise SystemExit(help_message(help_from_function, function, name))


def args_and_kwargs(argv, parameters, docstring):
    """Convert argv into args and kwargs."""
    parameter_list = list(parameters.values())
    args, kwargs = [], {}

    for key in (iter_argv := iter(argv)):
        if key.startswith("--"):
            left, right = parse_kwarg(key[2:], iter_argv, parameters)
            kwargs[left] = right
        elif key.startswith("-"):
            parse_short_options(key[1:], docstring, iter_argv, parameters, kwargs)
        else:
            args.append(get_type(parameter_list[len(args)])(key))

    return args, kwargs


def parse_kwarg(key, argv, parameters):
    """
    Parses a single keyword argument from command-line arguments.
    Handles '=' syntax for inline values. Casts `NoneType` values to `True`
    and boolean values to `not default`.
    """
    key, value = key.split("=", 1) if "=" in key else (key, None)
    key = key.replace("-", "_")
    cast_to = get_type(parameters.get(key))

    if value is None:
        if cast_to is bool:
            return key, not parameters[key].default
        if cast_to is type(None):
            return key, True
        value = next(argv)

    return key, value if cast_to is str else cast_to(value)


def parse_short_options(short_options, docstring, iter_argv, parameters, kwargs):
    """
    Converts short options into long options and casts into correct types.
    """
    for i, short in enumerate(short_options):
        long = short_to_long_option(short, docstring)

        if long not in parameters:
            raise SystemExit(f"--{long}: invalid long option")

        cast_to = get_type(parameters[long])

        if cast_to is bool:
            kwargs[long] = not parameters[long].default
        elif cast_to is type(None):
            kwargs[long] = True
        elif i == len(short_options) - 1:
            kwargs[long] = cast_to(next(iter_argv))
        else:
            raise SystemExit(f"-{short}: invalid type")


def short_to_long_option(short, docstring):
    """
    Converts a one character short option to a long option according to the help message.
    """
    template = f"-{short}, --"
    if (start := docstring.find(template)) != -1:
        start += len(template)
        if len(docstring) - start > 1:
            chars = [" ", "\n", "]"]
            indices = (i for char in chars if (i := docstring.find(char, start)) != -1)
            return docstring[start : min(indices, default=None)]
    raise SystemExit(f"-{short}: invalid short option")


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


def check_for_version(argv, parameters, docstring, module):
    """
    Displays version information if --version is specified in the docstring.
    """
    if (
        "version" not in parameters
        and any(
            (argv == [arg] and string in docstring)
            for arg, string in [
                ("--version", "--version"),
                ("-v", "-v, --version"),
                ("-V", "-V, --version"),
            ]
        )
        and module
    ):
        print(get_version(module))
        raise SystemExit


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
    return format_blocks([["usage:", " ".join(message)]])


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
        message.append(["commands:", *commands])

    return format_blocks(message)


def format_blocks(blocks, sep="\n  "):
    """Formats blocks of text with proper indentation."""
    return "\n\n".join(sep.join(block) for block in blocks)


def load_module(name):
    """Load module from name"""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        raise SystemExit(f"{name}: command not found")


def get_commands(module):
    """Returns list of public commands that are not present in `__all__`."""
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
        return metadata.version(module.__name__)
    except metadata.PackageNotFoundError:
        return module.__dict__.get("__version__")


def get_project_name():
    """
    Detect project name from project structure.
    """
    single_file_layout = [path.stem for path in Path().glob("*.py")]
    flat_layout = [
        path.parent.name
        for path in Path().glob("*/__init__.py")
        if path.parent.name != "tests"
    ]
    src_layout = [path.parent.name for path in Path().glob("src/*/__init__.py")]

    if len(names := single_file_layout + flat_layout + src_layout) == 1:
        return names[0]

    if name := input("CLI name: "):
        return name

    raise SystemExit(1)


def get_output(command):
    """Return the stdout of a shell command or None on failure."""
    try:
        output = subprocess.run(
            command.split(), capture_output=True, text=True, check=False
        ).stdout
    except FileNotFoundError:
        return None
    return output.removesuffix("\n") if output else None


def get_homepage(url=None):
    """Return a homepage url from a git remote url."""
    url = url or get_output("git remote get-url origin") or ""
    url = url.removesuffix(".git")
    if url.startswith("git@"):
        url = "https://" + url.replace(":", "/")[4:]
    return url


def get_description(name):
    """Return the first paragraph of a module's docstring if available."""
    try:
        if doc := (importlib.import_module(name).__doc__ or "").split("\n\n"):
            return " ".join(
                [stripped for line in doc[0].splitlines() if (stripped := line.strip())]
            )
    except ModuleNotFoundError:
        pass
    return None


def cli(
    name="",
    author="",
    email="",
    description="",
    homepage="",
):
    """
    magiCLI✨

    Generates a "pyproject.toml" configuration file for a module and sets up the project script.
    The CLI name must be the same as the module name.

    usage:
      magicli [option]

    options:
      --name
      --author
      --email
      --description
      --homepage
      -v, --version
    """
    pyproject = Path("pyproject.toml")
    if (
        pyproject.exists()
        and input("Overwrite existing pyproject.toml? (yN) ").strip().lower() != "y"
    ):
        raise SystemExit(1)

    name = name or get_project_name()
    author = author or get_output("git config --get user.name")
    email = email or get_output("git config --get user.email")
    authors = [f'{k}="{v}"' for k, v in {"name": author, "email": email}.items() if v]

    project = [
        "[project]",
        f'name = "{name}"',
        'dynamic = ["version"]',
        'dependencies = ["magicli<3"]',
    ]

    if authors:
        project.append(f"authors = [{{{', '.join(authors)}}}]")

    if Path(readme := "README.md").exists():
        project.append(f'readme = "{readme}"')

    if Path(license_file := "LICENSE").exists():
        project.append(f'license-files = ["{license_file}"]')

    if description or (description := get_description(name)):
        project.append(f'description = "{description}"')

    blocks = [project, ["[project.scripts]", f'{name} = "magicli:magicli"']]

    if homepage or (homepage := get_homepage()):
        blocks.append(["[project.urls]", f'Home = "{homepage}"'])

    blocks.append(
        [
            "[build-system]",
            'requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]',
            'build-backend = "setuptools.build_meta"',
        ]
    )

    pyproject.write_text(format_blocks(blocks, sep="\n") + "\n", encoding="utf-8")

    message = ["pyproject.toml created! ✨"]
    if Path(".git").exists():
        message.append("You can specify the version with `git tag`")
    else:
        message.append(
            "Error: Not a git repo. Run `git init`. Specify version with `git tag`."
        )
    print(*message, sep="\n")
