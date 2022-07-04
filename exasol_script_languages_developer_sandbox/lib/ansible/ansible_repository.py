import shutil
from pathlib import Path

import jinja2


class AnsibleRepository:

    def copy_to(self, target: Path) -> None:
        pass


class AnsibleResourceRepository(AnsibleRepository):

    def __init__(self, path: str):
        self._path = path

    def copy_to(self, target: Path) -> None:
        loader = jinja2.PackageLoader("exasol_script_languages_developer_sandbox", package_path=self._path)
        env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape(), keep_trailing_newline=True)
        for ansible_file in loader.list_templates():
            t = env.get_template(ansible_file)
            content = t.render()
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
