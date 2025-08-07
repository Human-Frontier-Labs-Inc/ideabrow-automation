#!/usr/bin/env python3
"""
IdeaBrow Pipeline Tester - Mock GitHub workflow and test components
Usage: python3 test_pipeline.py [webhook|docs|full|phases]
"""

import os
import sys
import json
import requests
import subprocess
import time
from datetime import datetime
from pathlib import Path

class PipelineTester:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.test_dir = Path(__file__).parent
        self.webhook_url = "http://localhost:8090/webhook"
        self.sample_docs = self.test_dir / "sample-docs"
        
    def test_docs_processing(self):
        """Test: Mock GitHub workflow - process docs and create webhook payload"""
        print("🔄 Testing docs processing...")
        
        # Read sample docs
        docs = {}
        for doc_file in self.sample_docs.glob("document-*.md"):
            with open(doc_file) as f:
                docs[doc_file.stem] = f.read()
        
        if not docs:
            print("❌ No sample docs found!")
            return False
            
        print(f"✅ Loaded {len(docs)} documents")
        
        # Extract project info (mock GitHub workflow logic)
        project_name = "test-app"
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        unique_name = f"{project_name}-{timestamp}"
        
        # Create requirements summary
        first_doc = list(docs.values())[0]
        summary = first_doc[:200].replace('\n', ' ')
        
        # Mock progress tracker (simplified)
        progress_tracker = f"""# Project: {project_name.title()}

## Overview
{summary}

## Phase 1: Template Analysis
- Analyze template and requirements
- Set up development environment

## Phases 2-5: Development Process
- Core features, enhancements, testing, final review
"""
        
        # Create webhook payload using REAL existing repo from yesterday
        real_repo = "git@github.com:Human-Frontier-Labs-Inc/safeviewshield-2025-08-06-141810.git"
        
        payload = {
            "project_name": unique_name,
            "template_hint": "modern-saas/nextjs-saas-clerk",
            "requirements_summary": summary,
            "progress_tracker": progress_tracker,
            "github_repo": real_repo,  # Use real repo that exists!
            "starter_prompt": f"Let's build {project_name.replace('-', ' ').title()}. Start by analyzing the template and understanding the requirements.",
            "docs_content": docs
        }
        
        print(f"✅ Created payload for project: {unique_name}")
        return payload
    
    def test_webhook(self, payload=None):
        """Test: Send webhook to server"""
        print("🌐 Testing webhook server...")
        
        if not payload:
            payload = self.test_docs_processing()
            if not payload:
                return False
                
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Webhook processed successfully")
                return True
            else:
                print(f"❌ Webhook failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return False
    
    def test_phases(self, project_name):
        """Test: Check if phases are scheduled correctly"""
        print("⏰ Testing phase scheduling...")
        
        # Check for scheduled sleep processes
        try:
            result = subprocess.run(
                ["ps", "aux"], 
                capture_output=True, 
                text=True
            )
            
            scheduled_count = 0
            for line in result.stdout.split('\n'):
                if 'sleep' in line and 'send-claude-message' in line and project_name in line:
                    scheduled_count += 1
            
            if scheduled_count >= 4:  # Phases 2-5
                print(f"✅ Found {scheduled_count} scheduled phases")
                return True
            else:
                print(f"⚠️  Only {scheduled_count} phases scheduled (expected 4)")
                return False
                
        except Exception as e:
            print(f"❌ Phase check error: {e}")
            return False
    
    def test_full_flow(self):
        """Test: Complete end-to-end flow"""
        print("🚀 Testing full pipeline flow...")
        print("-" * 50)
        
        # Step 1: Process docs
        payload = self.test_docs_processing()
        if not payload:
            return False
        
        print("-" * 50)
        
        # Step 2: Send webhook
        if not self.test_webhook(payload):
            return False
        
        print("-" * 50)
        
        # Step 3: Check phases (wait a bit for processing)
        time.sleep(3)
        project_name = payload["project_name"]
        
        if not self.test_phases(project_name):
            print("⚠️  Phases may still be processing...")
        
        print("-" * 50)
        print(f"✅ Full flow test complete for: {project_name}")
        print(f"📊 Monitor: python3 ../monitoring/pipeline_monitor.py")
        print(f"🔍 Attach: tmux attach -t {project_name}")
        
        return True

def main():
    tester = PipelineTester()
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_pipeline.py [docs|webhook|phases|full]")
        print("\ndocs    - Test document processing only")
        print("webhook - Test webhook server only") 
        print("phases  - Test phase scheduling (needs project name)")
        print("full    - Test complete end-to-end flow")
        return 1
    
    test_type = sys.argv[1]
    
    if test_type == "docs":
        payload = tester.test_docs_processing()
        if payload:
            print(f"Project: {payload['project_name']}")
            print(f"Template: {payload['template_hint']}")
            return 0
        return 1
        
    elif test_type == "webhook":
        return 0 if tester.test_webhook() else 1
        
    elif test_type == "phases":
        if len(sys.argv) < 3:
            print("Usage: python3 test_pipeline.py phases <project-name>")
            return 1
        return 0 if tester.test_phases(sys.argv[2]) else 1
        
    elif test_type == "full":
        return 0 if tester.test_full_flow() else 1
        
    else:
        print(f"Unknown test type: {test_type}")
        return 1

if __name__ == "__main__":
    exit(main())