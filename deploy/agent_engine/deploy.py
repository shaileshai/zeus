"""Deploy Zeus agent to Vertex AI Agent Engine."""

import os
import subprocess
import sys


def deploy():
    """Deploy the agent using ADK CLI."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    region = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    if not project:
        print("Error: Set GOOGLE_CLOUD_PROJECT environment variable")
        sys.exit(1)

    print(f"Deploying Zeus agent to Vertex AI Agent Engine...")
    print(f"  Project: {project}")
    print(f"  Region: {region}")

    cmd = [
        "adk", "deploy", "agent_engine",
        "--project", project,
        "--region", region,
        "--agent_folder", "agent",
    ]

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode == 0:
        print("\n✅ Agent deployed successfully!")
    else:
        print(f"\n❌ Deployment failed (exit code {result.returncode})")
        sys.exit(result.returncode)


if __name__ == "__main__":
    deploy()
