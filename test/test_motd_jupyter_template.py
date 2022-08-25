import json
import subprocess
from pathlib import Path
from typing import NamedTuple

import pytest
from jinja2 import Template


@pytest.fixture()
def motd_file(tmp_path):
    jupyter_server_config_file = tmp_path / "jupyter_server_config.json"
    python_file = tmp_path / "999_jupyter.py"

    src_path = Path(__file__).parent.parent / "exasol_script_languages_developer_sandbox" / "runtime" / \
               "ansible" / "roles" / "jupyter" / "templates" / "etc" /"update-motd.d" / "999-jupyter"
    with open(src_path, "r") as f:
        python_code_template = f.read()
    python_template = Template(python_code_template)

    class jupyterlab(NamedTuple):
        virtualenv = "dummy_env"
        password = "dummy_password"

    python_code = python_template.render(user_name="test_user", jupyterlab=jupyterlab(),
                                         jupyter_server_config_file=str(jupyter_server_config_file),
                                         server_hashed_password="dummy_password_hash")
    with open(python_file, "w") as f:
        f.write(python_code)
    yield python_file, jupyter_server_config_file




jupyter_update_msg_header = """
  _    _           _       _                                       _                   _              _____                                    _ _
 | |  | |         | |     | |                                     | |                 | |            |  __ \                                  | | |
 | |  | |_ __   __| | __ _| |_ ___   _   _  ___  _   _ _ __       | |_   _ _ __  _   _| |_ ___ _ __  | |__) |_ _ ___ _____      _____  _ __ __| | |
 | |  | | '_ \ / _` |/ _` | __/ _ \ | | | |/ _ \| | | | '__|  _   | | | | | '_ \| | | | __/ _ \ '__| |  ___/ _` / __/ __\ \ /\ / / _ \| '__/ _` | |
 | |__| | |_) | (_| | (_| | ||  __/ | |_| | (_) | |_| | |    | |__| | |_| | |_) | |_| | ||  __/ |    | |  | (_| \__ \__ \\ V  V / (_) | | | (_| |_|
  \____/| .__/ \__,_|\__,_|\__\___|  \__, |\___/ \__,_|_|     \____/ \__,_| .__/ \__, |\__\___|_|    |_|   \__,_|___/___/ \_/\_/ \___/|_|  \__,_(_)
        | |                           __/ |                               | |     __/ |
        |_|                          |___/                                |_|    |___/
"""


def test_motd_jupyter_template_prints_password_message(motd_file):
    """
    Test which runs the motd jupyter template and validates that the message is printed
    because the password matches.
    """
    python_file, jupyter_server_config_file = motd_file
    mock_data = {
        "ServerApp": {
        "password": "dummy_password_hash"
        }
    }
    with open(jupyter_server_config_file, "w") as f:
        json.dump(mock_data, f)

    result = subprocess.run(["python3", python_file], capture_output=True)
    assert jupyter_update_msg_header in result.stdout.decode("utf-8")


def test_motd_jupyter_template_prints_password_message_not_if_passward_was_changed(motd_file):
    """
    Test which runs the motd jupyter template and validates that the message is not printed
    because the password does not match.
    """
    python_file, jupyter_server_config_file = motd_file
    mock_data = {
        "ServerApp": {
        "password": "NOT_MATCHING_PASSWORD"
        }
    }
    with open(jupyter_server_config_file, "w") as f:
        json.dump(mock_data, f)

    result = subprocess.run(["python3", python_file], capture_output=True)
    assert result.stdout.decode("utf-8") == ""
