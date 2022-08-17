import logging
import time
import traceback
from sys import stderr
from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.asset_id import AssetId
from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.setup_ec2.cf_stack import find_ec2_instance_in_cf_stack
from exasol_script_languages_developer_sandbox.lib.asset_printing.print_assets import print_assets
from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format import VmDiskImageFormat
from exasol_script_languages_developer_sandbox.lib.vm_bucket.vm_slc_bucket import find_vm_bucket, find_vm_import_role


def export_vm(aws_access: AwsAccess,
              instance_id: str,
              vm_image_formats: Tuple[str, ...],
              asset_id: AssetId) -> None:
    vm_bucket = find_vm_bucket(aws_access)
    vmimport_role = find_vm_import_role(aws_access)
    tag_value = asset_id.tag_value
    bucket_prefix = f"{asset_id.bucket_prefix}/"
    ami_name = asset_id.ami_name
    has_errors = False
    try:
        try:
            logging.info(f"create ami with name '{ami_name}' and tag(s) '{tag_value}'")
            ami_id = aws_access.create_image_from_ec2_instance(instance_id, name=ami_name, tag_value=tag_value,
                                                               description="Image Description")

            ami_state = aws_access.get_ami(ami_id)["State"]
            while ami_state == "pending":
                logging.info(f"ami  with name '{ami_name}' and tag(s) '{tag_value}'  still pending...")
                time.sleep(10)
                ami_state = aws_access.get_ami(ami_id)["State"]
            if ami_state != "available":
                raise RuntimeError(f"Failed to create ami! ami state is '{ami_state}'")
        except Exception:
            logging.exception("Could not create AMI. Please remove snapshot if necessary!")
            has_errors = True
            return
        for vm_image_format in vm_image_formats:
            try:
                logging.info(f"export ami to vm with format '{vm_image_format}' and tag(s) '{tag_value}'")
                aws_access.export_ami_image_to_vm(image_id=ami_id, tag_value=tag_value,
                                                  description="VM Description", role_name=vmimport_role,
                                                  disk_format=VmDiskImageFormat[vm_image_format],
                                                  s3_bucket=vm_bucket, s3_prefix=bucket_prefix)

            except Exception:
                logging.exception(f"Failed to export VM to bucket {vm_bucket} at {bucket_prefix}\n")
                has_errors = True
                break
    finally:
        if has_errors:
            print(f"VM Export finished for: {ami_name}. There were errors. "
                  f"You might want to delete some of the assets created.", file=stderr)
        else:
            print(f"VM Export finished for: {ami_name} without any errors", file=stderr)
        print_assets(aws_access=aws_access, asset_id=asset_id, outfile=None)


def run_export_vm(aws_access: AwsAccess,
                  stack_name: str,
                  vm_image_formats: Tuple[str, ...],
                  asset_id: AssetId):
    """
    Runs export only of the VM image.
    """
    ec_instance_id = find_ec2_instance_in_cf_stack(aws_access, stack_name)
    export_vm(aws_access, ec_instance_id, vm_image_formats, asset_id)