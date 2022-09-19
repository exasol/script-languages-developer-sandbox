class CfDistribution:
    """
    Simplifies access to objects returned from:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudfront.html#CloudFront.Client.get_distribution
    """

    def __init__(self, aws_object):
        self._aws_object = aws_object


    @property
    def id(self) -> str:
        return self._aws_object["Id"]

    @property
    def domain_name(self) -> str:
        return self._aws_object["DomainName"]
