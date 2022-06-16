import logging

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.random_string_generator import get_random_str
from exasol_script_languages_developer_sandbox.lib.render_template import render_template


class CloudformationStack:
    """
    This class provides access to an AWS Cloudformation stack
    """

    def __init__(self, aws_access: AwsAccess):
        self._aws_access = aws_access
        self._stack_name = None

    @staticmethod
    def _generate_stack_name():
        return f"EC2-SLC-DEV-SANDBOX-{get_random_str(5)}"

    @property
    def stack_name(self):
        return self._stack_name

    def launch_ec2_stack(self, ec2_key_name) -> None:
        yml = render_template("ec2_cloudformation.jinja.yaml", key_name=ec2_key_name)
        self._stack_name = self._generate_stack_name()
        self._aws_access.upload_cloudformation_stack(yml, self._stack_name)
        logging.info(f"Deployed cloudformation stack {self._stack_name}")

    def get_ec2_instance_id(self) -> str:
        stack_resources = self._aws_access.get_all_stack_resources(self._stack_name)
        ec2_instance = [i for i in stack_resources if i["ResourceType"] == "AWS::EC2::Instance"]
        if len(ec2_instance) == 0:
            raise RuntimeError("Error starting or retrieving ec2 instance of stack %s" % self._stack_name)
        elif len(ec2_instance) > 1:
            raise RuntimeError("Multiple ec2 instances of stack %s" % self._stack_name)
        ec2_instance_id = ec2_instance[0]["PhysicalResourceId"]
        logging.info(f"Started EC2 with physical id {ec2_instance_id}")
        return ec2_instance_id

    def close(self) -> None:
        if self._stack_name is not None:
            self._aws_access.delete_stack(self._stack_name)
