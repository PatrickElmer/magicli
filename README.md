# magiᴄʟɪ✨

```bash
magicli
```

automatically turns a file into a CLI by introspecting its functions.

- no boilerplate
- automatic help message
- type casting included
- supports sub-commands
- complete `pyproject.toml` setup
- ready for upload to `pypi`

Create a full CLI in only 2 lines of code:

```python
# hello.py
def hello(name, greeting="hello"):
    print(greeting, name)
```

calling `magicli` creates this CLI:

![hello world example](https://raw.githubusercontent.com/PatrickElmer/magicli/refs/heads/main/docs/img/hello.svg)

(animated terminal created with [clivio](patrickelmer.github.io/clivio))

## Quick start

### Install magicli

```
pip install magicli
```

### Setup your repository

Initialize repo

```bash
git init
```

Add version info (optional)

```bash
git tag 1.0.0
```

### Automatically create CLI

```bash
magicli
```

_Make sure the name of your CLI, the module name and the name of the function have to same name._

### Install your Python package

```bash
pip install .
```

or after uploading to `pypi`:

```bash
pip install <package_name>
```

## Advanced use

### Using subcommands

```python
# hello.py
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
