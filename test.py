from exasol_script_languages_developer_sandbox.lib.asset_id import AssetId
from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.export_vm.rename_s3_objects import rename_s3_object
from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format import VmDiskImageFormat

aws_access = AwsAccess(aws_profile="exa_individual_mfa")
asset_id = AssetId("test-v0.7")
export_image_task = aws_access.get_export_image_task(export_image_task_id="export-ami-0880eef25c60c8c17")

vm_image_format = VmDiskImageFormat.VHD
rename_s3_object(aws_access, export_image_task, vm_image_format, asset_id)
