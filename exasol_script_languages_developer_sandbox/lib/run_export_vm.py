import logging
import traceback
from sys import stderr
from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.cf_stack import find_ec2_instance_in_cf_stack
from exasol_script_languages_developer_sandbox.lib.print_assets import print_assets
from exasol_script_languages_developer_sandbox.lib.render_template import render_template
from exasol_script_languages_developer_sandbox.lib.vm_disk_image_format import VmDiskImageFormat
from exasol_script_languages_developer_sandbox.lib.vm_slc_bucket import find_vm_bucket, find_vm_import_role, \
    get_bucket_prefix
from importlib.metadata import version


def export_vm(aws_access: AwsAccess,
              instance_id: str,
              vm_image_formats: Tuple[str, ...],
              name_suffix: str) -> None:
    vm_bucket = find_vm_bucket(aws_access)
    name = render_template("vm_image_name.jinja",
                           slc_version=version("exasol_script_languages_release"), suffix=name_suffix).strip("\n")
    tag_value = render_template("aws_tag_value.jinja",
                           slc_version=version("exasol_script_languages_release"), suffix=name_suffix).strip("\n")
    vmimport_role = find_vm_import_role(aws_access)
    has_errors = False
    try:
        try:
            logging.info(f"create ami with name '{name}' and tag(s) '{tag_value}'")
            ami_id = "ami-055e106c605a2fa41"#aws_access.create_image_from_ec2_instance(instance_id, name=name, tag_value=tag_value,
                     #                                          description="Image Description")
        except Exception:
            traceback.print_exc()
            logging.error("Could not create AMI. Please remove snapshot if necessary!")
            has_errors = True
            return
        bucket_prefix = get_bucket_prefix(slc_version=version("exasol_script_languages_release"),
                                          name_suffix=name_suffix)
        for vm_image_format in vm_image_formats:
            try:
                logging.info(f"export ami to vm with format '{vm_image_format}' and tag(s) '{tag_value}'")
                aws_access.export_ami_image_to_vm(image_id=ami_id, tag_value=tag_value,
                                                  description="VM Description", role_name=vmimport_role,
                                                  disk_format=VmDiskImageFormat[vm_image_format],
                                                  s3_bucket=vm_bucket, s3_prefix=bucket_prefix)

            except Exception:
                traceback.print_exc()
                logging.error(f"Failed to export VM to bucket {vm_bucket} at {bucket_prefix}\n")
                has_errors = True
                break
    finally:
        if has_errors:
            print(f"VM Export finished for: {name}. There were errors. "
                  f"You might want to delete some of the assets created.", file=stderr)
        else:
            print(f"VM Export finished for: {name} without any errors", file=stderr)
        print_assets(aws_access=aws_access, slc_version=version("exasol_script_languages_release"),
                     outfile=None, name_suffix=name_suffix)


def run_export_vm(aws_access: AwsAccess,
                  stack_name: str,
                  vm_image_formats: Tuple[str, ...],
                  name_suffix: str):
    """
    Runs export only of the VM image.
    """
    ec_instance_id = find_ec2_instance_in_cf_stack(aws_access, stack_name)
    export_vm(aws_access, ec_instance_id, vm_image_formats, name_suffix)
