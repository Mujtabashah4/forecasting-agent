"""
Request schemas for API endpoints
Based on Section 5.1 of implementation guide
"""
from pydantic import BaseModel, Field
from typing import List
from app.schemas.common import ProjectInfo, ForecastMonth, PurchaseOrder, ReasonCode


class ForecastReviewRequest(BaseModel):
    """
    Request to review project forecast
    This is what Capexplan sends to the AI Server
    """
    request_id: str = Field(..., description="Unique request identifier from Capexplan")
    project: ProjectInfo
    fiscal_year: int = Field(..., ge=2000, le=2100)
    current_month: int = Field(..., ge=1, le=12, description="Current month number in fiscal year")
    forecasts: List[ForecastMonth] = Field(..., min_length=12, max_length=12)
    purchase_orders: List[PurchaseOrder] = Field(default_factory=list)
    reason_codes: List[ReasonCode] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "project": {
                    "id": "PRJ-001",
                    "code": "PROJECT_CODE",
                    "name": "Sample Infrastructure Project",
                    "budget": 120000.00,
                    "approved_amount": 120000.00,
                    "start_date": "2024-01-01",
                    "anticipated_end_date": "2024-12-31",
                    "status": "active"
                },
                "fiscal_year": 2024,
                "current_month": 4,
                "forecasts": [
                    {
                        "month": 1,
                        "base_forecast": 1000.00,
                        "forecast_with_rollover": 1000.00,
                        "actual": 1050.00
                    },
                    {
                        "month": 2,
                        "base_forecast": 1000.00,
                        "forecast_with_rollover": 950.00,
                        "actual": 1200.00
                    }
                ],
                "purchase_orders": [
                    {
                        "po_number": "PO-001",
                        "amount": 1000.00,
                        "issue_date": "2024-01-15",
                        "estimated_delivery": "2024-01-30",
                        "actual_delivery": "2024-01-28",
                        "status": "delivered"
                    }
                ],
                "reason_codes": [
                    {"code": "inflation", "description": "Cost increases due to price changes"},
                    {"code": "normal_variance", "description": "Minor variance within typical range"}
                ]
            }
        }


class TokenRequest(BaseModel):
    """Request to get authentication token"""
    username: str
    password: str


class ReasonCodeWithPercent(BaseModel):
    """Reason code with contribution percentage"""
    code: str = Field(..., description="Reason code identifier")
    percent: int = Field(..., ge=0, le=100, description="Contribution percentage (0-100)")


class QuestionResponseRequest(BaseModel):
    """
    Request to submit a response to a question.

    Client Requirement:
    "Human will enter a reason or multiple reasons and also a contribution
    in percentage to that reason (ex: weather is 50% and inflation is the other 50%)"
    """
    session_id: str = Field(..., description="Session ID from forecast review response")
    question_id: str = Field(..., description="Question ID being answered")
    response_value: str = Field(..., description="Selected option value")
    reason_codes: List[ReasonCodeWithPercent] = Field(
        default_factory=list,
        description="Reason codes with percentages (should sum to 100)"
    )
    notes: str = Field(default="", description="Optional free-text notes")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "agent-session-uuid",
                "question_id": "q1",
                "response_value": "spread",
                "reason_codes": [
                    {"code": "weather_impact", "percent": 50},
                    {"code": "inflation", "percent": 50}
                ],
                "notes": "Supplier confirmed delayed delivery due to weather"
            }
        }


class ScenarioApprovalRequest(BaseModel):
    """
    Request to approve and apply a scenario.

    This is the final step where the user selects which scenario to apply
    and provides reason codes for the changes.
    """
    session_id: str = Field(..., description="Session ID from forecast review response")
    scenario_id: str = Field(..., description="Selected scenario ID (e.g., 'scenario-1')")
    reason_codes: List[ReasonCodeWithPercent] = Field(
        ...,
        min_length=1,
        description="Reason codes with percentages (must sum to 100)"
    )
    notes: str = Field(default="", description="Optional notes explaining the decision")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "agent-session-uuid",
                "scenario_id": "scenario-2",
                "reason_codes": [
                    {"code": "supplier_issue", "percent": 60},
                    {"code": "normal_delay", "percent": 40}
                ],
                "notes": "Approved spread scenario due to supplier delays"
            }
        }
