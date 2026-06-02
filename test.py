import json
from pathlib import Path

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

cfg_path = Path(__file__).resolve().parent / "application" / "config.json"
with open(cfg_path) as f:
    cfg = json.load(f)

region = cfg['region']
arn = cfg['agent_runtime_arn']
encoded_arn = requests.utils.quote(arn, safe='')

url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"

payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "tavily_search",
        "arguments": {"query": "latest AI news", "max_results": 3}
    }
})

session = boto3.Session()
creds = session.get_credentials().get_frozen_credentials()

req = AWSRequest(
    method='POST',
    url=url,
    data=payload,
    headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    }
)
SigV4Auth(creds, 'bedrock-agentcore', region).add_auth(req)

resp = requests.post(url, data=payload, headers=dict(req.headers), timeout=60)
print(f"Status: {resp.status_code}")
print(resp.text[:5000])
