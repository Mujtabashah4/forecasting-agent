"""
Response schemas for API endpoints
Based on Section 5.2 of implementation guide
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.common import Analysis, Flag, ThresholdAlert, Question, Scenario


class ForecastReviewResponse(BaseModel):
    """
    Response from forecast review
    This is what the AI Server returns to Capexplan
    """
    request_id: str = Field(..., description="Original request ID from input")
    session_id: str = Field(..., description="Agent session identifier")
    status: str = Field(..., description="Status: completed, error, etc.")
    analysis: Analysis
    flags: List[Flag] = Field(default_factory=list)
    threshold_alerts: List[ThresholdAlert] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)
    scenarios: List[Scenario] = Field(default_factory=list)
    explanation: str = Field(..., description="LLM-generated human-readable explanation")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response generation")

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "agent-session-uuid",
                "status": "completed",
                "analysis": {
                    "summary": "Project showing cost overruns in months 1-2",
                    "budget": 120000.00,
                    "approved_amount": 120000.00,
                    "total_base_forecast": 12000.00,
                    "total_forecast_with_rollover": 12050.00,
                    "total_actuals_to_date": 3150.00,
                    "budget_consumption_percent": 26.25,
                    "net_order_value": 7950.00,
                    "months_with_actuals": 3,
                    "months_remaining": 9
                },
                "flags": [],
                "threshold_alerts": [],
                "questions": [],
                "scenarios": [],
                "explanation": "Project is tracking well within budget.",
                "timestamp": "2024-04-15T10:30:00Z"
            }
        }


class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    llm_status: str
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: str


class QuestionResponseResponse(BaseModel):
    """Response after submitting a question response"""
    session_id: str
    question_id: str
    response_value: str
    status: str = "recorded"
    message: str
    timestamp: str


class ScenarioApprovalResponse(BaseModel):
    """Response after approving a scenario"""
    session_id: str
    scenario_id: str
    scenario_name: str
    status: str = "approved"
    approved_forecasts: List[dict]
    total_year_forecast: float
    variance_from_budget: float
    reason_codes: List[dict]
    message: str
    timestamp: str
    next_steps: List[str] = Field(
        default_factory=list,
        description="Suggested next steps after approval"
    )


class SessionStatusResponse(BaseModel):
    """Response with session status and history"""
    session_id: str
    request_id: str
    project_id: str
    project_name: str
    status: str
    responses: List[dict] = Field(default_factory=list)
    approved_scenario: Optional[dict] = None
    created_at: str
    last_updated: str


class StorageStatsResponse(BaseModel):
    """Response with storage statistics"""
    total_sessions: int
    total_responses: int
    total_approvals: int
    projects_with_history: int
