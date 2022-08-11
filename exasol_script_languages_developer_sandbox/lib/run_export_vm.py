from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.cf_stack import find_ec2_instance_in_cf_stack
from exasol_script_languages_developer_sandbox.lib.render_template import render_template
from exasol_script_languages_developer_sandbox.lib.vm_disk_image_format import VmDiskImageFormat
from exasol_script_languages_developer_sandbox.lib.vm_slc_bucket import find_vm_bucket, find_vm_import_role
from importlib.metadata import version

BUCKET_PREFIX = "slc_developer_sandbox"


def export_vm(aws_access: AwsAccess,
              instance_id: str,
              vm_image_formats: Tuple[str, ...]) -> None:
    vm_bucket = find_vm_bucket(aws_access)
    ami_name = render_template("vm_image_name.jinja", slc_version=version("exasol_script_languages_release"))
    vmimport_role = find_vm_import_role(aws_access)

    ami_id = aws_access.create_image_from_ec2_instance(instance_id, name=ami_name, description="Image Description")
    for vm_image_format in vm_image_formats:
        aws_access.export_ami_image_to_vm(image_id=ami_id, description="VM Description",
                                          role_name=vmimport_role, disk_format=VmDiskImageFormat[vm_image_format],
                                          s3_bucket=vm_bucket, s3_prefix=BUCKET_PREFIX)


def run_export_vm(aws_access: AwsAccess,
                  stack_name: str,
                  vm_image_formats: Tuple[str, ...]) -> None:
    """
    Runs export only of the VM image.
    """
    ec_instance_id = find_ec2_instance_in_cf_stack(aws_access, stack_name)
    export_vm(aws_access, ec_instance_id, vm_image_formats)
