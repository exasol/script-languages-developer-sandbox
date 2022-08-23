import logging

from exasol_script_languages_developer_sandbox.lib.aws_access.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.render_template import render_template

STACK_NAME = "CI-TEST-CODEBUILD"


def run_setup_ci_codebuild(aws_access: AwsAccess) -> None:
    yml = render_template("ci_code_build.jinja.yaml")
    aws_access.upload_cloudformation_stack(yml, STACK_NAME)
    logging.info(f"Deployed cloudformation stack {STACK_NAME}")

