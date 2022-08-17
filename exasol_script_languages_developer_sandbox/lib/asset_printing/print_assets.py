import fnmatch
from typing import Tuple, Optional, Any

import humanfriendly

from exasol_script_languages_developer_sandbox.lib.asset_id import AssetId, BUCKET_PREFIX
from exasol_script_languages_developer_sandbox.lib.asset_printing.mark_down_printer import MarkdownPrintingFactory
from exasol_script_languages_developer_sandbox.lib.asset_printing.printing_factory import PrintingFactory, TextObject, \
    HighlightedTextObject
from exasol_script_languages_developer_sandbox.lib.asset_printing.rich_console_printer import RichConsolePrintingFactory
from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess, get_value_safe
from enum import Enum

from exasol_script_languages_developer_sandbox.lib.tags import DEFAULT_TAG_KEY
from exasol_script_languages_developer_sandbox.lib.vm_bucket.vm_slc_bucket import find_vm_bucket


class AssetTypes(Enum):
    AMI = "ami"
    VM_S3 = "s3-object"
    SNAPSHOT = "snapshot"
    EXPORT_IMAGE_TASK = "export-image-task"
    CLOUDFORMATION = "cloudformation"
    EC2_KEY_PAIR = "ec2-key-pair"


def all_asset_types() -> Tuple[str, ...]:
    return tuple(asset_type.value for asset_type in AssetTypes)


def find_default_tag_value(aws_object: Any):
    return_value = "n/a"

    if "Tags" in aws_object:
        filtered_tags = [tag["Value"] for tag in aws_object["Tags"] if tag["Key"] == DEFAULT_TAG_KEY]
        if len(filtered_tags) == 1:
            return_value = filtered_tags[0]
    return return_value


def print_amis(aws_access: AwsAccess, filter_value: str, printing_factory: PrintingFactory):
    table_printer = printing_factory.create_table_printer(title=f"AMI Images (Filter={filter_value})")

    table_printer.add_column("Image-Id", style="blue", no_wrap=True)
    table_printer.add_column("Name", no_wrap=True)
    table_printer.add_column("Description", no_wrap=False)
    table_printer.add_column("Public", no_wrap=True)
    table_printer.add_column("ImageLocation", no_wrap=True)
    table_printer.add_column("CreationDate", style="magenta", no_wrap=True)
    table_printer.add_column("State", no_wrap=True)
    table_printer.add_column("Asset-Tag-Value", no_wrap=True)

    amis = aws_access.list_amis(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])
    for ami in amis:
        is_public = "yes" if ami["Public"] else "no"
        table_printer.add_row(ami["ImageId"], ami["Name"], ami["Description"], is_public,
                              ami["ImageLocation"], ami["CreationDate"], ami["State"], find_default_tag_value(ami))

    table_printer.finish()
    text_print = printing_factory.create_text_printer()

    text_print.print((TextObject("You can de-register AMI images using AWS CLI:\n"),
                     TextObject("'aws ec2 deregister-image --image-id "),
                     HighlightedTextObject("Image-Id"), TextObject("'")))
    text_print.print(tuple())


def print_snapshots(aws_access: AwsAccess, filter_value: str, printing_factory: PrintingFactory):
    table_printer = printing_factory.create_table_printer(title=f"EC-2 Snapshots (Filter={filter_value})")

    table_printer.add_column("SnapshotId", style="blue", no_wrap=True)
    table_printer.add_column("Description", no_wrap=False)
    table_printer.add_column("Progress", no_wrap=True)
    table_printer.add_column("VolumeId", no_wrap=True)
    table_printer.add_column("StartTime", style="magenta", no_wrap=True)
    table_printer.add_column("State", no_wrap=True)
    table_printer.add_column("Asset-Tag-Value", no_wrap=True)

    snapshots = aws_access.list_snapshots(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])
    for snapshot in snapshots:
        table_printer.add_row(snapshot["SnapshotId"], snapshot["Description"], snapshot["Progress"],
                              snapshot["VolumeId"], snapshot["StartTime"].strftime("%Y-%m-%d, %H:%M"),
                              snapshot["State"], find_default_tag_value(snapshot))

    table_printer.finish()

    text_print = printing_factory.create_text_printer()

    text_print.print((TextObject("You can remove snapshots using AWS CLI:\n"),
                     TextObject("'aws ec2 delete-snapshot --snapshot-id "),
                     HighlightedTextObject("SnapshotId"), TextObject("'")))
    text_print.print(tuple())


