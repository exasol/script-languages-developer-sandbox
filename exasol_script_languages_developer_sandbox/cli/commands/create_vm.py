from typing import Optional, Tuple

import click

from exasol_script_languages_developer_sandbox.cli.cli import cli
from exasol_script_languages_developer_sandbox.cli.common import add_options
from exasol_script_languages_developer_sandbox.cli.options.aws_options import aws_options
from exasol_script_languages_developer_sandbox.cli.options.logging import logging_options, set_log_level
from exasol_script_languages_developer_sandbox.lib.ansible.ansible_access import AnsibleAccess
from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.host_info import HostInfo
from exasol_script_languages_developer_sandbox.lib.run_create_vm import run_create_vm
from exasol_script_languages_developer_sandbox.lib.vm_disk_image_format import VmDiskImageFormat, \
    all_vm_disk_image_formats


@cli.command()
@add_options(aws_options)
@add_options(logging_options)
@click.option('--ec2-key-file', required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False),
                 default=None, help="The EC2 key-pair-file to use. If not given a temporary key-pair-file will be created.")
@click.option('--ec2-key-name', required=False, type=str,
             default=None, help="The EC2 key-pair-name to use. Only needs to be set together with ec2-key-file.")
@click.option('--default-password', required=True, type=str,
              help="The new (temporary) default password.")
@click.option('--vm-image-format', default=all_vm_disk_image_formats(),
              type=click.Choice(all_vm_disk_image_formats()), multiple=True,
              help="The VM image format. Can be declared multiple times.")
def create_vm(
            aws_profile: str,
            ec2_key_file: Optional[str],
            ec2_key_name: Optional[str],
            default_password: str,
            vm_image_format: Tuple[str, ...],
            log_level: str):
    """
    Creates a new VM image from a fresg EC-2 Ubuntu AMI.
    """
    set_log_level(log_level)
    run_create_vm(AwsAccess(aws_profile), ec2_key_file, ec2_key_name,
                  AnsibleAccess(), default_password, vm_image_format)
