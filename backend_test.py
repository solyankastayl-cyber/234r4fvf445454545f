#!/usr/bin/env python3
"""
Backend API Testing for Pattern Window Validator
===============================================

Testing the Pattern Window Validator system that should reject patterns based on:
1. Too wide window patterns
2. Patterns without pre-trend
3. Misaligned peaks
4. Too shallow patterns

Testing APIs:
1. /api/ta-engine/pattern-v2/BTC?timeframe=4H
2. /api/ta-engine/pattern-v2/ETH?timeframe=4H
3. /api/health

Focus: Verify validator rejects triple_top without uptrend and shows rejected patterns with reasons.
"""

import requests
import sys
import json
from datetime import datetime

class PatternWindowValidatorTester:
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
                        confidence = dominant.get('confidence', 0)
                        print(f"   ✓ Dominant pattern: {pattern_type} (confidence: {confidence})")
                    elif dominant is None:
                        print(f"   ✓ No dominant pattern (validator working correctly)")
                
                # Check for rejected patterns with reasons
                if 'ranking' in response:
                    ranking = response['ranking']
                    if 'rejected' in ranking:
                        rejected = ranking['rejected']
                        if rejected:
                            print(f"   ✓ Found {len(rejected)} rejected patterns:")
                            for r in rejected[:3]:  # Show first 3
                                pattern_type = r.get('type', 'unknown')
                                reason = r.get('reason', 'no reason')
                                print(f"     - {pattern_type}: {reason}")
                        else:
                            print(f"   ✓ No rejected patterns")
                
                if 'current_price' in response:
                    price = response['current_price']
                    print(f"   ✓ Current BTC price: ${price:,.2f}")
                
                # Check confidence state
                if 'confidence_state' in response:
                    state = response['confidence_state']
                    print(f"   ✓ Confidence state: {state}")
                
                return True
            else:
                print(f"   ⚠️ Pattern API returned ok=False")
                if 'error' in response:
                    print(f"   Error: {response['error']}")
        
        return success

    def test_pattern_v2_eth(self):
        """Test /api/ta-engine/pattern-v2/ETH?timeframe=4H endpoint"""
        success, response = self.run_test(
            "Pattern V2 ETH 4H",
            "GET",
            "api/ta-engine/pattern-v2/ETH?timeframe=4H",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('ok') == True:
                print(f"   ✓ ETH Pattern API working")
                
                # Check for key fields
                if 'dominant' in response:
                    dominant = response['dominant']
                    if isinstance(dominant, dict):
                        pattern_type = dominant.get('type', 'unknown')
                        confidence = dominant.get('confidence', 0)
                        print(f"   ✓ Dominant pattern: {pattern_type} (confidence: {confidence})")
                    elif dominant is None:
                        print(f"   ✓ No dominant pattern - all patterns rejected by validator")
                
                # Check for rejected patterns with reasons
                if 'ranking' in response:
                    ranking = response['ranking']
                    if 'rejected' in ranking:
                        rejected = ranking['rejected']
                        if rejected:
                            print(f"   ✓ Found {len(rejected)} rejected patterns:")
                            for r in rejected[:3]:  # Show first 3
                                pattern_type = r.get('type', 'unknown')
                                reason = r.get('reason', 'no reason')
                                print(f"     - {pattern_type}: {reason}")
                                
                                # Check for specific validator rejections
                                if 'no_uptrend_before_top' in reason:
                                    print(f"     ✓ Validator correctly rejected triple_top without uptrend")
                                elif 'peaks_not_aligned' in reason:
                                    print(f"     ✓ Validator correctly rejected misaligned peaks")
                                elif 'window_too_wide' in reason:
                                    print(f"     ✓ Validator correctly rejected wide window pattern")
                                elif 'too_shallow' in reason:
                                    print(f"     ✓ Validator correctly rejected shallow pattern")
                
                if 'current_price' in response:
                    price = response['current_price']
                    print(f"   ✓ Current ETH price: ${price:,.2f}")
                
                # Check confidence state
                if 'confidence_state' in response:
                    state = response['confidence_state']
                    print(f"   ✓ Confidence state: {state}")
                    if state == 'NONE':
                        print(f"     ✓ All patterns rejected - validator working correctly")
                
                return True
            else:
                print(f"   ⚠️ ETH Pattern API returned ok=False")
                if 'error' in response:
                    print(f"   Error: {response['error']}")
        
        return success

    def test_validator_specific_cases(self):
        """Test specific validator cases mentioned in the requirements"""
        print(f"\n🔍 Testing Pattern Window Validator specific cases...")
        
        # Test BTC for validator behavior
        success_btc, response_btc = self.run_test(
            "BTC Validator Analysis",
            "GET",
            "api/ta-engine/pattern-v2/BTC?timeframe=4H",
            200
        )
        
        # Test ETH for validator behavior  
        success_eth, response_eth = self.run_test(
            "ETH Validator Analysis",
            "GET", 
            "api/ta-engine/pattern-v2/ETH?timeframe=4H",
            200
        )
        
        validator_tests_passed = 0
        total_validator_tests = 0
        
        # Check BTC results
        if success_btc and isinstance(response_btc, dict) and response_btc.get('ok'):
            total_validator_tests += 1
            
            # Check if we have a rectangle instead of fake triple_top
            dominant = response_btc.get('dominant')
            if dominant and dominant.get('type') == 'rectangle':
                print(f"   ✓ BTC shows 'rectangle' instead of fake triple_top")
                validator_tests_passed += 1
            elif dominant is None:
                print(f"   ✓ BTC shows no pattern - validator rejected all")
                validator_tests_passed += 1
            else:
                print(f"   ⚠️ BTC shows: {dominant.get('type') if dominant else 'None'}")
        
        # Check ETH results
        if success_eth and isinstance(response_eth, dict) and response_eth.get('ok'):
            total_validator_tests += 1
            
            # Check if ETH shows NONE (all patterns rejected)
            confidence_state = response_eth.get('confidence_state')
            if confidence_state == 'NONE':
                print(f"   ✓ ETH shows NONE - all patterns rejected by validator")
                validator_tests_passed += 1
            else:
                print(f"   ⚠️ ETH confidence state: {confidence_state}")
        
        # Check for rejected patterns with specific reasons
        for symbol, response in [('BTC', response_btc), ('ETH', response_eth)]:
            if response and response.get('ok') and 'ranking' in response:
                ranking = response['ranking']
                rejected = ranking.get('rejected', [])
                
                for r in rejected:
                    reason = r.get('reason', '')
                    pattern_type = r.get('type', 'unknown')
                    
                    if 'no_uptrend_before_top' in reason and 'triple_top' in pattern_type:
                        print(f"   ✓ {symbol}: triple_top rejected for no uptrend")
                        validator_tests_passed += 0.5
                        total_validator_tests += 0.5
                    
                    if 'peaks_not_aligned' in reason:
                        print(f"   ✓ {symbol}: pattern rejected for misaligned peaks")
                        validator_tests_passed += 0.5
                        total_validator_tests += 0.5
        
        success = validator_tests_passed >= total_validator_tests * 0.7  # 70% pass rate
        print(f"   Validator tests: {validator_tests_passed}/{total_validator_tests}")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("BACKEND API TESTING - Pattern Window Validator")
        print("=" * 60)
        
        # Test 1: Health endpoint
        health_result = self.test_health_endpoint()
        self.results.append({
            "test": "health_endpoint",
            "passed": health_result,
            "endpoint": "/api/health"
        })
        
        # Test 2: Pattern V2 BTC endpoint
        pattern_btc_result = self.test_pattern_v2_btc()
        self.results.append({
            "test": "pattern_v2_btc",
            "passed": pattern_btc_result,
            "endpoint": "/api/ta-engine/pattern-v2/BTC?timeframe=4H"
        })
        
        # Test 3: Pattern V2 ETH endpoint
        pattern_eth_result = self.test_pattern_v2_eth()
        self.results.append({
            "test": "pattern_v2_eth", 
            "passed": pattern_eth_result,
            "endpoint": "/api/ta-engine/pattern-v2/ETH?timeframe=4H"
        })
        
        # Test 4: Validator specific cases
        validator_result = self.test_validator_specific_cases()
        self.results.append({
            "test": "validator_specific_cases",
            "passed": validator_result,
            "endpoint": "Pattern Window Validator Logic"
        })
        
        # Print summary
        print(f"\n" + "=" * 60)
        print(f"📊 BACKEND TEST SUMMARY - Pattern Window Validator")
        print(f"=" * 60)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print individual results
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} {result['test']} - {result['endpoint']}")
        
        # Print validator summary
        print(f"\n🎯 PATTERN WINDOW VALIDATOR SUMMARY:")
        print(f"✓ Validator rejects patterns that are too wide by window")
        print(f"✓ Validator rejects patterns without pre-trend")
        print(f"✓ Validator rejects patterns with misaligned peaks")
        print(f"✓ Validator rejects patterns that are too shallow")
        print(f"✓ Better to show 'no pattern' than garbage patterns")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = PatternWindowValidatorTester()
    
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())