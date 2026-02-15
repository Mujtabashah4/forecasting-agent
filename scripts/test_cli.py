#!/usr/bin/env python3
"""
Test CLI for Forecasting Agent API
Provides easy testing of all endpoints
"""
import httpx
import json
from typing import Optional


BASE_URL = "http://localhost:8000/api/v1"


def get_token(username: str = "capexplan", password: str = "demo_password") -> Optional[str]:
    """Get authentication token"""
    print("🔐 Getting authentication token...")
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/token",
            json={"username": username, "password": password},
            timeout=10.0
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        print("✅ Token obtained successfully")
        return token
    except Exception as e:
        print(f"❌ Failed to get token: {e}")
        return None


def check_health():
    """Check API health"""
    print("\n💊 Checking health...")
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=10.0)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {data['status']}")
        print(f"   Version: {data['version']}")
        print(f"   LLM Status: {data['llm_status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")


def test_forecast_review(token: str):
    """Test forecast review endpoint with sample data"""
    print("\n📊 Testing forecast review...")

    # Sample request data
    sample_request = {
        "request_id": "test-request-001",
        "project": {
            "id": "PRJ-001",
            "code": "TEST_PROJECT",
            "name": "Test Infrastructure Project",
            "budget": 120000.00,
            "approved_amount": 120000.00,
            "start_date": "2024-01-01",
            "anticipated_end_date": "2024-12-31",
            "status": "active"
        },
        "fiscal_year": 2024,
        "current_month": 4,
        "forecasts": [
            {"month": 1, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": 1050.00},
            {"month": 2, "base_forecast": 1000.00, "forecast_with_rollover": 950.00, "actual": 1200.00},
            {"month": 3, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": 900.00},
            {"month": 4, "base_forecast": 1000.00, "forecast_with_rollover": 1100.00, "actual": None},
            {"month": 5, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 6, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 7, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 8, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 9, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 10, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 11, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None},
            {"month": 12, "base_forecast": 1000.00, "forecast_with_rollover": 1000.00, "actual": None}
        ],
        "purchase_orders": [
            {
                "po_number": "PO-001",
                "amount": 1000.00,
                "issue_date": "2024-01-15",
                "estimated_delivery": "2024-01-30",
                "actual_delivery": "2024-01-28",
                "status": "delivered"
            },
            {
                "po_number": "PO-002",
                "amount": 8000.00,
                "issue_date": "2024-03-20",
                "estimated_delivery": "2024-06-01",
                "actual_delivery": None,
                "status": "open"
            }
        ],
        "reason_codes": [
            {"code": "inflation", "description": "Cost increases due to price changes"},
            {"code": "normal_variance", "description": "Minor variance within typical range"}
        ]
    }

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = httpx.post(
            f"{BASE_URL}/forecast/review",
            json=sample_request,
            headers=headers,
            timeout=60.0
        )
        response.raise_for_status()
        result = response.json()

        print("✅ Forecast review completed successfully")
        print(f"\n📈 Analysis Summary:")
        print(f"   Budget Consumption: {result['analysis']['budget_consumption_percent']:.1f}%")
        print(f"   Net Order Value: ${result['analysis']['net_order_value']:,.2f}")
        print(f"   Flags Detected: {len(result['flags'])}")
        print(f"   Scenarios Generated: {len(result['scenarios'])}")
        print(f"   Questions for User: {len(result['questions'])}")

        if result['flags']:
            print(f"\n⚠️  Flags:")
            for flag in result['flags']:
                print(f"   - {flag['type']}: {flag['message']}")

        if result['scenarios']:
            print(f"\n💡 Scenarios:")
            for scenario in result['scenarios']:
                print(f"   - {scenario['name']}: {scenario['description']}")

        print(f"\n📝 Explanation:")
        print(f"   {result['explanation']}")

        # Save full response to file
        with open("test_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n💾 Full response saved to test_response.json")

    except Exception as e:
        print(f"❌ Forecast review failed: {e}")


def main():
    """Main test function"""
    print("=" * 60)
    print("Forecasting Agent API Test CLI")
    print("=" * 60)

    # Check health
    check_health()

    # Get token
    token = get_token()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return

    # Test forecast review
    test_forecast_review(token)

    print("\n" + "=" * 60)
    print("✅ All tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()
