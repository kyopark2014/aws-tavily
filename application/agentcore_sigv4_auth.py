"""AWS SigV4 signing for Bedrock AgentCore streamable-HTTP MCP clients."""

from collections.abc import Generator

import boto3
import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials

BEDROCK_AGENTCORE_SERVICE = "bedrock-agentcore"


class SigV4HTTPXAuth(httpx.Auth):
    """Sign httpx requests with AWS SigV4 (sync and async)."""

    def __init__(self, credentials: Credentials, service: str, region: str) -> None:
        self.signer = SigV4Auth(credentials, service, region)

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        headers = dict(request.headers)
        headers.pop("connection", None)

        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )
        self.signer.add_auth(aws_request)
        request.headers.update(dict(aws_request.headers))
        yield request


def get_bedrock_agentcore_sigv4_auth(region: str) -> SigV4HTTPXAuth:
    creds = boto3.Session().get_credentials()
    if creds is None:
        raise RuntimeError("AWS credentials not found; configure credentials for AgentCore MCP access.")
    return SigV4HTTPXAuth(creds.get_frozen_credentials(), BEDROCK_AGENTCORE_SERVICE, region)
