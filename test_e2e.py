"""
End-to-End Integration Test: Precision Platform → Intelligence Platform

Tests the complete data flow:
1. Precision API: GET /recommendations
2. Intelligence API: POST /ingest
3. Intelligence API: GET /decision
"""

import requests
import json
from datetime import datetime


# API URLs
PRECISION_API = "http://localhost:5000"
INTELLIGENCE_API = "http://localhost:6000"

# Test field
FIELD_ID = "F001"


def test_precision_api():
    """Test Precision Platform API"""
    print("\n" + "="*70)
    print("STEP 1: Testing Precision Platform API")
    print("="*70)
    
    url = f"{PRECISION_API}/api/v1/recommendations?field_id={FIELD_ID}"
    print(f"📡 GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ SUCCESS: Received recommendations")
        print(f"   Field: {data['field_id']}")
        print(f"   Zones: {len(data['zones'])}")
        print(f"   Total Impact: R$ {data['summary']['total_estimated_impact_brl']:,.2f}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        return None


def test_intelligence_ingest(recommendations):
    """Test Intelligence Platform ingest endpoint"""
    print("\n" + "="*70)
    print("STEP 2: Testing Intelligence Platform - Ingest")
    print("="*70)
    
    url = f"{INTELLIGENCE_API}/api/v1/precision/ingest"
    print(f"📡 POST {url}")
    
    try:
        response = requests.post(
            url,
            json=recommendations,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ SUCCESS: Data ingested")
        print(f"   Field: {data['field_id']}")
        print(f"   Zones analyzed: {data['zones_analyzed']}")
        print(f"   Priority: {data['priority']}")
        print(f"   Estimated ROI: R$ {data['estimated_roi_brl_year']:,.2f}/year")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def test_intelligence_decision():
    """Test Intelligence Platform decision endpoint"""
    print("\n" + "="*70)
    print("STEP 3: Testing Intelligence Platform - Decision")
    print("="*70)
    
    url = f"{INTELLIGENCE_API}/api/v1/decision?field_id={FIELD_ID}"
    print(f"📡 GET {url}")
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ SUCCESS: Decision retrieved")
        print(f"   Field: {data['field_id']}")
        print(f"   Priority: {data['priority']['level']} (score: {data['priority']['score']:.1f}/10)")
        print(f"   Reason: {data['priority']['reason']}")
        print(f"   Total ROI: R$ {data['total_estimated_roi_brl_year']:,.2f}/year")
        print(f"\n   Zone Decisions: {len(data['zones'])}")
        
        for zone in data['zones']:
            status_emoji = {"optimal": "🟢", "warning": "🟡", "critical": "🔴"}
            emoji = status_emoji.get(zone['current_status'], "⚪")
            print(f"   {emoji} {zone['zone_id']}: {zone['action']['action']} (priority: {zone['action']['priority']})")
            print(f"      ROI: R$ {zone['action']['estimated_roi_brl_year']:,.0f}/year")
        
        print(f"\n   Next Steps ({len(data['next_steps'])}):")
        for i, step in enumerate(data['next_steps'], 1):
            print(f"   {i}. {step}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return None


def main():
    """Run end-to-end integration test"""
    print("\n" + "🧪"*35)
    print("E2E INTEGRATION TEST: Precision → Intelligence")
    print("🧪"*35)
    
    # Step 1: Get recommendations from Precision API
    recommendations = test_precision_api()
    if not recommendations:
        print("\n❌ FAILED: Could not retrieve recommendations from Precision API")
        print("   Make sure Precision API is running on http://localhost:5000")
        return False
    
    # Step 2: Send recommendations to Intelligence API (ingest)
    ingest_result = test_intelligence_ingest(recommendations)
    if not ingest_result:
        print("\n❌ FAILED: Could not ingest data into Intelligence API")
        print("   Make sure Intelligence API is running on http://localhost:6000")
        return False
    
    # Step 3: Get decision from Intelligence API
    decision = test_intelligence_decision()
    if not decision:
        print("\n❌ FAILED: Could not retrieve decision from Intelligence API")
        return False
    
    # Success!
    print("\n" + "="*70)
    print("✅ E2E TEST PASSED: Complete data flow working!")
    print("="*70)
    print("\nData Flow Summary:")
    print("  1. ✅ Precision API provided field recommendations")
    print("  2. ✅ Intelligence API ingested and processed data")
    print("  3. ✅ Intelligence API generated actionable decision")
    print("\n🎉 Integration successful: Precision → Intelligence")
    print("="*70 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
