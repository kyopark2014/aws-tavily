#!/usr/bin/env python3
"""
Unified uninstallation script
Sequentially deletes resources created by installer.py:
  AgentCore runtime -> IAM role -> IAM policy
Uses config.json (same naming rules as installer.py). No ECR cleanup — installer uses a pre-built image.
"""

import sys
import os
import json
import time
import argparse
import boto3
from botocore.exceptions import ClientError

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.json")

INSTALLER_CONFIG_KEYS = (
    "agent_runtime_arn",
    "agent_runtime_role",
    "container_image_uri",
)


def load_config():
    """Load config.json file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to parse config.json file: {e}")
        print("Error: config.json file is required for uninstallation")
        return None


def runtime_name_from_config(config):
    """Derive agent runtime name using the same rules as installer.py."""
    project_name = config.get("projectName")
    current_folder_name = os.path.basename(os.getcwd())
    repository_name = f"{project_name}_{current_folder_name}"
    return repository_name.replace("-", "_")


def clear_installer_config():
    """Remove keys written by installer.py from config.json."""
    try:
        config = load_config()
        if not config:
            return False
        for key in INSTALLER_CONFIG_KEYS:
            config.pop(key, None)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print("✓ Removed installer keys from config.json")
        return True
    except Exception as e:
        print(f"Warning: Failed to update config.json: {e}")
        return False


# ============================================================================
# Agent Runtime Deletion Functions
# ============================================================================

def delete_agent_runtime():
    """Delete AgentCore runtime and wait for deletion to complete."""
    print(f"\n{'='*60}")
    print("Deleting AgentCore runtime")
    print(f"{'='*60}")

    try:
        config = load_config()
        if not config:
            return False

        aws_region = config.get("region")
        project_name = config.get("projectName")
        agent_runtime_arn = config.get("agent_runtime_arn")

        if not all([aws_region, project_name]):
            print("Error: Missing required configuration in config.json")
            print("Required: region, projectName")
            return False

        runtime_name = runtime_name_from_config(config)
        client = boto3.client("bedrock-agentcore-control", region_name=aws_region)
        deletion_requested = False
        actual_runtime_name = None
        runtime_id = None

        if agent_runtime_arn:
            runtime_id = agent_runtime_arn.split("/")[-1] if "/" in agent_runtime_arn else None

        if runtime_id:
            try:
                client.delete_agent_runtime(agentRuntimeId=runtime_id)
                print(f"✓ Agent runtime deletion requested: {agent_runtime_arn}")
                deletion_requested = True
                actual_runtime_name = runtime_name
            except ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    print(f"Agent runtime not found (may already be deleted): {agent_runtime_arn}")
                    return True
                print(f"Error deleting agent runtime: {e}")
                return False

        if not deletion_requested:
            response = client.list_agent_runtimes()
            for agent_runtime in response.get("agentRuntimes", []):
                if agent_runtime["agentRuntimeName"] == runtime_name:
                    runtime_id = agent_runtime["agentRuntimeId"]
                    actual_runtime_name = agent_runtime["agentRuntimeName"]
                    try:
                        client.delete_agent_runtime(agentRuntimeId=runtime_id)
                        print(
                            f"✓ Agent runtime deletion requested: "
                            f"{agent_runtime['agentRuntimeArn']}"
                        )
                        deletion_requested = True
                        break
                    except ClientError as e:
                        if e.response["Error"]["Code"] == "ResourceNotFoundException":
                            print(
                                f"Agent runtime not found (may already be deleted): "
                                f"{actual_runtime_name}"
                            )
                            return True
                        print(f"Error deleting agent runtime: {e}")
                        return False

            if not deletion_requested:
                print(f"Agent runtime {runtime_name} not found (may already be deleted)")
                return True

        name_to_check = actual_runtime_name or runtime_name
        return wait_for_runtime_deletion(config, name_to_check)

    except Exception as e:
        print(f"Error deleting agent runtime: {e}")
        return False


def wait_for_runtime_deletion(config, runtime_name, max_wait_time=600):
    """Wait for AgentCore runtime to be completely deleted (check every 10 seconds)."""
    aws_region = config.get("region")
    if not aws_region:
        print("Error: region not found in config.json")
        return False

    print(f"\nWaiting for AgentCore runtime '{runtime_name}' to be deleted...")
    print("Checking every 10 seconds...")

    client = boto3.client("bedrock-agentcore-control", region_name=aws_region)
    start_time = time.time()
    check_count = 0

    while True:
        check_count += 1
        elapsed_time = time.time() - start_time

        try:
            response = client.list_agent_runtimes()
            runtime_exists = any(
                r["agentRuntimeName"] == runtime_name
                for r in response.get("agentRuntimes", [])
            )

            if not runtime_exists:
                print(f"✓ AgentCore runtime '{runtime_name}' has been successfully deleted")
                print(f"  (Checked {check_count} times, elapsed time: {elapsed_time:.1f} seconds)")
                return True

            if elapsed_time >= max_wait_time:
                print(
                    f"\nTimeout: AgentCore runtime '{runtime_name}' still exists after "
                    f"{max_wait_time} seconds"
                )
                print("  Please check manually or try again later")
                return False

            print(
                f"  [{check_count}] Runtime still exists, waiting 10 seconds... "
                f"(elapsed: {elapsed_time:.1f}s)"
            )
            time.sleep(10)

        except Exception as e:
            print(f"Error checking runtime status: {e}")
            return False


# ============================================================================
# IAM Role and Policy Deletion Functions
# ============================================================================

def detach_policy_from_role(role_name, policy_arn):
    """Detach policy from IAM role."""
    try:
        iam_client = boto3.client("iam")
        iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        print(f"✓ Policy detached successfully: {policy_arn}")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            print(f"Policy not attached to role (may already be detached): {policy_arn}")
            return True
        print(f"Policy detachment failed: {e}")
        return False
    except Exception as e:
        print(f"Policy detachment failed: {e}")
        return False


def delete_iam_role(config):
    """Delete IAM role created by installer.py."""
    project_name = config.get("projectName", "agentcore")
    role_name = f"AmazonBedrockAgentCoreRuntimeRoleFor{project_name}"

    try:
        iam_client = boto3.client("iam")
        existing_role = iam_client.get_role(RoleName=role_name)
        role_arn = existing_role["Role"]["Arn"]

        attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
        for policy in attached_policies.get("AttachedPolicies", []):
            detach_policy_from_role(role_name, policy["PolicyArn"])

        inline_policies = iam_client.list_role_policies(RoleName=role_name)
        for policy_name in inline_policies.get("PolicyNames", []):
            try:
                iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
                print(f"✓ Deleted inline policy: {policy_name}")
            except Exception as e:
                print(f"Warning: Failed to delete inline policy {policy_name}: {e}")

        iam_client.delete_role(RoleName=role_name)
        print(f"✓ IAM role deleted: {role_arn}")
        return True

    except iam_client.exceptions.NoSuchEntityException:
        print(f"IAM role {role_name} not found (may already be deleted)")
        return True
    except Exception as e:
        print(f"Role deletion failed: {e}")
        return False


def delete_iam_policy(config):
    """Delete IAM policy created by installer.py."""
    account_id = config.get("accountId")
    project_name = config.get("projectName", "agentcore")
    policy_name = f"AmazonBedrockAgentCoreRuntimePolicyFor{project_name}"
    policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"

    try:
        iam_client = boto3.client("iam")
        iam_client.get_policy(PolicyArn=policy_arn)

        versions_response = iam_client.list_policy_versions(PolicyArn=policy_arn)
        for version in versions_response["Versions"]:
            if not version["IsDefaultVersion"]:
                try:
                    iam_client.delete_policy_version(
                        PolicyArn=policy_arn,
                        VersionId=version["VersionId"],
                    )
                    print(f"✓ Deleted policy version: {version['VersionId']}")
                except Exception as e:
                    print(f"Warning: Failed to delete policy version {version['VersionId']}: {e}")

        iam_client.delete_policy(PolicyArn=policy_arn)
        print(f"✓ IAM policy deleted: {policy_arn}")
        return True

    except iam_client.exceptions.NoSuchEntityException:
        print(f"IAM policy {policy_name} not found (may already be deleted)")
        return True
    except Exception as e:
        print(f"Policy deletion failed: {e}")
        return False


def delete_iam_resources():
    """Delete IAM role and policy created by installer.py."""
    print(f"\n{'='*60}")
    print("Deleting IAM role and policy")
    print(f"{'='*60}")

    try:
        config = load_config()
        if not config:
            return False

        if not config.get("accountId"):
            print("Error: accountId not found in config.json")
            return False

        print("\n1. Deleting IAM role...")
        role_ok = delete_iam_role(config)

        print("\n2. Deleting IAM policy...")
        policy_ok = delete_iam_policy(config)

        if role_ok and policy_ok:
            print("\n✓ IAM resources deletion completed")
        else:
            print("\nWarning: IAM resources deletion completed with errors")
        return role_ok and policy_ok

    except Exception as e:
        print(f"Error deleting IAM resources: {e}")
        return False


# ============================================================================
# Main Function
# ============================================================================

def main():
    """Main function: Execute the entire uninstallation process."""
    parser = argparse.ArgumentParser(description="AgentCore Runtime Uninstaller")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and proceed with deletion",
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("AgentCore Runtime Uninstallation Script")
    print("=" * 60)

    config = load_config()
    if not config:
        print("\nError: Cannot proceed without config.json")
        sys.exit(1)

    print("Configuration file loaded successfully")
    print(f"  - Project Name: {config.get('projectName')}")
    print(f"  - Region: {config.get('region')}")
    print(f"  - Account ID: {config.get('accountId')}")
    if config.get("agent_runtime_arn"):
        print(f"  - Agent Runtime ARN: {config.get('agent_runtime_arn')}")
    if config.get("container_image_uri"):
        print(f"  - Container Image: {config.get('container_image_uri')}")

    if not args.yes:
        print("\n" + "=" * 60)
        print("WARNING: This will delete resources created by installer.py:")
        print("  - Bedrock AgentCore runtime")
        print("  - IAM role (AmazonBedrockAgentCoreRuntimeRoleFor*)")
        print("  - IAM policy (AmazonBedrockAgentCoreRuntimePolicyFor*)")
        print("=" * 60)
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Uninstallation cancelled.")
            sys.exit(0)

    steps = [
        ("Deleting AgentCore runtime", delete_agent_runtime),
        ("Deleting IAM role and policy", delete_iam_resources),
    ]

    all_ok = True
    for step_name, step_func in steps:
        if not step_func():
            print(f"\nWarning: Error occurred in step '{step_name}'.")
            print("   Continuing with remaining steps...")
            all_ok = False

    clear_installer_config()

    print("\n" + "=" * 60)
    if all_ok:
        print("Uninstallation process completed successfully!")
    else:
        print("Uninstallation process completed with warnings!")
    print("=" * 60)

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
