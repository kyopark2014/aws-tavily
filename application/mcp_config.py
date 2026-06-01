import logging
import sys
import utils
import os
import json
import boto3

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("mcp-config")

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

config = utils.load_config()
logger.info(f"config: {config}")

region = config["region"] if "region" in config else "us-west-2"
projectName = config["projectName"] if "projectName" in config else "mcp"
workingDir = os.path.dirname(os.path.abspath(__file__))
# 상위 디렉토리의 contents 폴더 경로 추가
parent_dir = os.path.dirname(workingDir)
contents_dir = os.path.join(parent_dir, "contents")
logger.info(f"workingDir: {workingDir}")
logger.info(f"contents_dir: {contents_dir}")

mcp_user_config = {}    

def get_agent_runtime_arn(mcp_type: str):
    #logger.info(f"mcp_type: {mcp_type}")
    agent_runtime_name = f"{projectName.lower().replace('-', '_')}_{mcp_type.replace('-', '_')}"
    logger.info(f"agent_runtime_name: {agent_runtime_name}")
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    response = client.list_agent_runtimes(
        maxResults=100
    )
    logger.info(f"response: {response}")
    
    agentRuntimes = response['agentRuntimes']
    for agentRuntime in agentRuntimes:
        if agentRuntime["agentRuntimeName"] == agent_runtime_name:
            logger.info(f"agent_runtime_name: {agent_runtime_name}, agentRuntimeArn: {agentRuntime["agentRuntimeArn"]}")
            return agentRuntime["agentRuntimeArn"]
    return None

def get_secret_value(secret_name):
    session = boto3.Session()
    client = session.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except client.exceptions.ResourceNotFoundException:
        logger.info(f"Secret not found, creating new secret: {secret_name}")
        try:
            # Create secret value with bearer_key 
            secret_value = {
                "key": secret_name,
                "value": "need to update"
            }
            
            # Convert to JSON string
            secret_string = json.dumps(secret_value)

            client.create_secret(
                Name=secret_name,
                SecretString=secret_string,  
                Description=f"secret key and token for {secret_name}"
            )
            logger.info(f"Secret created: {secret_name}. Please update it with the actual value.")
            return None
        except Exception as create_error:
            logger.error(f"Failed to create secret: {create_error}")
            return None
    except Exception as e:
        logger.error(f"Error getting secret value: {e}")
        return None

def load_config(mcp_type):
    if mcp_type == "s3_vector":
        mcp_type = "kb-retrieve"    
    
    if mcp_type == "kb-retrieve":
        return {
            "mcpServers": {
                "kb-retrieve": {
                    "command": "python",
                    "args": [f"{workingDir}/mcp_server_retrieve.py"]
                }
            }
        }
    
    elif mcp_type == "aws_documentation":
        return {
            "mcpServers": {
                "awslabs.aws-documentation-mcp-server": {
                    "command": "uvx",
                    "args": ["awslabs.aws-documentation-mcp-server@latest"],
                    "env": {
                        "FASTMCP_LOG_LEVEL": "ERROR"
                    }
                }
            }
        }

    elif mcp_type == "web_fetch":
        return {
            "mcpServers": {
                "web_fetch": {
                    "command": "npx",
                    "args": ["-y", "mcp-server-fetch-typescript"]
                }
            }
        }
    
    elif mcp_type == "text_extraction":
        return {
            "mcpServers": {
                "text_extraction": {
                    "command": "python",
                    "args": [f"{workingDir}/mcp_server_text_extraction.py"]
                }
            }
        }
    
    elif mcp_type == "aws-tavily":
        agent_arn = get_agent_runtime_arn(mcp_type)
        logger.info(f"mcp_type: {mcp_type}, agent_arn: {agent_arn}")
        if agent_arn is None:
            logger.warning(f"Agent runtime for '{mcp_type}' not found. Skipping MCP server. Ensure agent_runtime_{mcp_type.replace('-', '_')} is deployed.")
            return None
        encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
        
        mcp_url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        
        return {
            "mcpServers": {
                "tavily-search": {
                    "type": "streamable_http",
                    "url": mcp_url,
                    "auth": "bedrock_agentcore_sigv4",
                    "timeout_seconds": 180,
                    "sse_read_timeout_seconds": 300,
                    "headers": {
                        "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream",
                        "User-Agent": "aws-tavily-streamlit-mcp-client/1.0"
                    }
                }
            }
        }    
    
    elif mcp_type == "사용자 설정":
        return mcp_user_config

def load_selected_config(mcp_servers: dict):
    logger.info(f"mcp_servers: {mcp_servers}")
    
    loaded_config = {}
    for server in mcp_servers:
        config = load_config(server)
        if config:
            loaded_config.update(config["mcpServers"])
    return {
        "mcpServers": loaded_config
    }
