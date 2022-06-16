from unittest.mock import MagicMock

import pytest

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.render_template import render_template
from exasol_script_languages_developer_sandbox.lib.run_setup_e2 import run_setup_ec2, STACK_NAME
from test.cloudformation_validation import validate_using_cfn_lint


@pytest.fixture
def ec2_cloudformation_yml():
    return render_template("ec2_cloudformation.jinja.yaml", key_name="test_key")


def test_deploy_ec2_upload_invoked(ec2_cloudformation_yml):
    """"
    Test if function upload_cloudformation_stack() will be invoked
    with expected values when we run run_deploy_ci_build()
    """
    aws_access_mock = MagicMock()
    run_setup_ec2(aws_access=aws_access_mock, ec2_key_file="invalid", ec2_key_name="test_key")
    aws_access_mock.upload_cloudformation_stack.assert_called_once_with(ec2_cloudformation_yml, STACK_NAME)


def test_deploy_ec2_template(ec2_cloudformation_yml):
    aws_access = AwsAccess(None)
    aws_access.validate_cloudformation_template(ec2_cloudformation_yml)


def test_deploy_cec2_template_with_cnf_lint(tmp_path, ec2_cloudformation_yml):
    validate_using_cfn_lint(tmp_path, ec2_cloudformation_yml)
