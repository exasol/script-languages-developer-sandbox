from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.ansible.ansible_access import AnsibleAccess
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_context_manager import AnsibleContextManager
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_repository import AnsibleRepository, \
    default_repositories
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_run_context import AnsibleRunContext

from exasol_script_languages_developer_sandbox.lib.host_info import HostInfo
import importlib.metadata as meta


def run_install_dependencies(ansible_access: AnsibleAccess, host_infos: Tuple[HostInfo, ...],
                             ansible_run_context: AnsibleRunContext,
                             ansible_repositories: Tuple[AnsibleRepository, ...] = default_repositories) -> None:
    # TODO: Awaiting release 5.0.0 of slc!!!
    # new_extra_vars = {"slc_version": meta.version("exasol_script_languages_release")}
    new_extra_vars = {"slc_version": "master"}
    new_extra_vars.update(ansible_run_context.extra_vars)
    new_ansible_run_context = AnsibleRunContext(ansible_run_context.playbook, new_extra_vars)
    with AnsibleContextManager(ansible_access, ansible_repositories) as ansible_runner:
        ansible_runner.run(new_ansible_run_context, host_infos=host_infos)
