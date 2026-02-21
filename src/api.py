"""
CanaSwarm Intelligence Platform - REST API

Aggregates data from Precision Platform and provides actionable decisions.
"""

from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .models import (
    FieldRecommendations,
    FieldDecision,
    PriorityLevel,
    DecisionAction,
    ZoneDecision,
)
from .storage import InMemoryStorage


# Initialize FastAPI app
app = FastAPI(
    title="CanaSwarm Intelligence Platform API",
    description="Decision support system for agricultural field management",
    version="1.0.0",
    contact={
        "name": "AvilaOps",
        "url": "https://github.com/avilaops/CanaSwarm-Intelligence",
    },
)

# Initialize storage
storage = InMemoryStorage(data_dir="data")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "CanaSwarm Intelligence Platform API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "ingest": "/api/v1/precision/ingest (POST)",
            "decision": "/api/v1/decision (GET)",
            "fields": "/api/v1/fields (GET)",
            "health": "/health (GET)",
            "docs": "/docs (GET)",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    fields = storage.list_fields()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "stored_fields": len(fields),
        "fields_with_decisions": sum(1 for f in fields.values() if f["has_decision"]),
    }


@app.get("/api/v1/fields")
async def list_fields():
    """List all stored fields."""
    fields = storage.list_fields()
    return {
        "fields": list(fields.values()),
        "total": len(fields),
    }


@app.post(
    "/api/v1/precision/ingest",
    status_code=201,
    summary="Ingest Precision Platform data",
    description="Receive and store field recommendations from Precision Platform",
)
async def ingest_precision_data(recommendations: FieldRecommendations):
    """
    Ingest field recommendations from Precision Platform.
    
    This endpoint:
    1. Receives zone-based analysis from Precision Platform
    2. Stores recommendations for decision processing
    3. Automatically generates field decision
    
    Args:
        recommendations: Field recommendations from Precision Platform
        
    Returns:
        Confirmation with field ID and decision summary
    """
    # Store recommendations
    storage.store_recommendations(recommendations)
    
    # Generate decision from recommendations
    decision = _generate_decision(recommendations)
    storage.store_decision(decision)
    
    return {
        "message": "Data ingested successfully",
        "field_id": recommendations.field_id,
        "zones_analyzed": len(recommendations.zones),
        "decision_generated": True,
        "priority": decision.priority.level,
        "estimated_roi_brl_year": decision.total_estimated_roi_brl_year,
    }


@app.get(
    "/api/v1/decision",
    response_model=FieldDecision,
    summary="Get field decision",
    description="Retrieve actionable decision for a field",
)
async def get_field_decision(
    field_id: str = Query(
        ...,
        description="Field identifier (e.g., F001)",
        min_length=1,
        max_length=50,
    )
) -> FieldDecision:
    """
    Get actionable decision for a field.
    
    Returns:
    - Priority level and score
    - Zone-specific actions with ROI estimates
    - Next steps for field manager
    
    Args:
        field_id: Field identifier
        
    Returns:
        FieldDecision with prioritized actions
        
    Raises:
        404: Field not found or no decision available
    """
    # Get decision from storage
    decision = storage.get_decision(field_id)
    
    if not decision:
        # Try to generate decision from stored recommendations
        recommendations = storage.get_recommendations(field_id)
        if not recommendations:
            raise HTTPException(
                status_code=404,
                detail=f"No data available for field '{field_id}'. Please ingest Precision data first.",
            )
        
        # Generate and store decision
        decision = _generate_decision(recommendations)
        storage.store_decision(decision)
    
    return decision


