import os
from dotenv import load_dotenv
from github import Github

# 1. Load the settings from .env file
load_dotenv()

# 2. Get environment variables
token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("GITHUB_REPO")

if not token:
    print("[ERROR] GITHUB_TOKEN is not set in the .env file.")
    exit(1)

if not repo_name:
    print("[ERROR] GITHUB_REPO is not set in the .env file.")
    exit(1)

print(f"Connecting to GitHub to fetch info for '{repo_name}'...")

try:
    # 3. Initialize the GitHub API client
    g = Github(token)
    
    # 4. Fetch the repository object
    repo = g.get_repo(repo_name)
    
    # 5. Print out the basic information
    print("\n[SUCCESS] Authentication Successful!")
    print(f"Repository Name: {repo.full_name}")
    print(f"Description:     {repo.description}")
    print(f"Stars Count:     {repo.stargazers_count:,}")
    print(f"Forks Count:     {repo.forks_count:,}")
    
    # Note: open_issues_count includes both open Issues and open Pull Requests in GitHub's API
    print(f"Open Issues/PRs: {repo.open_issues_count}")
    
except Exception as e:
    print("\n[ERROR] Error connecting to GitHub:")
    print(str(e))
