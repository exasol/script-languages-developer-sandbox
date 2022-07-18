import shutil
from pathlib import Path
from importlib.resources import open_text, contents, is_resource


class AnsibleRepository:

    def copy_to(self, target: Path) -> None:
        pass


class AnsibleResourceRepository(AnsibleRepository):

    def __init__(self, path: str):
        self._path = f"exasol_script_languages_developer_sandbox.{path}"

    def copy_to(self, target: Path) -> None:
        for ansible_file in contents(self._path):
            if ansible_file == "__init__.py":
                continue
            if is_resource(self._path, ansible_file):
                with open_text(self._path, ansible_file) as ansible_file_io:
                    content = ansible_file_io.read()
                    target_file_path = target / ansible_file
                    if target_file_path.exists():
                        raise RuntimeError(f"Repository target: {target_file_path} already exists.")
                    with open(target / ansible_file, "w") as f:
                        f.write(content)


default_repositories = (AnsibleResourceRepository("runtime.ansible"), AnsibleResourceRepository("runtime.dependencies"))


class AnsibleDirectoryRepository(AnsibleRepository):

    def __init__(self, path: Path):
        self._path = path

    def copy_to(self, target: Path) -> None:
        for f in self._path.iterdir():
            if f.is_file():
                shutil.copy(f, target / f.name)
