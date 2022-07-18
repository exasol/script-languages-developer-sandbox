from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.ansible.ansible_access import AnsibleAccess
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_context_manager import AnsibleContextManager
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_repository import AnsibleRepository, \
    default_repositories
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_run_context import AnsibleRunContext

from exasol_script_languages_developer_sandbox.lib.host_info import HostInfo


def run_install_dependencies(ansible_access: AnsibleAccess, host_infos: Tuple[HostInfo, ...],
                             ansible_run_context: AnsibleRunContext,
                             ansible_repositories: Tuple[AnsibleRepository, ...] = default_repositories) -> None:
    with AnsibleContextManager(ansible_access, ansible_repositories) as ansible_runner:
        ansible_runner.run(ansible_run_context, host_infos=host_infos)