def print_export_image_tasks(aws_access: AwsAccess, filter_value: str, printing_factory: PrintingFactory):
    table_printer = printing_factory.create_table_printer(title=f"Export Image Tasks (Filter={filter_value})")

    table_printer.add_column("ExportImageTaskId", style="blue", no_wrap=True)
    table_printer.add_column("Description", no_wrap=False)
    table_printer.add_column("Progress", no_wrap=True)
    table_printer.add_column("S3ExportLocation - S3Bucket", no_wrap=True)
    table_printer.add_column("S3ExportLocation - S3Prefix", no_wrap=True)
    table_printer.add_column("Status", no_wrap=True)
    table_printer.add_column("StatusMessage", no_wrap=True)
    table_printer.add_column("Asset-Tag-Value", no_wrap=True)

    export_image_tasks = \
        aws_access.list_export_image_tasks(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])

    for export_image_task in export_image_tasks:
        export_location = export_image_task["S3ExportLocation"]
        s3bucket = export_location["S3Bucket"]
        s3prefix = export_location["S3Prefix"]
        table_printer.add_row(export_image_task["ExportImageTaskId"], export_image_task["Description"],
                              get_value_safe("Progress", export_image_task), s3bucket, s3prefix,
                              get_value_safe("Status", export_image_task),
                              get_value_safe("StatusMessage", export_image_task),
                              find_default_tag_value(export_image_task))

    table_printer.finish()
    text_print = printing_factory.create_text_printer()

    text_print.print((TextObject("You can cancel active tasks using AWS CLI:\n"),
                     TextObject("'aws ec2 cancel-export-task --export-task-id "),
                     HighlightedTextObject("ExportImageTaskId"), TextObject("'")))
    text_print.print(tuple())


def print_s3_objects(aws_access: AwsAccess, asset_id: Optional[AssetId], printing_factory: PrintingFactory):
    vm_bucket = find_vm_bucket(aws_access)

    if asset_id is not None:
        prefix = asset_id.bucket_prefix
    else:
        prefix = ""

    table_printer = printing_factory.create_table_printer(title=f"S3 Objects (Bucket={vm_bucket} Prefix={prefix})")

    table_printer.add_column("Key", no_wrap=True)
    table_printer.add_column("Size", no_wrap=True)
    table_printer.add_column("S3 URI", no_wrap=False)
    table_printer.add_column("URL", no_wrap=False)

    s3_objects = aws_access.list_s3_objects(bucket=vm_bucket, prefix=BUCKET_PREFIX)

    if s3_objects is not None and len(prefix) > 0:
        if prefix[-1] != "*":
            prefix = f"{prefix}*"
        s3_objects = [s3_object for s3_object in s3_objects if fnmatch.fnmatch(s3_object["Key"], prefix)]
    s3_bucket_location = aws_access.get_s3_bucket_location(bucket=vm_bucket)
    s3_bucket_uri = "s3://{bucket}/{{object}}".format(bucket=vm_bucket)
    https_bucket_url = "https://{bucket}.s3.{region}.amazonaws.com/{{object}}"\
        .format(bucket=vm_bucket, region=s3_bucket_location)

    if s3_objects is not None:
        for s3_object in s3_objects:
            obj_size = humanfriendly.format_size(s3_object["Size"])
            key = s3_object["Key"]
            s3_uri = s3_bucket_uri.format(object=key)
            https_url = https_bucket_url.format(object=key)
            table_printer.add_row(key, obj_size, s3_uri, https_url)

    table_printer.finish()


def cloudformation_stack_has_matching_tag(cloudformation_tag: dict, filter_value: str):
    if filter_value == "*":
        return True
    else:
        for tag in cloudformation_tag["Tags"]:
            tag_key = tag["Key"]
            tag_value = tag["Value"]
            if tag_key == DEFAULT_TAG_KEY and fnmatch.fnmatch(tag_value, filter_value):
                return True
    return False


