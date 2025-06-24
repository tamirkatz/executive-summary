#!/usr/bin/env python3
"""
Test script for the Enhanced Workflow frontend integration.
This script demonstrates how to make API calls to test both standard and enhanced workflows.
"""

import asyncio
import json
import requests
import time
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"  # Adjust based on your setup
RESEARCH_ENDPOINT = f"{API_BASE_URL}/research"

def test_standard_workflow():
    """Test the standard workflow (existing functionality)."""
    print("🔬 Testing Standard Workflow")
    
    payload = {
        "company": "Tesla",
        "company_url": "https://tesla.com",
        "user_role": "CEO",
        "use_enhanced_workflow": False  # Standard workflow
    }
    
    print(f"📤 Sending request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(RESEARCH_ENDPOINT, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Standard workflow initiated successfully")
        print(f"📋 Response: {json.dumps(result, indent=2)}")
        
        return result.get("job_id")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Standard workflow test failed: {e}")
        return None

def test_enhanced_workflow():
    """Test the enhanced workflow (new three-agent system)."""
    print("\n🚀 Testing Enhanced Workflow")
    
    payload = {
        "company": "Stripe",
        "company_url": "https://stripe.com",
        "user_role": "CTO",
        "use_enhanced_workflow": True  # Enhanced workflow with three agents
    }
    
    print(f"📤 Sending request: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(RESEARCH_ENDPOINT, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Enhanced workflow initiated successfully")
        print(f"📋 Response: {json.dumps(result, indent=2)}")
        
        return result.get("job_id")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Enhanced workflow test failed: {e}")
        return None

def check_job_status(job_id: str) -> Dict[str, Any]:
    """Check the status of a job."""
    if not job_id:
        return {}
    
    try:
        response = requests.get(f"{API_BASE_URL}/research/{job_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to check job status: {e}")
        return {}

def monitor_job(job_id: str, max_wait_time: int = 60):
    """Monitor a job for a limited time."""
    if not job_id:
        print("❌ No job ID provided")
        return
    
    print(f"👀 Monitoring job {job_id} (max {max_wait_time}s)")
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        status = check_job_status(job_id)
        
        if status:
            current_status = status.get("status", "unknown")
            print(f"📊 Job {job_id}: {current_status}")
            
            if current_status in ["completed", "failed", "error"]:
                print(f"🏁 Job finished with status: {current_status}")
                if status.get("report"):
                    print(f"📄 Report generated (length: {len(status['report'])} chars)")
                break
        
        time.sleep(5)  # Check every 5 seconds
    else:
        print(f"⏰ Monitoring stopped after {max_wait_time}s")

def compare_workflows():
    """Compare the two workflow types side by side."""
    print("🔄 Workflow Comparison Test")
    print("=" * 50)
    
    # Test standard workflow
    standard_job_id = test_standard_workflow()
    
    # Wait a moment
    time.sleep(2)
    
    # Test enhanced workflow
    enhanced_job_id = test_enhanced_workflow()
    
    print(f"\n📋 Job Summary:")
    print(f"Standard Workflow Job ID: {standard_job_id}")
    print(f"Enhanced Workflow Job ID: {enhanced_job_id}")
    
    # Monitor both jobs briefly
    if standard_job_id:
        print(f"\n👀 Checking standard workflow status...")
        monitor_job(standard_job_id, max_wait_time=30)
    
    if enhanced_job_id:
        print(f"\n👀 Checking enhanced workflow status...")
        monitor_job(enhanced_job_id, max_wait_time=30)

def test_api_connectivity():
    """Test basic API connectivity."""
    print("🌐 Testing API Connectivity")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        print("✅ API server is reachable")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API server is not reachable: {e}")
        print(f"💡 Make sure your backend server is running on {API_BASE_URL}")
        return False

def interactive_test():
    """Interactive test mode."""
    print("🎮 Interactive Enhanced Workflow Test")
    print("=" * 40)
    
    # Get user input
    company = input("Enter company name (default: OpenAI): ").strip() or "OpenAI"
    url = input("Enter company URL (default: https://openai.com): ").strip() or "https://openai.com"
    role = input("Enter your role (default: CEO): ").strip() or "CEO"
    
    # Ask about workflow type
    enhanced_choice = input("Use enhanced workflow? (y/N): ").strip().lower()
    use_enhanced = enhanced_choice in ['y', 'yes', '1', 'true']
    
    print(f"\n🚀 Testing {'Enhanced' if use_enhanced else 'Standard'} Workflow")
    
    payload = {
        "company": company,
        "company_url": url,
        "user_role": role,
        "use_enhanced_workflow": use_enhanced
    }
    
    print(f"📤 Request payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(RESEARCH_ENDPOINT, json=payload)
        response.raise_for_status()
        
        result = response.json()
        job_id = result.get("job_id")
        
        print(f"✅ Research initiated successfully!")
        print(f"🆔 Job ID: {job_id}")
        print(f"🌐 WebSocket URL: {result.get('websocket_url', 'Not provided')}")
        
        # Ask if user wants to monitor
        monitor_choice = input("\nMonitor job progress? (Y/n): ").strip().lower()
        if monitor_choice not in ['n', 'no', '0', 'false']:
            monitor_job(job_id, max_wait_time=120)
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Test failed: {e}")

def main():
    """Main test function."""
    print("🧪 Enhanced Workflow Frontend Integration Test")
    print("=" * 50)
    
    # Test API connectivity first
    if not test_api_connectivity():
        return
    
    print("\nChoose test mode:")
    print("1. Compare Standard vs Enhanced workflows")
    print("2. Test Enhanced workflow only")
    print("3. Test Standard workflow only")
    print("4. Interactive test")
    print("5. Exit")
    
    try:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            compare_workflows()
        elif choice == "2":
            job_id = test_enhanced_workflow()
            if job_id:
                monitor_job(job_id, max_wait_time=60)
        elif choice == "3":
            job_id = test_standard_workflow()
            if job_id:
                monitor_job(job_id, max_wait_time=60)
        elif choice == "4":
            interactive_test()
        elif choice == "5":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 