#!/usr/bin/env python3
"""
Backend API Testing for TA Engine
=================================

Tests all required endpoints:
1. Backend health endpoint /api/health returns ok=true
2. TA Engine MTF endpoint /api/ta-engine/mtf/BTC returns analysis data
3. TA Setup V2 endpoint /api/ta/setup/v2?symbol=BTC&timeframe=4H returns trade_setup and execution_plan
4. Execution plan returns valid=false when market is conflicted/neutral (no_trade)
5. Coinbase adapter module exists and properly structured
"""

import requests
import sys
import json
from datetime import datetime

class TAEngineAPITester:
    def __init__(self, base_url="https://ta-module-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, validate_func=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            else:
                raise Exception(f"Unsupported method: {method}")

            print(f"   Status: {response.status_code}")
            
            # Check status code
            if response.status_code != expected_status:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}...")
                self.results.append({
                    "test": name,
                    "status": "FAILED",
                    "reason": f"Status {response.status_code} != {expected_status}",
                    "response": response.text[:200] if response.text else None
                })
                return False, {}

            # Parse JSON response
            try:
                response_data = response.json() if response.text else {}
            except json.JSONDecodeError as e:
                print(f"❌ Failed - Invalid JSON response: {e}")
                self.results.append({
                    "test": name,
                    "status": "FAILED", 
                    "reason": f"Invalid JSON: {e}",
                    "response": response.text[:200] if response.text else None
                })
                return False, {}

            # Custom validation
            if validate_func:
                validation_result = validate_func(response_data)
                if not validation_result["valid"]:
                    print(f"❌ Failed - Validation: {validation_result['reason']}")
                    self.results.append({
                        "test": name,
                        "status": "FAILED",
                        "reason": validation_result["reason"],
                        "response": json.dumps(response_data, indent=2)[:300]
                    })
                    return False, response_data

            self.tests_passed += 1
            print(f"✅ Passed")
            self.results.append({
                "test": name,
                "status": "PASSED",
                "response_summary": self._summarize_response(response_data)
            })
            return True, response_data

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            self.results.append({
                "test": name,
                "status": "FAILED",
                "reason": "Request timeout (30s)"
            })
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.results.append({
                "test": name,
                "status": "FAILED",
                "reason": str(e)
            })
            return False, {}

    def _summarize_response(self, data):
        """Create a summary of response data"""
        if isinstance(data, dict):
            summary = {}
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        summary[key] = f"Array[{len(value)}]"
                    else:
                        summary[key] = f"Object with {len(value)} keys"
                else:
                    summary[key] = value
            return summary
        return str(data)[:100]

    def validate_health_response(self, data):
        """Validate health endpoint response"""
        if not isinstance(data, dict):
            return {"valid": False, "reason": "Response is not a JSON object"}
        
        if not data.get("ok"):
            return {"valid": False, "reason": "ok field is not true"}
        
        required_fields = ["mode", "version", "timestamp"]
        for field in required_fields:
            if field not in data:
                return {"valid": False, "reason": f"Missing required field: {field}"}
        
        return {"valid": True}

    def validate_mtf_response(self, data):
        """Validate MTF endpoint response"""
        if not isinstance(data, dict):
            return {"valid": False, "reason": "Response is not a JSON object"}
        
        # Check for MTF analysis data structure
        if not data.get("ok"):
            return {"valid": False, "reason": "ok field is not true"}
        
        required_fields = ["symbol", "tf_map", "mtf_context"]
        for field in required_fields:
            if field not in data:
                return {"valid": False, "reason": f"Missing required field: {field}"}
        
        # Check tf_map has data
        tf_map = data.get("tf_map", {})
        if not tf_map:
            return {"valid": False, "reason": "tf_map is empty"}
        
        return {"valid": True}

    def validate_setup_v2_response(self, data):
        """Validate TA Setup V2 endpoint response"""
        if not isinstance(data, dict):
            return {"valid": False, "reason": "Response is not a JSON object"}
        
        # Check for required fields
        required_fields = ["symbol", "timeframe"]
        for field in required_fields:
            if field not in data:
                return {"valid": False, "reason": f"Missing required field: {field}"}
        
        # Check for trade setup or execution plan
        has_trade_setup = "trade_setup" in data
        has_execution_plan = "execution_plan" in data
        has_scenarios = "scenarios" in data
        
        if not (has_trade_setup or has_execution_plan or has_scenarios):
            return {"valid": False, "reason": "Missing trade_setup, execution_plan, or scenarios"}
        
        return {"valid": True}

    def validate_no_trade_scenario(self, data):
        """Validate that execution plan returns valid=false for conflicted markets"""
        if not isinstance(data, dict):
            return {"valid": False, "reason": "Response is not a JSON object"}
        
        # Check execution plan
        execution_plan = data.get("execution_plan", {})
        if execution_plan and execution_plan.get("valid") is True:
            # This might be a valid trade - check if confidence is clear
            decision = data.get("decision", {})
            confidence_state = decision.get("confidence_state", "").lower()
            
            if confidence_state == "clear":
                return {"valid": True, "reason": "Valid trade with CLEAR confidence"}
            else:
                return {"valid": False, "reason": f"Execution plan valid=true but confidence_state={confidence_state} (should be CLEAR for valid trades)"}
        
        # Check if it properly returns no trade
        if execution_plan and execution_plan.get("valid") is False:
            return {"valid": True, "reason": "Correctly returns no trade scenario"}
        
        return {"valid": True, "reason": "No execution plan found (acceptable)"}

    def test_coinbase_adapter_structure(self):
        """Test Coinbase adapter module structure"""
        print(f"\n🔍 Testing Coinbase Adapter Structure...")
        
        try:
            # Check if file exists and has proper structure
            import os
            adapter_path = "/app/backend/modules/broker_adapters/coinbase_adapter.py"
            
            if not os.path.exists(adapter_path):
                print(f"❌ Failed - Coinbase adapter file not found at {adapter_path}")
                self.results.append({
                    "test": "Coinbase Adapter Structure",
                    "status": "FAILED",
                    "reason": "Adapter file not found"
                })
                return False
            
            # Read and check basic structure
            with open(adapter_path, 'r') as f:
                content = f.read()
            
            required_elements = [
                "class CoinbaseAdapter",
                "async def connect",
                "async def get_balance",
                "async def place_order",
                "async def get_candles"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"❌ Failed - Missing required elements: {missing_elements}")
                self.results.append({
                    "test": "Coinbase Adapter Structure",
                    "status": "FAILED",
                    "reason": f"Missing elements: {missing_elements}"
                })
                return False
            
            print(f"✅ Passed - Coinbase adapter properly structured")
            self.results.append({
                "test": "Coinbase Adapter Structure",
                "status": "PASSED",
                "response_summary": "All required methods found"
            })
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"❌ Failed - Error checking adapter: {str(e)}")
            self.results.append({
                "test": "Coinbase Adapter Structure",
                "status": "FAILED",
                "reason": str(e)
            })
            return False
        finally:
            self.tests_run += 1

    def run_all_tests(self):
        """Run all required tests"""
        print("=" * 60)
        print("TA ENGINE BACKEND API TESTING")
        print("=" * 60)
        
        # Test 1: Health endpoint
        self.run_test(
            "Backend Health Check",
            "GET",
            "/api/health",
            validate_func=self.validate_health_response
        )
        
        # Test 2: TA Engine MTF endpoint
        self.run_test(
            "TA Engine MTF Analysis",
            "GET", 
            "/api/ta-engine/mtf/BTC",
            validate_func=self.validate_mtf_response
        )
        
        # Test 3: TA Setup V2 endpoint - 4H timeframe
        success, setup_data = self.run_test(
            "TA Setup V2 - 4H Timeframe",
            "GET",
            "/api/ta/setup/v2?symbol=BTC&timeframe=4H",
            validate_func=self.validate_setup_v2_response
        )
        
        # Test 4: Check execution plan logic
        if success and setup_data:
            self.run_test(
                "Execution Plan Logic Check",
                "GET",
                "/api/ta/setup/v2?symbol=BTC&timeframe=4H",
                validate_func=self.validate_no_trade_scenario
            )
        
        # Test 5: TA Setup V2 endpoint - 1D timeframe (different timeframe)
        self.run_test(
            "TA Setup V2 - 1D Timeframe",
            "GET",
            "/api/ta/setup/v2?symbol=BTC&timeframe=1D",
            validate_func=self.validate_setup_v2_response
        )
        
        # Test 6: Coinbase adapter structure
        self.test_coinbase_adapter_structure()
        
        # Test 7: Provider status
        self.run_test(
            "Coinbase Provider Status",
            "GET",
            "/api/provider/coinbase/status"
        )
        
        # Print results
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"{status_icon} {result['test']}: {result['status']}")
            if result["status"] == "FAILED":
                print(f"   Reason: {result['reason']}")
        
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = TAEngineAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())