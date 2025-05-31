
import requests
import sys
import json
from datetime import datetime

class EmailHelperAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response.text:
                    try:
                        return success, response.json()
                    except json.JSONDecodeError:
                        return success, response.text
                return success, None
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_api_root(self):
        """Test the API root endpoint"""
        return self.run_test(
            "API Root Endpoint",
            "GET",
            "api",
            200
        )

    def test_generate_replies(self, email_content, sender_name=None, sender_email=None):
        """Test the generate-replies endpoint"""
        data = {
            "email_content": email_content,
            "sender_name": sender_name,
            "sender_email": sender_email
        }
        
        success, response = self.run_test(
            "Generate Email Replies",
            "POST",
            "api/generate-replies",
            200,
            data=data
        )
        
        if success:
            # Validate response structure
            if "replies" in response and "original_email" in response:
                print("✅ Response contains expected fields")
                
                # Check if we have 4 replies with different tones
                replies = response["replies"]
                if len(replies) == 4:
                    print(f"✅ Received 4 replies as expected")
                    
                    # Check if all tones are present
                    tones = [reply["tone"] for reply in replies]
                    expected_tones = ["professional", "friendly", "brief", "detailed"]
                    if all(tone in tones for tone in expected_tones):
                        print("✅ All expected tones are present")
                    else:
                        print(f"❌ Missing some tones. Found: {tones}")
                        success = False
                else:
                    print(f"❌ Expected 4 replies, got {len(replies)}")
                    success = False
            else:
                print("❌ Response missing expected fields")
                success = False
                
        return success, response

    def test_empty_email(self):
        """Test sending an empty email content"""
        data = {
            "email_content": ""
        }
        
        success, response = self.run_test(
            "Empty Email Content",
            "POST",
            "api/generate-replies",
            400,
            data=data
        )
        
        return success, response

def main():
    # Get the backend URL from the frontend .env file
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                backend_url = line.strip().split('=')[1].strip('"')
                break
    
    print(f"Using backend URL: {backend_url}")
    
    # Setup
    tester = EmailHelperAPITester(backend_url)
    
    # Sample email for testing
    sample_email = "Hi team, I wanted to schedule a meeting to discuss the quarterly budget review. Could we meet sometime next week? Please let me know your availability. Thanks!"
    
    # Run tests
    api_root_success, _ = tester.test_api_root()
    
    if not api_root_success:
        print("❌ API root test failed, stopping tests")
        return 1
    
    # Test with empty email (should fail with 400)
    empty_email_success, _ = tester.test_empty_email()
    
    # Test with valid email
    generate_replies_success, replies_response = tester.test_generate_replies(
        sample_email,
        sender_name="John Doe",
        sender_email="john@example.com"
    )
    
    if generate_replies_success:
        # Print a sample of the first reply
        first_reply = replies_response["replies"][0]
        print(f"\nSample reply ({first_reply['tone']}):")
        print(f"Preview: {first_reply['preview']}")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())
      