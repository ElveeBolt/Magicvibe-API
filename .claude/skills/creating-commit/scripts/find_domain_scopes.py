"""
Print domain scopes: subdirectories of src/<package>/.
The package name is detected automatically, so the skill works in any src-layout project.
Usage: python scripts/find_domain_scopes.py
"""

import subprocess
from pathlib import Path

IGNORED = {"core", "middlewares"}


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(out.stdout.strip())
    except OSError, subprocess.CalledProcessError:
        return Path.cwd()


def subdirs(path):
    """
    Visible subdirectories, skipping .hidden, _private, __pycache__ and *.egg-info.
    """
    if not path.is_dir():
        return []
    return sorted(
        d
        for d in path.iterdir()
        if d.is_dir()
        and not d.name.startswith((".", "_"))
        and not d.name.endswith(".egg-info")
    )


def main():
    packages = subdirs(repo_root() / "src")
    domains = sorted(
        {d.name for pkg in packages for d in subdirs(pkg) if d.name not in IGNORED}
    )

    if not packages:
        print("Domain scopes: (no package found in src/)")
    else:
        where = ", ".join(f"src/{p.name}" for p in packages)
        print(f"Domain scopes ({where}):", ", ".join(domains) or "(none)")


if __name__ == "__main__":
    main()
