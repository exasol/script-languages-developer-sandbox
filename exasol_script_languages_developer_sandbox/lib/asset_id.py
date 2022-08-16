BUCKET_PREFIX = "slc_developer_sandbox"


class AssetId:
    def __init__(self, asset_id: str):
        self._asset_id = asset_id

    @property
    def tag_value(self):
        return f"exa-slc-{self._asset_id}"

    @property
    def bucket_prefix(self):
        return f"{BUCKET_PREFIX}/{self._asset_id}"

    @property
    def ami_name(self):
        return f"Exasol-SLC-Developer-Sandbox-{self._asset_id}"
