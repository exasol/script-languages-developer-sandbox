import shutil
from pathlib import Path
from importlib.resources import open_text, contents


class AnsibleRepository:

    def copy_to(self, target: Path) -> None:
        pass


class AnsibleResourceRepository(AnsibleRepository):

    def __init__(self, path: str):
        self._path = path

    def copy_to(self, target: Path) -> None:
        for ansible_file in contents(f"exasol_script_languages_developer_sandbox.{self._path}"):
            with open_text(f"exasol_script_languages_developer_sandbox.{self._path}", ansible_file) as ansible_file_io:
                content = ansible_file_io.read()
                with open(target / ansible_file, "w") as f:
                    f.write(content)


default_repository = AnsibleResourceRepository("ansible")


class AnsibleDirectoryRepository(AnsibleRepository):

    def __init__(self, path: Path):
        self._path = path

    def copy_to(self, target: Path) -> None:
        for f in self._path.iterdir():
            if f.is_file():
                shutil.copy(f, target / f.name)
