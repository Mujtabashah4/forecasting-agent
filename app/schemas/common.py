"""
Common schemas shared across the application
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectInfo(BaseModel):
    """Project information"""
    id: str
    code: str
    name: str
    budget: float = Field(ge=0)
    approved_amount: float = Field(ge=0)
    start_date: str
    anticipated_end_date: str
    status: str


class ForecastMonth(BaseModel):
    """Forecast data for a single month"""
    month: int = Field(ge=1, le=12)
    base_forecast: float = Field(ge=0)
    forecast_with_rollover: float = Field(ge=0)
    actual: Optional[float] = None


class PurchaseOrder(BaseModel):
    """Purchase order information"""
    po_number: str
    amount: float = Field(ge=0)
    issue_date: str
    estimated_delivery: str
    actual_delivery: Optional[str] = None
    status: str


class ReasonCode(BaseModel):
    """Reason code for forecast adjustments"""
    code: str
    description: str


class Flag(BaseModel):
    """Issue flag detected by agent"""
    type: str
    severity: str
    message: str
    month: Optional[int] = None
    forecast: Optional[float] = None
    actual: Optional[float] = None
    variance: Optional[float] = None
    variance_percent: Optional[float] = None
    po_number: Optional[str] = None
    po_amount: Optional[float] = None
    monthly_forecast: Optional[float] = None
    ratio: Optional[float] = None
    # Project late detection fields
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    anticipated_end_date: Optional[str] = None
    days_late: Optional[int] = None
    # PO delivery analysis fields
    delivery_month: Optional[int] = None
    estimated_delivery: Optional[str] = None
    excess_ratio: Optional[float] = None


class ThresholdAlert(BaseModel):
    """Threshold alert from checks"""
    type: str
    severity: str
    message: str
    threshold: Optional[float] = None
    current: Optional[float] = None
    nov: Optional[float] = None
    future_forecast_total: Optional[float] = None
    shortfall: Optional[float] = None


class QuestionOption(BaseModel):
    """Option for a question"""
    value: str
    label: str
    follow_up: Optional[str] = None


class Question(BaseModel):
    """Question for user"""
    question_id: str
    type: str
    priority: str
    text: str
    options: list[QuestionOption]
    requires_reason: bool = False


class ScenarioForecast(BaseModel):
    """Forecast values for a scenario"""
    month: int = Field(ge=1, le=12)
    amount: float = Field(ge=0)


class SuggestedReasonCode(BaseModel):
    """Suggested reason code with percentage"""
    code: str
    suggested_percent: int = Field(ge=0, le=100)


class Scenario(BaseModel):
    """Forecast scenario"""
    scenario_id: str
    name: str
    description: str
    forecasts: list[ScenarioForecast]
    total_year_forecast: float
    variance_from_budget: float
    suggested_reason_codes: Optional[list[SuggestedReasonCode]] = None


class Analysis(BaseModel):
    """Analysis summary"""
    summary: str
    budget: float
    approved_amount: float
    total_base_forecast: float
    total_forecast_with_rollover: float
    total_actuals_to_date: float
    budget_consumption_percent: float
    net_order_value: float
    months_with_actuals: int
    months_remaining: int