def print_cloudformation_stacks(aws_access: AwsAccess, filter_value: str, printing_factory: PrintingFactory):
    table_printer = printing_factory.create_table_printer(title=f"Cloudformation stacks (Filter={filter_value})")

    table_printer.add_column("Stack-Name", style="blue", no_wrap=True)
    table_printer.add_column("Description", no_wrap=False)
    table_printer.add_column("StackStatus", no_wrap=True)
    table_printer.add_column("CreationTime", style="magenta", no_wrap=True)
    table_printer.add_column("PhysicalResourceId", no_wrap=False)
    table_printer.add_column("ResourceType", no_wrap=True)
    table_printer.add_column("Asset-Tag-Value", no_wrap=True)

    cloudformation_stack = aws_access.describe_stacks()

    relevant_stacks = [stack for stack in
                       cloudformation_stack if cloudformation_stack_has_matching_tag(stack, filter_value)]
    for stack in relevant_stacks:
        table_printer.add_row(stack["StackName"],
                              get_value_safe("Description", stack), stack["StackStatus"],
                              stack["CreationTime"].strftime("%Y-%m-%d, %H:%M"), "", "",
                              find_default_tag_value(stack))
        stack_resources = aws_access.get_all_stack_resources(stack_name=stack["StackName"])
        for stack_resource in stack_resources:
            table_printer.add_row("", "", "", "",
                                  stack_resource["PhysicalResourceId"], stack_resource["ResourceType"],
                                  find_default_tag_value(stack))

    table_printer.finish()
    text_print = printing_factory.create_text_printer()

    text_print.print((TextObject("You can remove a cf stack using AWS CLI:\n"),
                      TextObject("'aws cloudformation delete-stack --stack-name "),
                      HighlightedTextObject("Stack-Name/Stack-Id"), TextObject("'")))
    text_print.print(tuple())


def print_ec2_keys(aws_access: AwsAccess, filter_value: str, printing_factory: PrintingFactory):
    table_printer = printing_factory.create_table_printer(title=f"EC-2 Keys (Filter={filter_value})")

    table_printer.add_column("KeyPairId", style="blue", no_wrap=True)
    table_printer.add_column("KeyName", no_wrap=True)
    table_printer.add_column("CreateTime", style="magenta", no_wrap=True)
    table_printer.add_column("Asset-Tag-Value", no_wrap=True)

    key_pairs = aws_access.list_ec2_key_pairs(filters=[{'Name': f'tag:{DEFAULT_TAG_KEY}', 'Values': [filter_value]}])
    for key_pair in key_pairs:
        table_printer.add_row(key_pair["KeyPairId"], key_pair["KeyName"],
                              key_pair["CreateTime"].strftime("%Y-%m-%d, %H:%M"),
                              find_default_tag_value(key_pair))

    table_printer.finish()

    text_print = printing_factory.create_text_printer()

    text_print.print((TextObject("You can remove key-pairs using AWS CLI:\n"),
                     TextObject("'aws ec2 delete-key-pair --key-pair-id "),
                     HighlightedTextObject("KeyPairId"), TextObject("'")))
    text_print.print(tuple())


def print_with_printer(aws_access: AwsAccess, asset_id: Optional[AssetId],
                       asset_types: Tuple[str], filter_value: str, printing_factory: PrintingFactory):
    if AssetTypes.AMI.value in asset_types:
        print_amis(aws_access, filter_value, printing_factory)
    if AssetTypes.SNAPSHOT.value in asset_types:
        print_snapshots(aws_access, filter_value, printing_factory)
    if AssetTypes.EXPORT_IMAGE_TASK.value in asset_types:
        print_export_image_tasks(aws_access, filter_value, printing_factory)
    if AssetTypes.VM_S3.value in asset_types:
        print_s3_objects(aws_access, asset_id, printing_factory)
    if AssetTypes.CLOUDFORMATION.value in asset_types:
        print_cloudformation_stacks(aws_access, filter_value, printing_factory)
    if AssetTypes.EC2_KEY_PAIR.value in asset_types:
        print_ec2_keys(aws_access, filter_value, printing_factory)


def print_assets(aws_access: AwsAccess, asset_id: Optional[AssetId], outfile: Optional[str],
                 asset_types: Tuple[str] = all_asset_types()):
    if asset_id is None:
        filter_value = "*"
    else:
        filter_value = asset_id.tag_value

    if outfile is not None:
        with open(outfile, "w") as f:
            printing_factory = MarkdownPrintingFactory(f)
            print_with_printer(aws_access, asset_id, asset_types, filter_value, printing_factory)
    else:
        printing_factory = RichConsolePrintingFactory()
        print_with_printer(aws_access, asset_id, asset_types, filter_value, printing_factory)
