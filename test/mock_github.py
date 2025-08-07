#!/usr/bin/env python3
"""
Mock GitHub workflow - Simulates the GitHub Actions process
Usage: python3 mock_github.py [process|create-repo|cleanup]
"""

import os
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path

class MockGitHub:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_dir = Path(__file__).parent
        self.docs_dir = self.test_dir / "docs"
        self.processed_dir = self.test_dir / "processed"
        self.sample_docs = self.test_dir / "sample-docs"
        
    def setup_docs(self):
        """Set up docs directory for testing"""
        print("📁 Setting up docs directory...")
        
        # Clean and recreate
        if self.docs_dir.exists():
            shutil.rmtree(self.docs_dir)
        self.docs_dir.mkdir()
        
        # Copy sample docs
        for doc_file in self.sample_docs.glob("document-*.md"):
            shutil.copy2(doc_file, self.docs_dir)
        
        print(f"✅ Copied {len(list(self.docs_dir.glob('*.md')))} docs")
        return True
    
    def process_docs(self):
        """Mock GitHub Actions workflow"""
        print("🔄 Processing docs (mock GitHub workflow)...")
        
        if not self.docs_dir.exists() or not list(self.docs_dir.glob("*.md")):
            print("❌ No docs found! Run: python3 mock_github.py setup")
            return None
            
        # Extract project name from first doc
        first_doc = list(self.docs_dir.glob("*.md"))[0]
        with open(first_doc) as f:
            content = f.read()
            
        # Simple project name extraction
        lines = content.split('\n')
        project_name = "test-app"
        for line in lines[:10]:
            if line.startswith('# '):
                # Clean the project name - remove emojis and special chars
                raw_name = line[2:].strip().lower()
                # Keep only alphanumeric, spaces, and hyphens
                clean_name = ''.join(c for c in raw_name if c.isalnum() or c in ' -')
                project_name = clean_name.replace(' ', '-').strip('-')
                if project_name:
                    break
        
        # Fallback to test-app if cleaning resulted in empty name
        if not project_name:
            project_name = "test-app"
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        unique_name = f"{project_name}-{timestamp}"
        
        # Mock repo creation
        mock_repo_url = f"git@github.com:test-org/{unique_name}.git"
        
        # Create progress tracker
        summary = content[:300].replace('\n', ' ').strip()
        
        progress_tracker = f"""# Project: {project_name.replace('-', ' ').title()}

## Overview  
{summary}

## Template Analysis Requirements
**CRITICAL**: Before implementing ANY features, thoroughly analyze the provided template.
The template already includes authentication, database, and core infrastructure.
Focus on understanding and extending what's already there.

## Phase 1: Template Analysis & Adaptation
### Objectives
- Run the template and document all existing functionality
- Map template features to project requirements
- Identify which existing components can be reused
- Plan modifications to existing components
- Document gaps that need new development

### Success Criteria
- Complete template feature inventory documented
- Existing components mapped to project requirements  
- Database extension plan created
- UI component reuse strategy documented
- Gap analysis complete

## Phases 2-5: Development Process
- Phase 2: Core features with agent swarm (30 min)
- Phase 3: Enhanced features (30 min)
- Phase 4: Testing & polish (20 min)
- Phase 5: Final review & auto-push (15 min)
"""

        # Create webhook payload
        webhook_payload = {
            "project_name": unique_name,
            "template_hint": "modern-saas/nextjs-saas-clerk", 
            "requirements_summary": summary,
            "progress_tracker": progress_tracker,
            "github_repo": mock_repo_url,
            "starter_prompt": f"Let's build {project_name.replace('-', ' ').title()}. Start by analyzing the template and understanding the requirements in the /docs folder."
        }
        
        # Archive processed docs
        self.processed_dir.mkdir(exist_ok=True)
        archive_dir = self.processed_dir / unique_name
        archive_dir.mkdir(exist_ok=True)
        
        for doc_file in self.docs_dir.glob("*.md"):
            shutil.copy2(doc_file, archive_dir)
            
        # Save webhook payload
        with open(archive_dir / "webhook_payload.json", 'w') as f:
            json.dump(webhook_payload, f, indent=2)
            
        # Clean up docs (like real workflow)
        shutil.rmtree(self.docs_dir)
        
        print(f"✅ Processed docs into project: {unique_name}")
        print(f"📦 Archived to: {archive_dir}")
        print(f"🔗 Mock repo: {mock_repo_url}")
        
        return webhook_payload
    
    def cleanup(self):
        """Clean up test directories"""
        print("🧹 Cleaning up test directories...")
        
        dirs_to_clean = [self.docs_dir, self.processed_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✅ Cleaned: {dir_path}")
        
        return True

def main():
    mock = MockGitHub()
    
    if len(sys.argv) < 2:
        print("Usage: python3 mock_github.py [setup|process|cleanup]")
        print("\nsetup   - Set up docs directory with sample docs")
        print("process - Process docs and create webhook payload")
        print("cleanup - Clean up test directories")
        return 1
        
    action = sys.argv[1]
    
    if action == "setup":
        return 0 if mock.setup_docs() else 1
        
    elif action == "process":
        payload = mock.process_docs()
        if payload:
            print(f"\nWebhook payload ready:")
            print(f"Project: {payload['project_name']}")
            print(f"Template: {payload['template_hint']}")
            print(f"\nTo trigger webhook:")
            print(f"python3 test_pipeline.py webhook")
            return 0
        return 1
        
    elif action == "cleanup":
        return 0 if mock.cleanup() else 1
        
    else:
        print(f"Unknown action: {action}")
        return 1

if __name__ == "__main__":
    exit(main())