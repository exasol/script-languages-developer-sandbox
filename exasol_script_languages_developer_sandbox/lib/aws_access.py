import logging
import time
from typing import Optional, Any, List, Dict

import boto3
import botocore

from exasol_script_languages_developer_sandbox.lib.common import get_value_safe
from exasol_script_languages_developer_sandbox.lib.deployer import Deployer
from exasol_script_languages_developer_sandbox.lib.tags import create_default_asset_tag, DEFAULT_TAG_KEY
from exasol_script_languages_developer_sandbox.lib.vm_disk_image_format import VmDiskImageFormat


class AwsAccess(object):
    def __init__(self, aws_profile: Optional[str]):
        self._aws_profile = aws_profile

    @property
    def aws_profile_for_logging(self) -> str:
        if self._aws_profile is not None:
            return self._aws_profile
        else:
            return "{default}"

    @property
    def aws_profile(self) -> Optional[str]:
        return self._aws_profile

    def create_new_ec2_key_pair(self, key_name: str) -> str:
        """
        Create an EC-2 Key-Pair, identified by parameter 'key_name'
        """
        logging.debug(f"Running create_new_ec2_key_pair for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")
        key_pair = cloud_client.create_key_pair(KeyName=key_name)
        return str(key_pair['KeyMaterial'])

    def delete_ec2_key_pair(self, key_name: str) -> None:
        """
        Delete the EC-2 Key-Pair, given by parameter 'key_name'
        """
        logging.debug(f"Running delete_ec2_key_pair for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")
        cloud_client.delete_key_pair(KeyName=key_name)

    def upload_cloudformation_stack(self, yml: str, stack_name: str):
        """
        Deploy the cloudformation stack.
        """
        logging.debug(f"Running upload_cloudformation_stack for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("cloudformation")
        try:
            cfn_deployer = Deployer(cloudformation_client=cloud_client)
            result = cfn_deployer.create_and_wait_for_changeset(stack_name=stack_name, cfn_template=yml,
                                                                parameter_values=[],
                                                                capabilities=("CAPABILITY_IAM",), role_arn=None,
                                                                notification_arns=None, tags=tuple())
        except Exception as e:
            logging.error(f"Error creating changeset for cloud formation template: {e}")
            raise e
        try:
            cfn_deployer.execute_changeset(changeset_id=result.changeset_id, stack_name=stack_name)
            cfn_deployer.wait_for_execute(stack_name=stack_name, changeset_type=result.changeset_type)
        except Exception as e:
            logging.error(f"Error executing changeset for cloud formation template: {e}")
            logging.error(f"Run 'aws cloudformation describe-stack-events --stack-name {stack_name}' to get details.")
            raise e

    def validate_cloudformation_template(self, cloudformation_yml) -> None:
        """
        This function pushes the YAML to AWS Cloudformation for validation
        (see https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-validate-template.html)
        Pitfall: Boto3 expects the YAML string as parameter, whereas the AWS CLI expects the file URL as parameter.
        It requires to have the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables set correctly.
        """
        logging.debug(f"Running validate_cloudformation_template for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("cloudformation")
        cloud_client.validate_template(TemplateBody=cloudformation_yml)

    def _get_stack_resources(self, stack_name: str) -> List[Dict[str, str]]:
        cf_client = self._get_aws_client('cloudformation')
        current_result = cf_client.list_stack_resources(StackName=stack_name)
        result = current_result["StackResourceSummaries"]

        while "nextToken" in current_result:
            current_result = cf_client.list_stack_resources(StackName=stack_name, nextToken=current_result["nextToken"])
            result.extend(current_result["StackResourceSummaries"])
        return result

    def get_all_stack_resources(self, stack_name: str) -> List[Dict[str, str]]:
        """
        This functions uses Boto3 to get all AWS Cloudformation resources for a specific Cloudformation stack,
        identified by parameter `stack_name`.
        The AWS API truncates at a size of 1MB, and in order to get all chunks the method must be called
        passing the previous retrieved token until no token is returned.
        """
        logging.debug(f"Running get_all_codebuild_projects for aws profile {self.aws_profile_for_logging}")
        return self._get_stack_resources(stack_name=stack_name)

    def stack_exists(self, stack_name: str) -> bool:
        """
        This functions uses Boto3 to check if stack with name `stack_name` exists.
        """
        logging.debug(f"Running stack_exists for aws profile {self.aws_profile_for_logging}")
        try:
            result = self._get_stack_resources(stack_name=stack_name)
            return any([res["ResourceStatus"] != "DELETE_COMPLETE" for res in result])
        except botocore.exceptions.ClientError:
            return False

    def delete_stack(self, stack_name: str) -> None:
        """
        This functions uses Boto3 to delete a stack identified by parameter "stack_name".
        """
        logging.debug(f"Running delete_stack for aws profile {self.aws_profile_for_logging}")
        cf_client = self._get_aws_client('cloudformation')
        cf_client.delete_stack(StackName=stack_name)

    def describe_instance(self, instance_id: str):
        """
        Describes an AWS instance identified by parameter instance_id
        """
        logging.debug(f"Running describe_instance for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")
        return cloud_client.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]

    def create_image_from_ec2_instance(self, instance_id: str, name: str, tag_value: str, description: str) -> str:
        """
        Creates an AMI image from an EC-2 instance
        """
        logging.debug(f"Running create_image_from_ec2_instance for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")
        tags = [{"ResourceType": "image", "Tags": create_default_asset_tag(tag_value)},
                {"ResourceType": "snapshot", "Tags": create_default_asset_tag(tag_value)}]

        result = cloud_client.create_image(Name=name, InstanceId=instance_id, Description=description,
                                           NoReboot=False, TagSpecifications=tags)
        return result["ImageId"]

    def export_ami_image_to_vm(self, image_id: str, tag_value: str,
                               description: str, role_name: str, disk_format: VmDiskImageFormat,
                               s3_bucket: str, s3_prefix: str) -> None:
        """
        Creates an AMI image from an EC-2 instance
        """
        logging.debug(f"Running create_image_from_ec2_instance for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")
        tags = [{"ResourceType": "export-image-task", "Tags": create_default_asset_tag(tag_value)}]
        result = cloud_client.export_image(ImageId=image_id, Description=description,
                                           RoleName=role_name, DiskImageFormat=disk_format.value,
                                           S3ExportLocation={"S3Bucket": s3_bucket, "S3Prefix": s3_prefix},
                                           TagSpecifications=tags)

        export_image_task_id, status, status_message = \
            result["ExportImageTaskId"], result["Status"], result["StatusMessage"]
        logging.info(f"Started export of vm image to {s3_bucket}/{s3_prefix}. Status message is {status_message}.")
        last_progress = None
        last_status = status
        while status == "active":
            time.sleep(10)
            result = cloud_client.describe_export_image_tasks(ExportImageTaskIds=[export_image_task_id])
            assert "NextToken" not in result #We expect only one result
            export_image_tasks = result["ExportImageTasks"]
            if len(export_image_tasks) != 1:
                raise RuntimeError(f"Unexpected number of export image tasks: {export_image_tasks}")
            export_image_task = export_image_tasks[0]
            status = export_image_task["Status"]
            status_message = get_value_safe("StatusMessage", export_image_task)
            progress = get_value_safe("Progress", export_image_task)

            if progress != last_progress or status != last_status:
                logging.info(f"still running export of vm image to {s3_bucket}/{s3_prefix}. "
                             f"Status message is {status_message}. Progess is '{progress}'")
            last_progress = progress
            last_status = status
        if status != "completed":
            raise RuntimeError(f"Export of VM failed: status message was {status_message}")

    def list_amis(self, filters: list) -> list:
        """
        List AMI images with given tag filter
        """
        logging.debug(f"Running list_amis for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")

        response = cloud_client.describe_images(Filters=filters)
        return response["Images"]

    def list_snapshots(self, filters: list) -> list:
        """
        List EC2 volume snapthos with given tag filter
        """
        logging.debug(f"Running list_snapshots for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")

        response = cloud_client.describe_snapshots(Filters=filters)
        assert "NextToken" not in response
        return response["Snapshots"]

    def list_export_image_tasks(self, filters: list) -> list:
        """
        List export image tasks with given tag filter
        """
        logging.debug(f"Running list_export_image_tasks for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("ec2")

        response = cloud_client.describe_export_image_tasks(Filters=filters)
        assert "NextToken" not in response
        return response["ExportImageTasks"]

    def list_s3_objects(self, bucket: str, prefix: str) -> list:
        """
        List s3 objects images with given tag filter
        """
        logging.debug(f"Running list_s3_objects for aws profile {self.aws_profile_for_logging}")
        cloud_client = self._get_aws_client("s3")

        response = cloud_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" in response:
            return response["Contents"]

    def get_user(self) -> str:
        """
        Return the current IAM user name.
        """
        iam_client = self._get_aws_client("iam")
        cu = iam_client.get_user()
        return cu["User"]["UserName"]

    def _get_aws_client(self, service_name: str) -> Any:
        if self._aws_profile is None:
            return boto3.client(service_name)
        aws_session = boto3.session.Session(profile_name=self._aws_profile)
        return aws_session.client(service_name)
