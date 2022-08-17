import logging
import time
from sys import stderr
from typing import Tuple

from exasol_script_languages_developer_sandbox.lib.asset_id import AssetId
from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.setup_ec2.cf_stack import find_ec2_instance_in_cf_stack
from exasol_script_languages_developer_sandbox.lib.asset_printing.print_assets import print_assets
from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format import VmDiskImageFormat
from exasol_script_languages_developer_sandbox.lib.vm_bucket.vm_slc_bucket import find_vm_bucket, find_vm_import_role


def export_vm_image(aws_access: AwsAccess, vm_image_format: VmDiskImageFormat, tag_value: str,
                    ami_id: str, vmimport_role: str, vm_bucket: str, bucket_prefix: str):
    """
    Exports an AMI (parameter ami_id) to a VM image in the given S3-Bucket (parameter vm_bucket)
    at prefix (parameter bucket_prefix). The format of the VM is given by parameter vm_image_format.
    The export-image-task will be tagged with parameter tag_value. This action requires a AWS-role with sufficient
    permissions; this role needs to be defined by parameter vmimport_role.
    """
    logging.info(f"export ami to vm with format '{vm_image_format}'")
    export_image_task_id = \
        aws_access.export_ami_image_to_vm(image_id=ami_id, tag_value=tag_value,
                                          description="VM Description", role_name=vmimport_role,
                                          disk_format=vm_image_format,
                                          s3_bucket=vm_bucket, s3_prefix=bucket_prefix)

    export_image_task = aws_access.get_export_image_task(export_image_task_id)

    logging.info(
        f"Started export of vm image to {vm_bucket}/{bucket_prefix}. "
        f"Status message is {export_image_task.status_message}.")
    last_progress = export_image_task.progress
    last_status = export_image_task.status
    while export_image_task.is_active:
        time.sleep(10)
        export_image_task = aws_access.get_export_image_task(export_image_task_id)
        if export_image_task.progress != last_progress or export_image_task.status != last_status:
            logging.info(f"still running export of vm image to {vm_bucket}/{bucket_prefix}. "
                         f"Status message is {export_image_task.status_message}. "
                         f"Progess is '{export_image_task.progress}'")
        last_progress = export_image_task.progress
        last_status = export_image_task.status
    if not export_image_task.is_completed:
        raise RuntimeError(f"Export of VM failed: status message was {export_image_task.status_message}")


def create_ami(aws_access: AwsAccess, ami_name: str, tag_value: str, instance_id: str) -> str:
    """
    Creates a new AMI with the given name (parameter ami_name) for the EC2-Instance identified by parameter instance_id.
    The AMI will be tagged with given tag_value.
    :raises RuntimeError if an error occured during creation of the AMI
    Returns the ami_id if the export-image-task succeeded.
    """
    logging.info(f"create ami with name '{ami_name}' and tag(s) '{tag_value}'")
    ami_id = aws_access.create_image_from_ec2_instance(instance_id, name=ami_name, tag_value=tag_value,
                                                       description="Image Description")

    ami = aws_access.get_ami(ami_id)
    while ami.is_pending:
        logging.info(f"ami  with name '{ami.name}' and tag(s) '{tag_value}'  still pending...")
        time.sleep(10)
        ami = aws_access.get_ami(ami_id)
    if ami.is_available:
        raise RuntimeError(f"Failed to create ami! ami state is '{ami.state}'")
    return ami_id


def export_vm(aws_access: AwsAccess,
              instance_id: str,
              vm_image_formats: Tuple[str, ...],
              asset_id: AssetId) -> None:
    vm_bucket = find_vm_bucket(aws_access)
    vmimport_role = find_vm_import_role(aws_access)
    tag_value = asset_id.tag_value
    bucket_prefix = f"{asset_id.bucket_prefix}/"
    has_errors = False
    try:
        try:
            ami_id = create_ami(aws_access, asset_id.ami_name, tag_value, instance_id)
        except Exception:
            logging.exception("Could not create AMI. Please remove snapshot if necessary!")
            has_errors = True
            return
        for vm_image_format in vm_image_formats:
            try:
                export_vm_image(aws_access, VmDiskImageFormat[vm_image_format], tag_value,
                                ami_id, vmimport_role, vm_bucket, bucket_prefix)
            except Exception:
                logging.exception(f"Failed to export VM to bucket {vm_bucket} at {bucket_prefix}\n")
                has_errors = True
                break
    finally:
        if has_errors:
            print(f"VM Export finished for: {asset_id.ami_name}. There were errors. "
                  f"You might want to delete some of the assets created.", file=stderr)
        else:
            print(f"VM Export finished for: {asset_id.ami_name} without any errors", file=stderr)
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
