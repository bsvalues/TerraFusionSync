#!/usr/bin/env python3
"""
TerraFusion AI Integration Test
Verifies that NarratorAI can connect to Ollama and process property data
"""

import os
import sys
import requests
import json
import time
from datetime import datetime

def test_ollama_connection():
    """Test direct connection to Ollama service"""
    print("🔗 Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running and accessible")
            return True
        else:
            print(f"❌ Ollama responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running with: ollama serve")
        return False

def test_model_availability():
    """Check if the AI model is available"""
    print("🧠 Checking for Llama3 model...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json()
            model_names = [model['name'] for model in models.get('models', [])]
            
            if 'llama3:latest' in model_names or 'llama3' in model_names:
                print("✅ Llama3 model is available")
                return True
            else:
                print(f"⚠️  Available models: {model_names}")
                print("   Run: ollama pull llama3")
                return False
        else:
            print(f"❌ Cannot check models: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking models: {e}")
        return False

def test_ai_generation():
    """Test AI text generation with property data"""
    print("📝 Testing AI generation with sample property data...")
    
    sample_property = {
        "parcel_id": "123456789",
        "address": "456 Main Street, Benton County, WA",
        "property_type": "Residential",
        "year_built": 1985,
        "square_feet": 2400,
        "bedrooms": 3,
        "bathrooms": 2,
        "assessed_value": 425000,
        "tax_district": "503",
        "exemptions": ["Senior Citizen", "Veteran"]
    }
    
    prompt = f"""Summarize this property information in plain English for a citizen:
    
Property Details:
- Address: {sample_property['address']}
- Type: {sample_property['property_type']}
- Built: {sample_property['year_built']}
- Size: {sample_property['square_feet']} square feet
- Bedrooms: {sample_property['bedrooms']}
- Bathrooms: {sample_property['bathrooms']}
- Assessed Value: ${sample_property['assessed_value']:,}
- Tax District: {sample_property['tax_district']}
- Exemptions: {', '.join(sample_property['exemptions'])}

Please provide a clear, friendly summary that a homeowner would understand."""

    try:
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 200
            }
        }
        
        print("   Sending request to Ollama...")
        response = requests.post("http://localhost:11434/api/generate", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_summary = result.get('response', '').strip()
            
            print("✅ AI generation successful!")
            print("\n📋 Generated Property Summary:")
            print("-" * 50)
            print(ai_summary)
            print("-" * 50)
            return True
        else:
            print(f"❌ AI generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during AI generation: {e}")
        return False

def test_narrator_ai_service():
    """Test the NarratorAI Rust service if it's running"""
    print("🤖 Testing NarratorAI service...")
    try:
        response = requests.get("http://localhost:7100/api/v1/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ NarratorAI service is running")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Ollama Connected: {health_data.get('ollama_connected', False)}")
            return True
        else:
            print(f"⚠️  NarratorAI service responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("⚠️  NarratorAI service is not running")
        print("   This is optional - the Python integration works directly with Ollama")
        return False

def main():
    """Run all AI integration tests"""
    print("🧠 TerraFusion AI Integration Test")
    print("=" * 50)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Model Availability", test_model_availability),
        ("AI Generation", test_ai_generation),
        ("NarratorAI Service", test_narrator_ai_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n🎯 Results: {passed_count}/{total_count} tests passed")
    
    if passed_count >= 3:  # Ollama + Model + Generation
        print("\n🎉 AI integration is working! Your TerraFusion platform")
        print("   now has local AI capabilities for intelligent data analysis.")
    else:
        print("\n⚠️  Some tests failed. Check the setup instructions above.")
    
    return passed_count >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)