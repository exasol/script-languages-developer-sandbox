# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['exasol_script_languages_developer_sandbox',
 'exasol_script_languages_developer_sandbox.cli',
 'exasol_script_languages_developer_sandbox.cli.commands',
 'exasol_script_languages_developer_sandbox.cli.options',
 'exasol_script_languages_developer_sandbox.lib',
 'exasol_script_languages_developer_sandbox.lib.ansible',
 'exasol_script_languages_developer_sandbox.runtime',
 'exasol_script_languages_developer_sandbox.runtime.ansible',
 'exasol_script_languages_developer_sandbox.runtime.dependencies']

package_data = \
{'': ['*'], 'exasol_script_languages_developer_sandbox': ['templates/*']}

install_requires = \
['ansible-runner>=2.2.1,<3.0.0',
 'ansible>=6.1.0,<7.0.0',
 'boto3>=1.22.0,<2.0.0',
 'click>=8.1.3,<9.0.0',
 'exasol_script_languages_release @ '
 'git+https://github.com/exasol/script-languages-release.git@bug/679_use_a_duplicated_pyproject_toml',
 'jinja2>=3.1.0']

setup_kwargs = {
    'name': 'exasol-script-languages-developer-sandbox',
    'version': '0.1.0',
    'description': 'Manages script-languages developer virtual machines.',
    'long_description': None,
    'author': 'Thomas Uebensee',
    'author_email': 'ext.thomas.uebensee@exasol.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8.0,<4.0',
}


setup(**setup_kwargs)
