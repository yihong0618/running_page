#!/usr/bin/env python3
"""
Script to push changes and create a PR for running_page contribution.
Make sure you have created the fork first at: https://github.com/yihong0618/running_page/fork
"""

import subprocess
import requests
import sys
import time
import os

GITHUB_PAT = os.environ.get("GITHUB_PAT", "")
BRANCH = "improve-to-date-function"
FORK_USER = "jimcody1995"
REPO_OWNER = "yihong0618"
REPO = "running_page"


def check_fork_exists():
    """Check if the fork exists"""
    url = f"https://api.github.com/repos/{FORK_USER}/{REPO}"
    headers = {"Authorization": f"token {GITHUB_PAT}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200


def push_to_fork():
    """Push the branch to the fork"""
    remote_url = f"https://{FORK_USER}:{GITHUB_PAT}@github.com/{FORK_USER}/{REPO}.git"
    print(f"Pushing branch '{BRANCH}' to fork...")
    result = subprocess.run(
        ["git", "push", remote_url, BRANCH],
        cwd="/root/running_page",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error pushing: {result.stderr}")
        return False
    print("✓ Successfully pushed to fork")
    return True


def create_pull_request():
    """Create a pull request"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO}/pulls"
    headers = {
        "Authorization": f"token {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    data = {
        "title": "refactor: use datetime.fromisoformat in to_date function",
        "body": """## Description

This PR refactors the `to_date` function in `run_page/utils.py` to use `datetime.fromisoformat()` instead of custom timestamp parsing logic, as recommended in the TODO comment.

## Changes

- Replaced custom `strptime`-based parsing with `datetime.fromisoformat()` for standard ISO format strings
- Maintained backward compatibility by falling back to `strptime` for non-standard formats
- Improved code clarity and documentation
- Removed TODO comment as the improvement is now implemented

## Benefits

- Uses standard library function (available since Python 3.7, project requires >=3.12)
- Simplifies code by leveraging built-in ISO format parsing
- Maintains backward compatibility for edge cases
- Better performance for standard ISO format strings

## Testing

- Verified code compiles without errors
- Function maintains same behavior for existing callers in `codoon_sync.py`
- Backward compatible with existing timestamp formats

This addresses the TODO comment on line 33 of `utils.py`.""",
        "head": f"{FORK_USER}:{BRANCH}",
        "base": "master",
    }

    print("Creating pull request...")
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        pr_data = response.json()
        print("✓ Pull request created successfully!")
        print(f"  URL: {pr_data['html_url']}")
        return True
    else:
        print(f"Error creating PR: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    print("Checking if fork exists...")
    if not check_fork_exists():
        print("❌ Fork does not exist!")
        print(
            f"Please create the fork first by visiting: https://github.com/{REPO_OWNER}/{REPO}/fork"
        )
        print("Or click the 'Fork' button on: https://github.com/{REPO_OWNER}/{REPO}")
        print("\nAfter creating the fork, run this script again.")
        sys.exit(1)

    print("✓ Fork exists")

    if not push_to_fork():
        sys.exit(1)

    # Wait a moment for GitHub to process the push
    print("Waiting for GitHub to process the push...")
    time.sleep(2)

    if not create_pull_request():
        sys.exit(1)

    print("\n✅ All done! Your PR has been created.")


if __name__ == "__main__":
    main()
