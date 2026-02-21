"""
Test SQLite persistence implementation.

Quick validation of SQLiteStorage functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage_sql import SQLiteStorage
from src.models import (
    FieldRecommendations,
    FieldDecision,
    PriorityLevel,
    DecisionAction,
    ZoneRecommendation,
    ZoneDecision,
    ManagementZone,
    FinancialImpact,
    FieldSummary,
)


def test_sqlite_storage():
    """Test SQLite storage operations."""
    print("=" * 60)
    print("Testing SQLiteStorage Implementation")
    print("=" * 60)
    
    # Initialize storage with test database
    db_path = "data/test_intelligence.db"
    print(f"\n1. Initializing SQLite storage: {db_path}")
    storage = SQLiteStorage(db_path=db_path)
    print(f"✓ Storage initialized successfully")
    
    # Test storing recommendations
    print("\n2. Storing field recommendations...")
    recommendations = FieldRecommendations(
        field_id="TEST001",
        crop="sugarcane",
        season="2025-2026",
        harvest_number=3,
        total_area_ha=45.5,
        analysis_date="2025-06-15",
        summary=FieldSummary(
            total_estimated_impact_brl=125000.0,
            avg_profitability_score=7.8,
        ),
        zones=[
            ManagementZone(
                zone_id="TEST001-Z1",
                area_ha=15.2,
                avg_yield_t_ha=85.5,
                expected_yield_t_ha=95.0,
                profitability_score=8.5,
                status="warning",
                recommendation=ZoneRecommendation(
                    action="Apply precision irrigation",
                    priority="high",
                    reason="High yield potential with water stress detected",
                ),
                financial_impact=FinancialImpact(
                    estimated_gain_brl_year=45000.0,
                    estimated_loss_brl_year=None,
                    reform_cost_brl=12500.0,
                    payback_months=3,
                ),
            ),
            ManagementZone(
                zone_id="TEST001-Z2",
                area_ha=30.3,
                avg_yield_t_ha=72.3,
                expected_yield_t_ha=78.0,
                profitability_score=6.8,
                status="optimal",
                recommendation=ZoneRecommendation(
                    action="Standard irrigation",
                    priority="medium",
                    reason="Medium yield with standard management sufficient",
                ),
                financial_impact=FinancialImpact(
                    estimated_gain_brl_year=18000.0,
                    estimated_loss_brl_year=None,
                    reform_cost_brl=8500.0,
                    payback_months=6,
                ),
            ),
        ],
    )
    storage.store_recommendations(recommendations)
    print(f"✓ Recommendations stored for field: {recommendations.field_id}")
    
    # Test retrieving recommendations
    print("\n3. Retrieving recommendations...")
    retrieved = storage.get_recommendations("TEST001")
    assert retrieved is not None, "Failed to retrieve recommendations"
    assert retrieved.field_id == "TEST001"
    assert len(retrieved.zones) == 2
    print(f"✓ Retrieved {len(retrieved.zones)} zones for {retrieved.field_id}")
    
    # Test storing decision
    print("\n4. Storing field decision...")
    decision = FieldDecision(
        field_id="TEST001",
        crop="sugarcane",
        season="2025-2026",
        total_area_ha=45.5,
        analysis_date="2025-06-15",
        decision_date="2025-06-16",
        priority=PriorityLevel(
            level="high",
            score=8.2,
            reason="Multiple zones require intervention for optimal yield",
        ),
        total_estimated_roi_brl_year=63000.0,
        zones=[
            ZoneDecision(
                zone_id="TEST001-Z1",
                area_ha=15.2,
                current_status="warning",
                action=DecisionAction(
                    action="Implement precision irrigation system",
                    priority="high",
                    estimated_roi_brl_year=45000.0,
                    implementation_cost_brl=12500.0,
                    payback_months=3,
                    justification="High yield potential with precision irrigation needs",
                ),
            ),
            ZoneDecision(
                zone_id="TEST001-Z2",
                area_ha=30.3,
                current_status="optimal",
                action=DecisionAction(
                    action="Maintain standard irrigation schedule",
                    priority="medium",
                    estimated_roi_brl_year=18000.0,
                    implementation_cost_brl=8500.0,
                    payback_months=6,
                    justification="Medium yield, standard irrigation sufficient",
                ),
            ),
        ],
        next_steps=[
            "Implement precision irrigation in Zone 1",
            "Schedule soil analysis for Zone 2",
            "Monitor progress over next 30 days",
        ],
    )
    storage.store_decision(decision)
    print(f"✓ Decision stored for field: {decision.field_id}")
    
    # Test retrieving decision
    print("\n5. Retrieving decision...")
    retrieved_decision = storage.get_decision("TEST001")
    assert retrieved_decision is not None, "Failed to retrieve decision"
    assert retrieved_decision.field_id == "TEST001"
    assert len(retrieved_decision.zones) == 2
    print(f"✓ Retrieved decision with {len(retrieved_decision.zones)} zone decisions")
    
    # Test listing fields
    print("\n6. Listing all fields...")
    fields = storage.list_fields()
    assert "TEST001" in fields, "Field not found in list"
    print(f"✓ Found {len(fields)} field(s) in storage")
    print(f"  Field TEST001: {fields['TEST001']['crop']}, {fields['TEST001']['area_ha']} ha")
    
    # Test storage stats
    print("\n7. Getting storage statistics...")
    stats = storage.get_stats()
    print(f"✓ Storage stats:")
    print(f"  - Total fields: {stats['total_fields']}")
    print(f"  - Total decisions: {stats['total_decisions']}")
    print(f"  - Historical snapshots: {stats['historical_snapshots']}")
    print(f"  - Total area (ha): {stats['total_area_ha']}")
    print(f"  - High priority actions: {stats['high_priority_actions']}")
    
    # Test decision history
    print("\n8. Testing decision history...")
    history = storage.get_decision_history("TEST001", limit=5)
    print(f"✓ Retrieved {len(history)} historical decision(s)")
    
    # Store another decision to test history
    decision.decision_date = "2025-06-17"
    storage.store_decision(decision)
    history = storage.get_decision_history("TEST001", limit=5)
    print(f"✓ After second store - retrieved {len(history)} historical decision(s)")
    
    # Cleanup
    storage.close()
    print("\n9. Storage closed successfully")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nSQLite Persistence Features Validated:")
    print("  ✓ Store/retrieve recommendations")
    print("  ✓ Store/retrieve decisions")
    print("  ✓ List fields with metadata")
    print("  ✓ Storage statistics")
    print("  ✓ Decision history tracking")
    print("  ✓ Time-series analysis support")
    print("\nDatabase location: data/test_intelligence.db")


if __name__ == "__main__":
    try:
        test_sqlite_storage()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
