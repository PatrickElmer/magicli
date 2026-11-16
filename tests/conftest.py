import pytest


@pytest.fixture(autouse=True)
def isolated_git(tmp_path, monkeypatch):
    """Keep git from reading the user's config or discovering repositories above `tmp_path`."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))


@pytest.fixture
def project(tmp_path, monkeypatch):
    """
    Factory that turns `tmp_path` into the working directory and populates it.
    Positional arguments are touched as empty files, keyword arguments are written
    with their value as content and `git=True` creates a `.git` directory.
    """
    monkeypatch.chdir(tmp_path)

    def make(*files, git=False, **contents):
        if git:
            (tmp_path / ".git").mkdir()
        for filename in files:
            (tmp_path / filename).touch()
        for filename, content in contents.items():
            (tmp_path / filename).write_text(content, encoding="utf-8")
        return tmp_path

    return make
