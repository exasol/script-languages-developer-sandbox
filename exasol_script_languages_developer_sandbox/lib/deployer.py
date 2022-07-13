# Copyright 2012-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

#Source: https://github.com/aws/aws-cli/blob/e1f7196ad7859a8144f0313fa4b407da5ae8b101/awscli/customizations/cloudformation/deployer.py

import time
import logging
import botocore
import collections

from datetime import datetime

from botocore.exceptions import ValidationError

LOG = logging.getLogger(__name__)

ChangeSetResult = collections.namedtuple(
    "ChangeSetResult", ["changeset_id", "changeset_type"])


class Deployer(object):

    def __init__(self, cloudformation_client,
                 changeset_prefix="slc-ci-setup-deploy-"):
        self._client = cloudformation_client
        self.changeset_prefix = changeset_prefix

    def has_stack(self, stack_name):
        """
        Checks if a CloudFormation stack with given name exists

        :param stack_name: Name or ID of the stack
        :return: True if stack exists. False otherwise
        """
        try:
            resp = self._client.describe_stacks(StackName=stack_name)
            if len(resp["Stacks"]) != 1:
                return False

            # When you run CreateChangeSet on a a stack that does not exist,
            # CloudFormation will create a stack and set it's status
            # REVIEW_IN_PROGRESS. However this stack is cannot be manipulated
            # by "update" commands. Under this circumstances, we treat like
            # this stack does not exist and call CreateChangeSet will
            # ChangeSetType set to CREATE and not UPDATE.
            stack = resp["Stacks"][0]
            return stack["StackStatus"] != "REVIEW_IN_PROGRESS"

        except botocore.exceptions.ClientError as e:
            # If a stack does not exist, describe_stacks will throw an
            # exception. Unfortunately we don't have a better way than parsing
            # the exception msg to understand the nature of this exception.
            msg = str(e)

            if "Stack with id {0} does not exist".format(stack_name) in msg:
                LOG.debug("Stack with id {0} does not exist".format(
                    stack_name))
                return False
            else:
                # We don't know anything about this exception. Don't handle
                LOG.debug("Unable to get stack details.", exc_info=e)
                raise e

    def create_changeset(self, stack_name, cfn_template,
                         parameter_values, capabilities, role_arn,
                         notification_arns, tags):
        """
        Call Cloudformation to create a changeset and wait for it to complete

        :param stack_name: Name or ID of stack
        :param cfn_template: CloudFormation template string
        :param parameter_values: Template parameters object
        :param capabilities: Array of capabilities passed to CloudFormation
        :param tags: Array of tags passed to CloudFormation
        :return:
        """

        now = datetime.utcnow().isoformat()
        description = "Created by AWS CLI at {0} UTC".format(now)

        # Each changeset will get a unique name based on time
        changeset_name = self.changeset_prefix + str(int(time.time()))

        if not self.has_stack(stack_name):
            changeset_type = "CREATE"
            # When creating a new stack, UsePreviousValue=True is invalid.
            # For such parameters, users should either override with new value,
            # or set a Default value in template to successfully create a stack.
            parameter_values = [x for x in parameter_values
                                if not x.get("UsePreviousValue", False)]
        else:
            changeset_type = "UPDATE"
            # UsePreviousValue not valid if parameter is new
            summary = self._client.get_template_summary(StackName=stack_name)
            existing_parameters = [parameter['ParameterKey'] for parameter in
                                   summary['Parameters']]
            parameter_values = [x for x in parameter_values
                                if not (x.get("UsePreviousValue", False) and
                                        x["ParameterKey"] not in existing_parameters)]

        kwargs = {
            'ChangeSetName': changeset_name,
            'StackName': stack_name,
            'TemplateBody': cfn_template,
            'ChangeSetType': changeset_type,
            'Parameters': parameter_values,
            'Capabilities': capabilities,
            'Description': description,
            'Tags': tags,
        }

        # don't set these arguments if not specified to use existing values
        if role_arn is not None:
            kwargs['RoleARN'] = role_arn
        if notification_arns is not None:
            kwargs['NotificationARNs'] = notification_arns
        try:
            resp = self._client.create_change_set(**kwargs)
            return ChangeSetResult(resp["Id"], changeset_type)
        except Exception as ex:
            LOG.debug("Unable to create changeset", exc_info=ex)
            raise ex

    def wait_for_changeset(self, changeset_id, stack_name):
        """
        Waits until the changeset creation completes

        :param changeset_id: ID or name of the changeset
        :param stack_name:   Stack name
        :return: Latest status of the create-change-set operation
        """
        LOG.info("Waiting for changeset to be created..")

        # Wait for changeset to be created
        waiter = self._client.get_waiter("change_set_create_complete")
        # Poll every 5 seconds. Changeset creation should be fast
        waiter_config = {'Delay': 5}
        try:
            waiter.wait(ChangeSetName=changeset_id, StackName=stack_name,
                        WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Create changeset waiter exception", exc_info=ex)

            resp = ex.last_response
            status = resp["Status"]
            reason = resp["StatusReason"]

            raise RuntimeError("Failed to create the changeset: {0} "
                               "Status: {1}. Reason: {2}"
                               .format(ex, status, reason)) from ex

    def execute_changeset(self, changeset_id, stack_name,
                          disable_rollback=False):
        """
        Calls CloudFormation to execute changeset

        :param changeset_id: ID of the changeset
        :param stack_name: Name or ID of the stack
        :param disable_rollback: Disable rollback of all resource changes
        :return: Response from execute-change-set call
        """
        return self._client.execute_change_set(
            ChangeSetName=changeset_id,
            StackName=stack_name,
            DisableRollback=disable_rollback)

    def wait_for_execute(self, stack_name, changeset_type):

        LOG.info("Waiting for stack create/update to complete\n")

        # Pick the right waiter
        if changeset_type == "CREATE":
            waiter = self._client.get_waiter("stack_create_complete")
        elif changeset_type == "UPDATE":
            waiter = self._client.get_waiter("stack_update_complete")
        else:
            raise RuntimeError("Invalid changeset type {0}"
                               .format(changeset_type))

        # Poll every 30 seconds. Polling too frequently risks hitting rate limits
        # on CloudFormation's DescribeStacks API
        waiter_config = {
            'Delay': 30,
            'MaxAttempts': 120,
        }

        try:
            waiter.wait(StackName=stack_name, WaiterConfig=waiter_config)
        except botocore.exceptions.WaiterError as ex:
            LOG.debug("Execute changeset waiter exception", exc_info=ex)
            raise RuntimeError("Execute changeset waiter exception", ex)

    def create_and_wait_for_changeset(self, stack_name, cfn_template,
                                      parameter_values, capabilities, role_arn,
                                      notification_arns, tags):

        result = self.create_changeset(
            stack_name, cfn_template, parameter_values, capabilities,
            role_arn, notification_arns, tags)
        self.wait_for_changeset(result.changeset_id, stack_name)

        return result
