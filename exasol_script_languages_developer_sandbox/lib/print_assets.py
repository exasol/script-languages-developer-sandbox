from typing import Tuple

import humanfriendly

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from enum import Enum
from rich.console import Console
from rich.table import Table

from exasol_script_languages_developer_sandbox.lib.common import get_value_safe
from exasol_script_languages_developer_sandbox.lib.render_template import render_template
from exasol_script_languages_developer_sandbox.lib.tags import DEFAULT_TAG_KEY
from exasol_script_languages_developer_sandbox.lib.vm_slc_bucket import find_vm_bucket, get_bucket_prefix


class AssetTypes(Enum):
    AMI = "ami",
    VM_S3 = "s3-object",
    SNAPSHOT = "snapshot",
    EXPORT_IMAGE_TASK = "export-image-task"


def all_asset_types() -> Tuple[str, ...]:
    return tuple(asset_type.value for asset_type in AssetTypes)


def print_amis(aws_access: AwsAccess, filter_value: str):
    table = Table(title=f"AMI Images (Filter={filter_value})")

    table.add_column("Image-Id", style="blue", no_wrap=True)
    table.add_column("Name", no_wrap=True)
    table.add_column("Description", no_wrap=False)
    table.add_column("Public", no_wrap=True)
    table.add_column("ImageLocation", no_wrap=True)
    table.add_column("CreationDate", style="magenta", no_wrap=True)
    table.add_column("State", no_wrap=True)

    console = Console()
    amis = aws_access.list_amis(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])
    for ami in amis:
        is_public = "yes" if ami["Public"] else "no"
        table.add_row(ami["ImageId"], ami["Name"], ami["Description"], is_public,
                      ami["ImageLocation"], ami["CreationDate"], ami["State"])

    console.print(table)


def print_snapshots(aws_access: AwsAccess, filter_value: str):
    table = Table(title=f"EC-2 Snapshots (Filter={filter_value})")

    table.add_column("SnapshotId", style="blue", no_wrap=True)
    table.add_column("Description", no_wrap=False)
    table.add_column("Progress", no_wrap=True)
    table.add_column("VolumeId", no_wrap=True)
    table.add_column("StartTime", style="magenta", no_wrap=True)
    table.add_column("State", no_wrap=True)

    console = Console()
    snapshots = aws_access.list_snapshots(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])
    for snapshot in snapshots:
        table.add_row(snapshot["SnapshotId"], snapshot["Description"], snapshot["Progress"],
                      snapshot["VolumeId"], snapshot["StartTime"].strftime("%Y-%m-%d, %H:%M"), snapshot["State"])

    console.print(table)


def print_export_image_tasks(aws_access: AwsAccess, filter_value: str):
    table = Table(title=f"Export Image Tasks (Filter={filter_value})")

    table.add_column("ExportImageTaskId", style="blue", no_wrap=True)
    table.add_column("Description", no_wrap=False)
    table.add_column("Progress", no_wrap=True)
    table.add_column("S3ExportLocation - S3Bucket", no_wrap=True)
    table.add_column("S3ExportLocation - S3Prefix", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("StatusMessage", no_wrap=True)

    console = Console()
    export_image_tasks = \
        aws_access.list_export_image_tasks(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])

    for export_image_task in export_image_tasks:
        export_location = export_image_task["S3ExportLocation"]
        s3bucket = export_location["S3Bucket"]
        s3prefix = export_location["S3Prefix"]
        table.add_row(export_image_task["ExportImageTaskId"], export_image_task["Description"],
                      get_value_safe("Progress", export_image_task), s3bucket, s3prefix,
                      get_value_safe("Status", export_image_task), get_value_safe("StatusMessage", export_image_task))

    console.print(table)


def print_s3_objects(aws_access: AwsAccess, slc_version: str, name_suffix: str):
    vm_bucket = find_vm_bucket(aws_access)

    if len(slc_version) > 0:
        prefix = get_bucket_prefix(slc_version=slc_version, name_suffix=name_suffix)
    else:
        prefix = ""
    table = Table(title=f"S3 Objects (Bucket={vm_bucket} Prefix={prefix})")

    table.add_column("Key", no_wrap=False)
    table.add_column("Size", no_wrap=True)

    console = Console()
    s3_objects = aws_access.list_s3_objects(bucket=vm_bucket, prefix=prefix)

    for s3_object in s3_objects:
        obj_size = humanfriendly.format_size(s3_object["Size"])
        table.add_row(s3_object["Key"], obj_size)

    console.print(table)


def print_assets(aws_access: AwsAccess, slc_version: str, name_suffix: str,
                 asset_types: Tuple[str] = all_asset_types()):
    if len(slc_version) == 0:
        filter_value = "*"
    else:
        filter_value = render_template("aws_tag_value.jinja", slc_version=slc_version, suffix=name_suffix).strip("\n")

    if AssetTypes.AMI.value in asset_types:
        print_amis(aws_access, filter_value)
    if AssetTypes.SNAPSHOT.value in asset_types:
        print_snapshots(aws_access, filter_value)
    if AssetTypes.EXPORT_IMAGE_TASK.value in asset_types:
        print_export_image_tasks(aws_access, filter_value)
    if AssetTypes.VM_S3.value in asset_types:
        print_s3_objects(aws_access, slc_version, name_suffix)
