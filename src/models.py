"""Data models for CanaSwarm Intelligence Platform."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# Input models (from Precision Platform)
class FinancialImpact(BaseModel):
    """Financial impact of zone status."""
    estimated_loss_brl_year: Optional[float] = None
    estimated_gain_brl_year: Optional[float] = None
    reform_cost_brl: Optional[float] = None
    payback_months: Optional[int] = None


class ZoneRecommendation(BaseModel):
    """Agronomic recommendation for a management zone."""
    action: str
    priority: Literal["low", "medium", "high", "critical"]
    reason: str


class ManagementZone(BaseModel):
    """Management zone with analysis and recommendations."""
    zone_id: str
    area_ha: float
    avg_yield_t_ha: float
    expected_yield_t_ha: float
    profitability_score: float
    status: Literal["optimal", "warning", "critical"]
    recommendation: ZoneRecommendation
    financial_impact: FinancialImpact


class FieldSummary(BaseModel):
    """Summary statistics for the field."""
    total_estimated_impact_brl: float
    avg_profitability_score: float


class FieldRecommendations(BaseModel):
    """Complete field analysis from Precision Platform."""
    field_id: str
    crop: str
    season: str
    harvest_number: int
    total_area_ha: float
    analysis_date: str
    summary: FieldSummary
    zones: List[ManagementZone]


# Output models (Intelligence decisions)
class PriorityLevel(BaseModel):
    """Priority level for field action."""
    level: Literal["low", "medium", "high", "critical"]
    score: float = Field(..., ge=0, le=10)
    reason: str


class DecisionAction(BaseModel):
    """Recommended action with timeline."""
    action: str
    priority: Literal["low", "medium", "high", "critical"]
    estimated_roi_brl_year: float
    implementation_cost_brl: Optional[float] = None
    payback_months: Optional[int] = None
    justification: str


class ZoneDecision(BaseModel):
    """Decision for a specific zone."""
    zone_id: str
    area_ha: float
    current_status: Literal["optimal", "warning", "critical"]
    action: DecisionAction


class FieldDecision(BaseModel):
    """Complete field decision from Intelligence Platform."""
    field_id: str
    crop: str
    season: str
    total_area_ha: float
    analysis_date: str
    decision_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    priority: PriorityLevel
    total_estimated_roi_brl_year: float
    zones: List[ZoneDecision]
    next_steps: List[str] = Field(
        default_factory=list,
        description="Actionable next steps for field manager"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "field_id": "F001-UsinaGuarani-Piracicaba",
                "crop": "cana-de-açúcar",
                "season": "2025/26",
                "total_area_ha": 150.5,
                "analysis_date": "2026-02-20",
                "decision_date": "2026-02-20 23:15:00",
                "priority": {
                    "level": "high",
                    "score": 7.5,
                    "reason": "2 zones require intervention (1 critical, 1 warning)"
                },
                "total_estimated_roi_brl_year": 234500.00,
                "zones": [
                    {
                        "zone_id": "Z001",
                        "area_ha": 45.2,
                        "current_status": "warning",
                        "action": {
                            "action": "reform",
                            "priority": "high",
                            "estimated_roi_brl_year": 120000.00,
                            "implementation_cost_brl": 15000.00,
                            "payback_months": 8,
                            "justification": "Zone Z001: 18% yield gap. Reform will recover R$ 120k/year with 8-month payback."
                        }
                    }
                ],
                "next_steps": [
                    "Schedule soil analysis for Z001 and Z003",
                    "Request reform quotes for critical zones",
                    "Monitor Z002 (optimal performance)"
                ]
            }
        }
