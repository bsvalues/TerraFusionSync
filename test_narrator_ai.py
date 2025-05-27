#!/usr/bin/env python3
"""
Test script for NarratorAI Service
Demonstrates AI-powered property data processing capabilities
"""

import requests
import json
import time

NARRATOR_AI_URL = "http://localhost:7100"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing NarratorAI health...")
    try:
        response = requests.get(f"{NARRATOR_AI_URL}/api/v1/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Service: {health_data['service']} v{health_data['version']}")
            print(f"✅ Status: {health_data['status']}")
            print(f"✅ Ollama Connected: {health_data['ollama_connected']}")
            if health_data['available_models']:
                print(f"✅ Available Models: {', '.join(health_data['available_models'])}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_summarize():
    """Test property summarization"""
    print("\n📝 Testing property summarization...")
    
    sample_property = """
    Property ID: 12345-BENTON-WA. This is a 2-story single-family residential home 
    built in 1995, located at 123 Maple Street in the Kennewick residential district. 
    Total square footage: 2,400 sq ft. Lot size: 0.25 acres (10,890 sq ft). 
    Bedrooms: 4, Bathrooms: 3.5. Garage: 2-car attached. 
    Assessed value: $485,000. Market value: $520,000. 
    Last sale: $420,000 in December 2019. 
    Tax district: 503. School district: Kennewick School District.
    Special features: Updated kitchen (2020), new roof (2018), 
    central air conditioning, hardwood floors.
    """
    
    try:
        response = requests.post(
            f"{NARRATOR_AI_URL}/api/v1/summarize",
            json={
                "text": sample_property,
                "max_tokens": 500,
                "temperature": 0.7
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Summary generated in {result['processing_time_ms']}ms")
            print(f"🤖 Model used: {result['model_used']}")
            print(f"📄 Summary: {result['result']}")
            return True
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_classify():
    """Test property classification"""
    print("\n🏷️ Testing property classification...")
    
    properties = [
        "Single-family residential home with 3 bedrooms and 2 bathrooms",
        "Multi-unit apartment complex with 24 units and commercial retail space",
        "Agricultural farmland with barn and grain storage facilities",
        "Office building with medical and professional services"
    ]
    
    for i, prop in enumerate(properties, 1):
        print(f"\n  Testing property {i}: {prop[:50]}...")
        try:
            response = requests.post(
                f"{NARRATOR_AI_URL}/api/v1/classify",
                json={
                    "text": prop,
                    "max_tokens": 200,
                    "temperature": 0.3
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Classification: {result['result']}")
            else:
                print(f"  ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_explain():
    """Test data explanation"""
    print("\n💡 Testing assessment data explanation...")
    
    assessment_data = """
    Mill rate: 1.2%, Assessed value: $485,000, Market value: $520,000, 
    Exemptions: Homestead $50,000, Senior $15,000, 
    Taxable value: $420,000, Annual tax: $5,040,
    Payment schedule: Semi-annual (June 30, December 31)
    """
    
    try:
        response = requests.post(
            f"{NARRATOR_AI_URL}/api/v1/explain",
            json={
                "text": assessment_data,
                "max_tokens": 600,
                "temperature": 0.5
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Explanation generated in {result['processing_time_ms']}ms")
            print(f"📚 Explanation: {result['result']}")
            return True
        else:
            print(f"❌ Explanation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    print("\n📊 Testing metrics endpoint...")
    try:
        response = requests.get(f"{NARRATOR_AI_URL}/api/v1/metrics")
        if response.status_code == 200:
            metrics = response.text
            print("✅ Metrics endpoint working")
            # Count metrics
            metric_lines = [line for line in metrics.split('\n') if line and not line.startswith('#')]
            print(f"📈 Found {len(metric_lines)} metric measurements")
            return True
        else:
            print(f"❌ Metrics failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 NarratorAI Service Test Suite")
    print("=" * 50)
    
    # Test health first
    if not test_health():
        print("\n❌ Service not available. Make sure NarratorAI is running on port 7100")
        print("   To start: cd ai/narrator_ai && cargo run")
        return
    
    # Run all tests
    tests = [
        test_summarize,
        test_classify, 
        test_explain,
        test_metrics
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! NarratorAI is working perfectly!")
        print("\n💡 Integration tips:")
        print("   • Add AI analysis to your GIS export workflows")
        print("   • Use summarization for property owner communications") 
        print("   • Integrate classification for automated data processing")
        print("   • Monitor performance with the metrics endpoint")
    else:
        print("⚠️ Some tests failed. Check the service configuration.")

if __name__ == "__main__":
    main()