import datetime
from unittest.mock import MagicMock, call

import pytest
from dateutil.tz import tzutc

from exasol_script_languages_developer_sandbox.lib.export_vm.run_export_vm import export_vm
from exasol_script_languages_developer_sandbox.lib.export_vm.vm_disk_image_format import all_vm_disk_image_formats, \
    VmDiskImageFormat
from exasol_script_languages_developer_sandbox.lib.vm_bucket.vm_slc_bucket import STACK_NAME
from test.conftest import DEFAULT_ASSET_ID

INSTANCE_ID = "test-instance"
TEST_ROLE_ID = 'VM-SLC-Bucket-VMImportRole-TEST'
TEST_BUCKET_ID = 'vm-slc-bucket-vmslcbucket-TEST'


def get_only_vm_stack_side_effect(stack_name: str):
    if stack_name == STACK_NAME:
        # The following is a snapshot from calling AwsAccess(a).get_all_stack_resources("VM-SLC-Bucket") on a running
        # cloudformation stack
        return [{'LogicalResourceId': 'VMImportRole',
                 'PhysicalResourceId': TEST_ROLE_ID,
                 'ResourceType': 'AWS::IAM::Role',
                 'LastUpdatedTimestamp': datetime.datetime(2022, 8, 11, 17, 15, 20, 380000, tzinfo=tzutc()),
                 'ResourceStatus': 'CREATE_COMPLETE', 'DriftInformation': {'StackResourceDriftStatus': 'NOT_CHECKED'}},
                {'LogicalResourceId': 'VMSLCBucket', 'PhysicalResourceId': TEST_BUCKET_ID,
                 'ResourceType': 'AWS::S3::Bucket',
                 'LastUpdatedTimestamp': datetime.datetime(2022, 8, 11, 17, 14, 55, 63000, tzinfo=tzutc()),
                 'ResourceStatus': 'CREATE_COMPLETE', 'DriftInformation': {'StackResourceDriftStatus': 'NOT_CHECKED'}}]
    else:
        raise ValueError(f"Unexpected parameter:{stack_name}")


TEST_AMI_ID = "AMI-IMAGE-12345"


def call_counter(func):
    def helper(*args, **kwargs):
        helper.calls += 1
        return func(helper.calls, *args, **kwargs)
    helper.calls = 0
    return helper


@call_counter
def get_ami_side_effect(counter: int, ami_id: str):
    if ami_id == TEST_AMI_ID:
        if counter < 3:
            state = "pending"
        else:
            state = "available"
        return {'Architecture': 'x86_64',
                'CreationDate': '2022-08-16T15:02:10.000Z',
                'ImageId': TEST_AMI_ID,
                'ImageLocation': '123/some_dummy_location',
                'ImageType': 'machine', 'Public': False, 'OwnerId': '123',
                'PlatformDetails': 'Linux/UNIX',
                'UsageOperation': 'RunInstances',
                'State': state,
                'BlockDeviceMappings':
                    [{'DeviceName': '/dev/sda1',
                      'Ebs':
                          {'DeleteOnTermination': True, 'SnapshotId': 'snap-0e4b4dcef3f806d84',
                           'VolumeSize': 100, 'VolumeType': 'gp2', 'Encrypted': False}
                      },
                     {'DeviceName': '/dev/sdb', 'VirtualName': 'ephemeral0'},
                     {'DeviceName': '/dev/sdc', 'VirtualName': 'ephemeral1'}],
                'Description': 'Image Description', 'EnaSupport': True,
                'Hypervisor': 'xen',
                'Name': DEFAULT_ASSET_ID.ami_name,
                'RootDeviceName': '/dev/sda1',
                'RootDeviceType': 'ebs', 'SriovNetSupport': 'simple',
                'Tags': [{'Key': 'exa_slc_id', 'Value': DEFAULT_ASSET_ID.tag_value}],
                'VirtualizationType': 'hvm'}
    else:
        raise ValueError(f"Unexpect parameter: {ami_id}")


@pytest.fixture
def aws_vm_export_mock():
    aws_access_mock = MagicMock()
    aws_access_mock.get_all_stack_resources.side_effect = get_only_vm_stack_side_effect
    aws_access_mock.create_image_from_ec2_instance.return_value = TEST_AMI_ID
    aws_access_mock.get_ami.side_effect = get_ami_side_effect
    return aws_access_mock


vm_formats = [
    (VmDiskImageFormat.VMDK,),
    (VmDiskImageFormat.VHD,),
    (VmDiskImageFormat.VHD, VmDiskImageFormat.VMDK),
    tuple(vm_format for vm_format in VmDiskImageFormat),
    tuple()
]


@pytest.mark.parametrize("vm_formats_to_test", vm_formats)
def test_export_vm(aws_vm_export_mock, default_asset_id, vm_formats_to_test):
    """"
    Test if function export_vm() will be invoked
    with expected values when we run_export_vm()
    """
    export_vm(aws_access=aws_vm_export_mock, instance_id=INSTANCE_ID,
              vm_image_formats=tuple(vm_image_format.value for vm_image_format in vm_formats_to_test),
              asset_id=default_asset_id)

    aws_vm_export_mock.create_image_from_ec2_instance.assert_called_once_with(INSTANCE_ID, name=default_asset_id.ami_name,
                                                                           tag_value=default_asset_id.tag_value,
                                                                           description="Image Description")

    expected_calls = [
        call(image_id=TEST_AMI_ID,
             tag_value=default_asset_id.tag_value,
             description="VM Description",
             role_name=TEST_ROLE_ID,
             disk_format=disk_format,
             s3_bucket=TEST_BUCKET_ID,
             s3_prefix=f"{default_asset_id.bucket_prefix}/")
        for disk_format in vm_formats_to_test]
    assert aws_vm_export_mock.export_ami_image_to_vm.call_args_list == expected_calls