def _generate_decision(recommendations: FieldRecommendations) -> FieldDecision:
    """
    Generate field decision from Precision recommendations.
    
    This is the core intelligence logic that:
    1. Analyzes zone recommendations
    2. Prioritizes actions
    3. Calculates ROI
    4. Generates next steps
    
    Args:
        recommendations: Field recommendations from Precision Platform
        
    Returns:
        FieldDecision with actionable intelligence
    """
    # Analyze zones and generate zone decisions
    zone_decisions: List[ZoneDecision] = []
    total_roi = 0.0
    critical_zones = 0
    warning_zones = 0
    
    for zone in recommendations.zones:
        # Determine ROI based on financial impact
        if zone.financial_impact.estimated_gain_brl_year:
            roi = zone.financial_impact.estimated_gain_brl_year
        elif zone.financial_impact.estimated_loss_brl_year:
            roi = zone.financial_impact.estimated_loss_brl_year
        else:
            roi = 0.0
        
        total_roi += roi
        
        # Count critical/warning zones
        if zone.status == "critical":
            critical_zones += 1
        elif zone.status == "warning":
            warning_zones += 1
        
        # Generate zone decision
        zone_decision = ZoneDecision(
            zone_id=zone.zone_id,
            area_ha=zone.area_ha,
            current_status=zone.status,
            action=DecisionAction(
                action=zone.recommendation.action,
                priority=zone.recommendation.priority,
                estimated_roi_brl_year=abs(roi),
                implementation_cost_brl=zone.financial_impact.reform_cost_brl,
                payback_months=zone.financial_impact.payback_months,
                justification=_generate_justification(zone, roi),
            ),
        )
        zone_decisions.append(zone_decision)
    
    # Determine overall priority
    priority = _calculate_priority(
        critical_zones=critical_zones,
        warning_zones=warning_zones,
        avg_score=recommendations.summary.avg_profitability_score,
    )
    
    # Generate next steps
    next_steps = _generate_next_steps(recommendations, critical_zones, warning_zones)
    
    return FieldDecision(
        field_id=recommendations.field_id,
        crop=recommendations.crop,
        season=recommendations.season,
        total_area_ha=recommendations.total_area_ha,
        analysis_date=recommendations.analysis_date,
        priority=priority,
        total_estimated_roi_brl_year=abs(total_roi),
        zones=zone_decisions,
        next_steps=next_steps,
    )


def _generate_justification(zone, roi: float) -> str:
    """Generate human-readable justification for zone action."""
    gap_pct = (
        (zone.expected_yield_t_ha - zone.avg_yield_t_ha) / zone.expected_yield_t_ha * 100
    )
    
    if zone.status == "optimal":
        return f"Zone {zone.zone_id}: Performing at {100-gap_pct:.0f}% of potential. Maintain current management."
    
    justification = f"Zone {zone.zone_id}: {gap_pct:.0f}% yield gap. "
    
    if roi < 0:
        justification += f"{zone.recommendation.action.replace('_', ' ').title()} will recover R$ {abs(roi):,.0f}/year"
        if zone.financial_impact.payback_months:
            justification += f" with {zone.financial_impact.payback_months}-month payback"
    else:
        justification += f"Expected gain: R$ {roi:,.0f}/year"
    
    justification += "."
    return justification


def _calculate_priority(
    critical_zones: int, warning_zones: int, avg_score: float
) -> PriorityLevel:
    """Calculate overall field priority."""
    if critical_zones > 0:
        level = "critical"
        score = 9.0 + min(critical_zones * 0.5, 1.0)
        reason = f"{critical_zones} critical zone(s) require immediate intervention"
    elif warning_zones > 1:
        level = "high"
        score = 7.0 + min(warning_zones * 0.5, 2.0)
        reason = f"{warning_zones} zone(s) require intervention"
    elif warning_zones == 1:
        level = "medium"
        score = 5.0 + avg_score / 2
        reason = "1 zone requires attention"
    else:
        level = "low"
        score = avg_score
        reason = "Field performing optimally"
    
    return PriorityLevel(
        level=level,
        score=min(score, 10.0),
        reason=reason,
    )


def _generate_next_steps(
    recommendations: FieldRecommendations, critical_zones: int, warning_zones: int
) -> List[str]:
    """Generate actionable next steps for field manager."""
    steps = []
    
    # Identify zones requiring action
    critical_zone_ids = [
        z.zone_id for z in recommendations.zones if z.status == "critical"
    ]
    warning_zone_ids = [
        z.zone_id for z in recommendations.zones if z.status == "warning"
    ]
    
    if critical_zone_ids:
        steps.append(
            f"🔴 URGENT: Schedule soil analysis for critical zones: {', '.join(critical_zone_ids)}"
        )
        steps.append(f"Request reform quotes for zones: {', '.join(critical_zone_ids)}")
    
    if warning_zone_ids:
        steps.append(
            f"🟡 Schedule intervention for warning zones: {', '.join(warning_zone_ids)}"
        )
    
    # Check for optimal zones
    optimal_zones = [z.zone_id for z in recommendations.zones if z.status == "optimal"]
    if optimal_zones:
        steps.append(f"🟢 Monitor optimal zones: {', '.join(optimal_zones)}")
    
    # Financial planning
    if critical_zones > 0 or warning_zones > 0:
        total_reform_cost = sum(
            z.financial_impact.reform_cost_brl or 0
            for z in recommendations.zones
            if z.status in ["critical", "warning"]
        )
        if total_reform_cost > 0:
            steps.append(
                f"💰 Budget allocation: R$ {total_reform_cost:,.0f} for reforms"
            )
    
    # Schedule follow-up
    steps.append(f"📅 Schedule follow-up analysis in 30 days")
    
    return steps


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for better error messages."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=6000)
