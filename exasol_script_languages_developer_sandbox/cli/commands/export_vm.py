from typing import Tuple

import click

from exasol_script_languages_developer_sandbox.cli.cli import cli
from exasol_script_languages_developer_sandbox.cli.common import add_options
from exasol_script_languages_developer_sandbox.cli.options.aws_options import aws_options
from exasol_script_languages_developer_sandbox.cli.options.logging import logging_options, set_log_level
from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.run_export_vm import run_export_vm
from exasol_script_languages_developer_sandbox.lib.vm_disk_image_format import all_vm_disk_image_formats


@cli.command()
@add_options(aws_options)
@add_options(logging_options)
@click.option('--stack-name', required=True,
              type=str,
              help="Existing cloudformation stack containing the EC2 instance.")
@click.option('--vm-image-format', default=all_vm_disk_image_formats(),
              type=click.Choice(all_vm_disk_image_formats()), multiple=True,
              help="The VM image format. Can be declared multiple times.")
def export_vm(
            aws_profile: str,
            stack_name: str,
            vm_image_format: Tuple[str, ...],
            log_level: str):
    """
    Debug command which creates a new VM image from a running EC2-Instance.
    """
    set_log_level(log_level)
    run_export_vm(AwsAccess(aws_profile), stack_name, vm_image_format)
