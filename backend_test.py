#!/usr/bin/env python3
"""
Backend API Testing for Design Unification
==========================================

Testing the following APIs:
1. /api/ta-engine/pattern-v2/BTC?timeframe=4H
2. /api/health

Focus: Verify APIs are working correctly after design changes.
"""

import requests
import sys
import json
from datetime import datetime

class DesignUnificationTester:
    def __init__(self, base_url="https://tech-analyzer-15.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Try to parse JSON response
                try:
                    json_data = response.json()
                    if isinstance(json_data, dict):
                        if json_data.get('ok'):
                            print(f"   Response: OK = {json_data.get('ok')}")
                        if 'error' in json_data:
                            print(f"   Error: {json_data.get('error')}")
                    return True, json_data
                except:
                    return True, {"raw_response": response.text[:200]}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False, {"error": f"Status {response.status_code}", "response": response.text[:200]}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (10s)")
            return False, {"error": "timeout"}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {"error": str(e)}

    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('ok') == True:
                print(f"   ✓ Health check passed")
                return True
            else:
                print(f"   ⚠️ Health check returned ok=False")
        
        return success

    def test_pattern_v2_btc(self):
        """Test /api/ta-engine/pattern-v2/BTC?timeframe=4H endpoint"""
        success, response = self.run_test(
            "Pattern V2 BTC 4H",
            "GET",
            "api/ta-engine/pattern-v2/BTC?timeframe=4H",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('ok') == True:
                print(f"   ✓ Pattern API working")
                
                # Check for key fields
                if 'dominant' in response:
                    dominant = response['dominant']
                    if isinstance(dominant, dict):
                        pattern_type = dominant.get('type', 'unknown')
                        confidence = dominant.get('score', 0)
                        print(f"   ✓ Dominant pattern: {pattern_type} (confidence: {confidence})")
                
                if 'current_price' in response:
                    price = response['current_price']
                    print(f"   ✓ Current BTC price: ${price:,.2f}")
                
                return True
            else:
                print(f"   ⚠️ Pattern API returned ok=False")
                if 'error' in response:
                    print(f"   Error: {response['error']}")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("BACKEND API TESTING - Design Unification")
        print("=" * 60)
        
        # Test 1: Health endpoint
        health_result = self.test_health_endpoint()
        self.results.append({
            "test": "health_endpoint",
            "passed": health_result,
            "endpoint": "/api/health"
        })
        
        # Test 2: Pattern V2 BTC endpoint
        pattern_result = self.test_pattern_v2_btc()
        self.results.append({
            "test": "pattern_v2_btc",
            "passed": pattern_result,
            "endpoint": "/api/ta-engine/pattern-v2/BTC?timeframe=4H"
        })
        
        # Print summary
        print(f"\n" + "=" * 60)
        print(f"📊 BACKEND TEST SUMMARY")
        print(f"=" * 60)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print individual results
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} {result['test']} - {result['endpoint']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = DesignUnificationTester()
    
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())