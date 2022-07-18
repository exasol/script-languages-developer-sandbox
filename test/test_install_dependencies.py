from pathlib import Path

import docker
import pytest
from docker.types import Mount

from exasol_script_languages_developer_sandbox.lib.ansible.ansible_access import AnsibleAccess
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_repository import AnsibleDirectoryRepository, \
    default_repositories
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_run_context import AnsibleRunContext
from exasol_script_languages_developer_sandbox.lib.run_install_dependencies import run_install_dependencies

TEST_CONTAINER_NAME = "ansible-test"
TEST_CONTAINER_IMAGE_TAG = "script_languages_developer_sandbox_test_container:latest"

@pytest.fixture
def docker_test_container():
    docker_env = docker.from_env()
    p = Path(__file__).parent / "test_container"
    docker_env.images.build(path=str(p), tag=TEST_CONTAINER_IMAGE_TAG)
    socket_mount = Mount("/var/run/docker.sock", "/var/run/docker.sock", type="bind")
    test_container = docker_env.containers.create(image=TEST_CONTAINER_IMAGE_TAG,
                                                  name=TEST_CONTAINER_NAME, mounts=[socket_mount],
                                                  command="sleep infinity", detach=True)
    test_container.start()
    yield test_container
    test_container.stop()
    test_container.remove()


def test_install_dependencies(docker_test_container):
    """"
    Test install dependencies, using test setup
    """
    ansible_test_dir = Path(__file__).parent / "ansible"
    repos = default_repositories + (AnsibleDirectoryRepository(ansible_test_dir),)
    ansible_run_context = AnsibleRunContext(playbook="slc_setup_test.yml",
                                            extra_vars={"test_docker_container": docker_test_container.name})
    run_install_dependencies(AnsibleAccess(), host_infos=tuple(), ansible_run_context=ansible_run_context,
                             ansible_repositories=repos)
