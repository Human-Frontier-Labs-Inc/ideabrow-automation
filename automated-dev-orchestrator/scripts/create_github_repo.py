#!/usr/bin/env python3
"""
Create GitHub repository using GitHub API
This script creates a repository in the specified organization.
"""

import os
import sys
import json
import requests
from typing import Optional, Dict, Any

def create_repository(
    repo_name: str,
    org_name: str = "Human-Frontier-Labs-Inc",
    description: str = "Auto-generated from ideabrow-automation",
    private: bool = True,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a GitHub repository in the specified organization.
    
    Args:
        repo_name: Name of the repository to create
        org_name: GitHub organization name
        description: Repository description
        private: Whether the repository should be private
        token: GitHub Personal Access Token (uses GH_PAT env var if not provided)
    
    Returns:
        Dict containing the API response or error information
    """
    
    # Get token from environment if not provided
    if not token:
        token = os.environ.get('GH_PAT') or os.environ.get('GH_TOKEN')
    
    if not token:
        return {
            "error": "No GitHub token found",
            "message": "Please set GH_PAT or GH_TOKEN environment variable"
        }
    
    # GitHub API endpoint for creating org repos
    url = f"https://api.github.com/orgs/{org_name}/repos"
    
    # Request headers
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    # Request payload
    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False,  # Don't initialize with README
        "has_issues": True,
        "has_projects": True,
        "has_wiki": False
    }
    
    try:
        # Make the API request
        response = requests.post(url, headers=headers, json=data)
        
        # Check if successful
        if response.status_code == 201:
            repo_data = response.json()
            return {
                "success": True,
                "repo_name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "html_url": repo_data["html_url"],
                "ssh_url": repo_data["ssh_url"],
                "clone_url": repo_data["clone_url"],
                "created_at": repo_data["created_at"]
            }
        else:
            # Handle errors
            error_data = response.json() if response.text else {}
            return {
                "error": f"API request failed with status {response.status_code}",
                "message": error_data.get("message", "Unknown error"),
                "status_code": response.status_code,
                "response": error_data
            }
            
    except requests.exceptions.RequestException as e:
        return {
            "error": "Request failed",
            "message": str(e)
        }
    except Exception as e:
        return {
            "error": "Unexpected error",
            "message": str(e)
        }

def main():
    """Command-line interface for creating GitHub repos."""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 create_github_repo.py <repo-name> [org-name] [description]")
        print("\nExample:")
        print("  python3 create_github_repo.py my-project-2024")
        print("  python3 create_github_repo.py my-project Human-Frontier-Labs-Inc 'My awesome project'")
        sys.exit(1)
    
    # Parse arguments
    repo_name = sys.argv[1]
    org_name = sys.argv[2] if len(sys.argv) > 2 else "Human-Frontier-Labs-Inc"
    description = sys.argv[3] if len(sys.argv) > 3 else "Auto-generated from ideabrow-automation"
    
    # Create the repository
    print(f"Creating repository: {org_name}/{repo_name}")
    result = create_repository(repo_name, org_name, description)
    
    # Handle result
    if result.get("success"):
        print(f"✅ Repository created successfully!")
        print(f"   URL: {result['html_url']}")
        print(f"   SSH: {result['ssh_url']}")
        print(f"   Clone: {result['clone_url']}")
        # Output JSON for workflow to parse
        print(f"JSON_OUTPUT:{json.dumps(result)}")
        sys.exit(0)
    else:
        print(f"❌ Failed to create repository")
        print(f"   Error: {result.get('message', 'Unknown error')}")
        if result.get('status_code') == 401:
            print("   Note: Authentication failed. Check your GH_PAT token.")
        elif result.get('status_code') == 403:
            print("   Note: Permission denied. Ensure your token has 'repo' and 'write:org' scopes.")
        elif result.get('status_code') == 422:
            print("   Note: Repository may already exist or name is invalid.")
        # Output error JSON
        print(f"JSON_ERROR:{json.dumps(result)}")
        sys.exit(1)

if __name__ == "__main__":
    main()