# Pull Request Instructions

## Summary

This contribution improves the `to_date` function in `run_page/utils.py` by replacing custom timestamp parsing logic with `datetime.fromisoformat()`, as recommended in the TODO comment.

## Changes Made

- **File**: `run_page/utils.py`
- **Function**: `to_date()`
- **Improvement**: Uses `datetime.fromisoformat()` for standard ISO format strings
- **Backward Compatibility**: Maintains fallback to `strptime` for non-standard formats

## Steps to Create PR

### 1. Create Fork (One-time setup)

Since the GitHub PAT doesn't have permissions to create forks via API, you need to create the fork manually:

1. Visit: https://github.com/yihong0618/running_page/fork
2. Click the "Fork" button
3. Wait for the fork to be created at: https://github.com/jimcody1995/running_page

### 2. Push Changes and Create PR

Once the fork exists, run:

```bash
cd /root/running_page
python3 create_pr.py
```

The script will:
- Verify the fork exists
- Push the `improve-to-date-function` branch to your fork
- Create a pull request to the upstream repository

## Manual Alternative

If you prefer to do it manually:

```bash
# Push to fork (use environment variable for PAT)
export GITHUB_PAT="your_token_here"
cd /root/running_page
git push https://jimcody1995:${GITHUB_PAT}@github.com/jimcody1995/running_page.git improve-to-date-function

# Then create PR via GitHub web interface or API
```

## PR Details

- **Title**: refactor: use datetime.fromisoformat in to_date function
- **Branch**: improve-to-date-function
- **Base**: master
- **Description**: See the script for full PR description

