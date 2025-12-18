# magiᴄʟɪ✨

Automatically generates a CLI from functions of a module.

## Install

```
pip install magicli
```

## Get started

Simple usage example.

```python
# module.py
def hello(name, times=1):
    for _ in range(times):
        print("hello", name)
```

Then run this in your terminal to initialize the CLI:

```bash
magicli
```

You are now able to install your package:

```bash
pip install .
```

And then call it:

```bash
$ hello world --times 2
hello world
hello world
```

### Define name of CLI in `pyproject.toml`

The terminal command `magicli` adds the following to your `pyproject.toml`.

```toml
[project.scripts]
hello = "magicli:magicli"
```

Important: Make sure the name of your CLI, the module name and the name of the function to be called are the same!

```bash
.
├── hello.py
└── pyproject.toml
```

You can now `pip install` your code and call it like this:

```bash
$ hello world --times 2
hello world
hello world
```

### Using subcommands

```python
# module.py
def hello(): ...

def world(times=1):
    for _ in range(times):
        print("hello world")
```

```bash
$ hello world --times 2
hello world
hello world
```

### Help message

By default, the docstring of the function will be displayed.

If no docstring is specified, an error message will be printed.

## Development

Run pytest with coverage report:

```bash
python3 -m pytest -s --cov=magicli --cov-report=term-missing
```
