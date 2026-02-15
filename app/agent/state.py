"""
Agent State Definition for LangGraph Workflow
Based on Section 7.2 of implementation guide
"""
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class AgentStatus(str, Enum):
    """Agent execution status"""
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class ForecastAgentState(TypedDict):
    """
    Complete state for the Forecasting Agent workflow.
    This state is passed through all nodes in the LangGraph workflow.
    """

    # Request Information
    request_id: str
    session_id: str

    # Project Data (from input)
    project: Dict[str, Any]
    fiscal_year: int
    current_month: int
    forecasts: List[Dict[str, Any]]
    purchase_orders: List[Dict[str, Any]]
    available_reason_codes: List[Dict[str, Any]]

    # Calculated Metrics
    total_budget: float
    total_approved: float
    total_base_forecast: float
    total_forecast_with_rollover: float
    total_actuals: float
    budget_consumption_percent: float
    net_order_value: float
    total_pos: float
    months_with_actuals: int
    months_remaining: int

    # Analysis Results
    variances: List[Dict[str, Any]]
    flags: List[Dict[str, Any]]
    threshold_alerts: List[Dict[str, Any]]
    po_analysis: List[Dict[str, Any]]

    # Outputs
    scenarios: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    explanation: str
    summary: str

    # Status
    status: AgentStatus
    errors: List[str]
    timestamp: str
