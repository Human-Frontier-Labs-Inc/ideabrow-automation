#!/usr/bin/env python3
"""
Test script for the enhanced webhook server
"""

import requests
import json
import time

def test_webhook_server(port=8090):
    """Test the webhook server functionality"""
    base_url = f"http://localhost:{port}"
    
    print("Testing Enhanced Webhook Server")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Response: {json.dumps(health_data, indent=2)}")
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Admin state endpoint
    print("\n2. Testing admin state endpoint...")
    try:
        response = requests.get(f"{base_url}/admin/state")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            state_data = response.json()
            print(f"   Response: {json.dumps(state_data, indent=2)}")
            print("   ✅ Admin state check passed")
        else:
            print("   ❌ Admin state check failed")
    except Exception as e:
        print(f"   ❌ Admin state error: {e}")
    
    # Test 3: Test endpoint with sample data
    print("\n3. Testing webhook with sample data...")
    test_payload = {
        "project_name": f"test-project-{int(time.time())}",
        "requirements_summary": "Build a simple test application with basic CRUD operations",
        "template_hint": "nextjs-basic",
        "github_repo": "test/test-repo",
        "progress_tracker_content": "# Project: Test\n\n## Phase 1: Setup\n- Initialize project",
        "starter_prompt": "Let's start building this test application"
    }
    
    try:
        response = requests.post(f"{base_url}/test", json=test_payload)
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 202]:
            response_data = response.json()
            print(f"   Response: {json.dumps(response_data, indent=2)}")
            print("   ✅ Test webhook passed")
            
            # Test duplicate request
            print("\n4. Testing duplicate request detection...")
            time.sleep(1)
            duplicate_response = requests.post(f"{base_url}/test", json=test_payload)
            print(f"   Status: {duplicate_response.status_code}")
            if duplicate_response.status_code == 409:
                print("   ✅ Duplicate detection working")
            else:
                print("   ⚠️  Duplicate detection may not be working as expected")
                
        else:
            print("   ❌ Test webhook failed")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Test webhook error: {e}")
    
    print("\n" + "=" * 40)
    print("Test completed!")
    return True

if __name__ == "__main__":
    test_webhook_server()