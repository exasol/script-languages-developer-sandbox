import logging
import os
from tempfile import mkstemp
from typing import Optional

from exasol_script_languages_developer_sandbox.lib.aws_access import AwsAccess
from exasol_script_languages_developer_sandbox.lib.random_string_generator import get_random_str


class KeyFileManager:
    def __init__(self, aws_access: AwsAccess,
                 external_ec2_key_name: Optional[str], external_ec2_key_file: Optional[str]):
        self._ec2_key_file = external_ec2_key_file
        self._aws_access = aws_access
        self._remove_key_on_close = False
        if self._ec2_key_file is None:
            logging.debug("Creating new key-pair")
            self._key_name = f"ec2-key-{get_random_str(10)}"
            ec2_key_file_handle, self._ec2_key_file = mkstemp(text=True)
            with os.fdopen(ec2_key_file_handle, 'w') as f:
                f.write(aws_access.create_new_ec2_key_pair(key_name=self._key_name))
            self._remove_key_on_close = True
            logging.debug(f"Created new key-pair: key-name={self._key_name}, key-file={self._ec2_key_file}")
            os.chmod(self._ec2_key_file, 0o400)
        else:
            logging.debug("Using existing key-pair")
            self._key_name = external_ec2_key_name

    @property
    def key_file_location(self):
        return self._ec2_key_file

    @property
    def key_name(self):
        return self._key_name

    def close(self):
        if self._remove_key_on_close:
            os.remove(self._ec2_key_file)
            self._aws_access.delete_ec2_key_pair(key_name=self._key_name)
