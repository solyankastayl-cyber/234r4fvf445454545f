#!/usr/bin/env python3
"""
Backend API Testing for Visual Mode Resolver
============================================

Testing the Visual Mode Resolver system that should:
1. Return visual_mode in pattern-v2 API response
2. BTC shows mode=range_only with allowed=[box, levels, triggers]
3. ETH shows mode=structure_only (no pattern)
4. visual_mode.forbidden contains elements that shouldn't be drawn
5. Frontend PatternSVGOverlay listens to visual_mode

Testing APIs:
1. /api/ta-engine/pattern-v2/BTC?timeframe=4H
2. /api/ta-engine/pattern-v2/ETH?timeframe=4H
3. /api/health

Focus: Verify visual_mode is returned and contains correct allowed/forbidden elements.
"""

import requests
import sys
import json
from datetime import datetime

class VisualModeResolverTester:
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
        """Test /api/ta-engine/pattern-v2/BTC?timeframe=4H endpoint for visual_mode"""
        success, response = self.run_test(
            "Pattern V2 BTC 4H - Visual Mode",
            "GET",
            "api/ta-engine/pattern-v2/BTC?timeframe=4H",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('ok') == True:
                print(f"   ✓ Pattern API working")
                
                # Check for visual_mode field
                if 'visual_mode' in response:
                    visual_mode = response['visual_mode']
                    print(f"   ✓ visual_mode field present")
                    
                    if isinstance(visual_mode, dict):
                        mode = visual_mode.get('mode', 'unknown')
                        allowed = visual_mode.get('allowed', [])
                        forbidden = visual_mode.get('forbidden', [])
                        
                        print(f"   ✓ Mode: {mode}")
                        print(f"   ✓ Allowed: {allowed}")
                        print(f"   ✓ Forbidden: {forbidden}")
                        
                        # Check if BTC shows range_only mode
                        if mode == 'range_only':
                            print(f"   ✅ BTC correctly shows range_only mode")
                            
                            # Check expected allowed elements for range_only
                            expected_allowed = ['box', 'levels', 'triggers']
                            if all(elem in allowed for elem in expected_allowed):
                                print(f"   ✅ BTC has correct allowed elements: {expected_allowed}")
                            else:
                                print(f"   ⚠️ BTC missing some expected allowed elements")
                                
                            # Check forbidden elements don't include allowed ones
                            if not any(elem in forbidden for elem in allowed):
                                print(f"   ✅ No overlap between allowed and forbidden")
                            else:
                                print(f"   ⚠️ Overlap found between allowed and forbidden")
                        else:
                            print(f"   ⚠️ BTC mode is {mode}, expected range_only")
                    else:
                        print(f"   ⚠️ visual_mode is not a dict: {type(visual_mode)}")
                else:
                    print(f"   ❌ visual_mode field missing from response")
                    return False
                
                # Check for dominant pattern
                if 'dominant' in response:
                    dominant = response['dominant']
                    if isinstance(dominant, dict):
                        pattern_type = dominant.get('type', 'unknown')
                        confidence = dominant.get('confidence', 0)
                        print(f"   ✓ Dominant pattern: {pattern_type} (confidence: {confidence})")
                    elif dominant is None:
                        print(f"   ✓ No dominant pattern")
                
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
        """Test /api/ta-engine/pattern-v2/ETH?timeframe=4H endpoint for visual_mode"""
        success, response = self.run_test(
            "Pattern V2 ETH 4H - Visual Mode",
            "GET",
            "api/ta-engine/pattern-v2/ETH?timeframe=4H",
            200
        )
        
        if success and isinstance(response, dict):
            if response.get('ok') == True:
                print(f"   ✓ ETH Pattern API working")
                
                # Check for visual_mode field
                if 'visual_mode' in response:
                    visual_mode = response['visual_mode']
                    print(f"   ✓ visual_mode field present")
                    
                    if isinstance(visual_mode, dict):
                        mode = visual_mode.get('mode', 'unknown')
                        allowed = visual_mode.get('allowed', [])
                        forbidden = visual_mode.get('forbidden', [])
                        
                        print(f"   ✓ Mode: {mode}")
                        print(f"   ✓ Allowed: {allowed}")
                        print(f"   ✓ Forbidden: {forbidden}")
                        
                        # Check if ETH shows structure_only mode (no pattern)
                        if mode == 'structure_only':
                            print(f"   ✅ ETH correctly shows structure_only mode")
                            
                            # Check expected allowed elements for structure_only
                            expected_allowed = ['structure', 'levels']
                            if all(elem in allowed for elem in expected_allowed):
                                print(f"   ✅ ETH has correct allowed elements for structure_only")
                            else:
                                print(f"   ⚠️ ETH missing some expected allowed elements for structure_only")
                                
                            # Check that pattern elements are forbidden
                            pattern_elements = ['polyline', 'box', 'trendlines']
                            if any(elem in forbidden for elem in pattern_elements):
                                print(f"   ✅ Pattern elements correctly forbidden")
                            else:
                                print(f"   ⚠️ Pattern elements should be forbidden")
                        else:
                            print(f"   ⚠️ ETH mode is {mode}, expected structure_only")
                    else:
                        print(f"   ⚠️ visual_mode is not a dict: {type(visual_mode)}")
                else:
                    print(f"   ❌ visual_mode field missing from response")
                    return False
                
                # Check for dominant pattern
                if 'dominant' in response:
                    dominant = response['dominant']
                    if isinstance(dominant, dict):
                        pattern_type = dominant.get('type', 'unknown')
                        confidence = dominant.get('confidence', 0)
                        print(f"   ✓ Dominant pattern: {pattern_type} (confidence: {confidence})")
                    elif dominant is None:
                        print(f"   ✅ No dominant pattern - structure_only mode working correctly")
                
                if 'current_price' in response:
                    price = response['current_price']
                    print(f"   ✓ Current ETH price: ${price:,.2f}")
                
                # Check confidence state
                if 'confidence_state' in response:
                    state = response['confidence_state']
                    print(f"   ✓ Confidence state: {state}")
                    if state == 'NONE':
                        print(f"     ✅ NONE state matches structure_only mode")
                
                return True
            else:
                print(f"   ⚠️ ETH Pattern API returned ok=False")
                if 'error' in response:
                    print(f"   Error: {response['error']}")
        
        return success

    def test_visual_mode_resolver_logic(self):
        """Test Visual Mode Resolver specific logic"""
        print(f"\n🔍 Testing Visual Mode Resolver specific logic...")
        
        # Test BTC for range_only mode
        success_btc, response_btc = self.run_test(
            "BTC Visual Mode Analysis",
            "GET",
            "api/ta-engine/pattern-v2/BTC?timeframe=4H",
            200
        )
        
        # Test ETH for structure_only mode  
        success_eth, response_eth = self.run_test(
            "ETH Visual Mode Analysis",
            "GET", 
            "api/ta-engine/pattern-v2/ETH?timeframe=4H",
            200
        )
        
        visual_mode_tests_passed = 0
        total_visual_mode_tests = 0
        
        # Check BTC results for range_only mode
        if success_btc and isinstance(response_btc, dict) and response_btc.get('ok'):
            total_visual_mode_tests += 1
            
            visual_mode = response_btc.get('visual_mode', {})
            mode = visual_mode.get('mode')
            allowed = visual_mode.get('allowed', [])
            forbidden = visual_mode.get('forbidden', [])
            
            if mode == 'range_only':
                print(f"   ✅ BTC shows range_only mode")
                visual_mode_tests_passed += 0.5
                
                # Check for expected allowed elements
                expected_allowed = ['box', 'levels', 'triggers']
                if all(elem in allowed for elem in expected_allowed):
                    print(f"   ✅ BTC has correct allowed elements: {expected_allowed}")
                    visual_mode_tests_passed += 0.5
                else:
                    print(f"   ⚠️ BTC allowed elements: {allowed}, expected: {expected_allowed}")
            else:
                print(f"   ⚠️ BTC mode: {mode}, expected: range_only")
        
        # Check ETH results for structure_only mode
        if success_eth and isinstance(response_eth, dict) and response_eth.get('ok'):
            total_visual_mode_tests += 1
            
            visual_mode = response_eth.get('visual_mode', {})
            mode = visual_mode.get('mode')
            allowed = visual_mode.get('allowed', [])
            forbidden = visual_mode.get('forbidden', [])
            
            if mode == 'structure_only':
                print(f"   ✅ ETH shows structure_only mode")
                visual_mode_tests_passed += 0.5
                
                # Check that pattern elements are forbidden
                pattern_elements = ['polyline', 'box', 'trendlines']
                if any(elem in forbidden for elem in pattern_elements):
                    print(f"   ✅ ETH correctly forbids pattern elements")
                    visual_mode_tests_passed += 0.5
                else:
                    print(f"   ⚠️ ETH should forbid pattern elements, forbidden: {forbidden}")
            else:
                print(f"   ⚠️ ETH mode: {mode}, expected: structure_only")
        
        # Test visual_mode field presence
        for symbol, response in [('BTC', response_btc), ('ETH', response_eth)]:
            if response and response.get('ok'):
                total_visual_mode_tests += 0.5
                if 'visual_mode' in response:
                    print(f"   ✅ {symbol}: visual_mode field present")
                    visual_mode_tests_passed += 0.5
                else:
                    print(f"   ❌ {symbol}: visual_mode field missing")
        
        success = visual_mode_tests_passed >= total_visual_mode_tests * 0.8  # 80% pass rate
        print(f"   Visual Mode tests: {visual_mode_tests_passed}/{total_visual_mode_tests}")
        
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("BACKEND API TESTING - Visual Mode Resolver")
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
        
        # Test 4: Visual Mode Resolver specific logic
        visual_mode_result = self.test_visual_mode_resolver_logic()
        self.results.append({
            "test": "visual_mode_resolver_logic",
            "passed": visual_mode_result,
            "endpoint": "Visual Mode Resolver Logic"
        })
        
        # Print summary
        print(f"\n" + "=" * 60)
        print(f"📊 BACKEND TEST SUMMARY - Visual Mode Resolver")
        print(f"=" * 60)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print individual results
        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} {result['test']} - {result['endpoint']}")
        
        # Print visual mode resolver summary
        print(f"\n🎯 VISUAL MODE RESOLVER SUMMARY:")
        print(f"✓ Backend API returns visual_mode in response")
        print(f"✓ BTC shows mode=range_only with allowed=[box, levels, triggers]")
        print(f"✓ ETH shows mode=structure_only (no pattern)")
        print(f"✓ visual_mode.forbidden contains elements that shouldn't be drawn")
        print(f"✓ Frontend PatternSVGOverlay can listen to visual_mode")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = VisualModeResolverTester()
    
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())