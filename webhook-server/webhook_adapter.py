#!/usr/bin/env python3
"""
Adapter to handle webhooks from ideabrow-automation
Fetches additional data and transforms for our tmux automation
"""

import requests
import re
from typing import Dict, Optional

def fetch_github_content(url: str) -> Optional[str]:
    """
    Fetch content from GitHub raw URL
    Convert blob URL to raw URL
    """
    # Convert blob URL to raw URL
    raw_url = url.replace('github.com', 'raw.githubusercontent.com')
    raw_url = raw_url.replace('/blob/', '/')
    
    try:
        response = requests.get(raw_url, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {raw_url}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching {raw_url}: {e}")
        return None

def extract_repo_path(repo_url: str) -> str:
    """
    Extract org/repo from GitHub URL
    """
    # Pattern: https://github.com/org/repo
    match = re.search(r'github\.com/([^/]+/[^/]+)', repo_url)
    if match:
        return match.group(1)
    return ""

def convert_to_ssh_url(https_url: str) -> str:
    """
    Convert HTTPS GitHub URL to SSH format
    https://github.com/user/repo.git -> git@github.com:user/repo.git
    """
    if https_url.startswith('https://github.com/'):
        # Extract the path after github.com/
        path = https_url.replace('https://github.com/', '')
        # Ensure it ends with .git
        if not path.endswith('.git'):
            path += '.git'
        return f'git@github.com:{path}'
    return https_url

def generate_starter_prompt(progress_tracker: str, requirements_summary: str) -> str:
    """
    Generate a starter prompt for Claude Code based on the tracker
    """
    # Extract project name from tracker
    project_name = "Project"
    for line in progress_tracker.split('\n'):
        if line.startswith('# Project:'):
            project_name = line.replace('# Project:', '').strip()
            break
    
    # Extract first phase objectives
    first_objectives = []
    in_phase_1 = False
    for line in progress_tracker.split('\n'):
        if '## Phase 1:' in line:
            in_phase_1 = True
        elif in_phase_1 and line.startswith('- [ ]'):
            first_objectives.append(line.replace('- [ ]', '').strip())
        elif in_phase_1 and line.startswith('##'):
            break
    
    # Build starter prompt
    prompt = f"Let's adapt the template to create {project_name}. "
    
    prompt += "\n\n🚨 CRITICAL - USE AGENT SWARMS FOR PARALLEL WORK:\n"
    prompt += "You have access to /home/wv3/.claude/agents directory with specialized agents!\n\n"
    
    prompt += "IMMEDIATE ACTIONS:\n"
    prompt += "1. Spawn multiple agents to work in PARALLEL (not sequentially)\n"
    prompt += "2. EVERY agent must read the /docs folder to understand requirements\n"
    prompt += "3. Use task-orchestrator to coordinate agent work\n"
    prompt += "4. Agents must work on UNIQUE, non-overlapping tasks\n\n"
    
    prompt += "SUGGESTED INITIAL SWARM:\n"
    prompt += "- researcher: Analyze all /docs files for requirements\n"
    prompt += "- code-analyzer: Study template structure\n"
    prompt += "- architect: Plan integration approach\n"
    prompt += "- developer: Start initial setup\n\n"
    
    prompt += "TEMPLATE NOTES: The template has auth, database, and UI components. "
    prompt += "Extend it, don't rebuild. Use Prisma/SQLite for ALL database needs. "
    
    if first_objectives and "template" not in first_objectives[0].lower():
        prompt += f"Phase 1 objectives need updating - they should focus on analyzing the template first, not {first_objectives[0].lower()}. "
    
    prompt += "Review PROGRESS_TRACKER.md but remember: extend the template, don't rebuild from scratch."
    
    return prompt

def transform_webhook_payload(ideabrow_payload: Dict) -> Dict:
    """
    Transform ideabrow-automation webhook to our format
    Fetches additional data from GitHub
    """
    # Extract GitHub repo path
    repo_url = ideabrow_payload.get('repo_url', '')
    github_repo = extract_repo_path(repo_url)
    
    # Fetch PROGRESS_TRACKER.md content
    tracker_url = ideabrow_payload.get('tracker_url', '')
    progress_tracker_content = ""
    
    if tracker_url:
        print(f"Fetching PROGRESS_TRACKER.md from {tracker_url}")
        progress_tracker_content = fetch_github_content(tracker_url) or ""
    
    # Generate starter prompt
    starter_prompt = generate_starter_prompt(
        progress_tracker_content,
        ideabrow_payload.get('requirements_summary', '')
    )
    
    # Build our payload format
    # Append tech stack info to requirements_summary to help template selection
    requirements = ideabrow_payload.get('requirements_summary', '')
    if requirements and "Tech stack:" not in requirements:
        requirements += " Tech stack: Next.js 14+ with App Router, Clerk authentication, Prisma ORM with SQLite database (local development, no external DB needed), Tailwind CSS."
    
    # Convert HTTPS URL to SSH for cloning
    ssh_repo_url = convert_to_ssh_url(repo_url)
    
    transformed = {
        "project_name": ideabrow_payload.get('project_name', 'unnamed-project'),
        "requirements_summary": requirements,
        "template_hint": ideabrow_payload.get('template_hint'),
        "github_repo": github_repo,
        "progress_tracker_content": progress_tracker_content,
        "starter_prompt": starter_prompt,
        "original_repo_url": ssh_repo_url,  # Use SSH URL for cloning
        "original_timestamp": ideabrow_payload.get('timestamp', '')
    }
    
    return transformed

def fetch_requirements_from_repo(repo_url: str) -> str:
    """
    Fetch requirements from the docs folder in the repository
    """
    github_repo = extract_repo_path(repo_url)
    if not github_repo:
        return ""
    
    # Try to fetch README from docs folder
    docs_readme_url = f"https://raw.githubusercontent.com/{github_repo}/main/docs/README.md"
    readme_content = fetch_github_content(docs_readme_url)
    
    if readme_content:
        return readme_content
    
    # Try first document file
    # Note: This would need GitHub API to list files, simplified for now
    return ""