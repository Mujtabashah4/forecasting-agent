"""
LangGraph Workflow for Forecasting Agent
Based on Section 7 of implementation guide
"""
from langgraph.graph import StateGraph, END
from app.agent.state import ForecastAgentState, AgentStatus
from app.agent.nodes.load_data import load_data_node
from app.agent.nodes.calculate_metrics import calculate_metrics_node
from app.agent.nodes.detect_variances import detect_variances_node
from app.agent.nodes.check_thresholds import check_thresholds_node
from app.agent.nodes.check_project_status import check_project_status_node
from app.agent.nodes.analyze_pos import analyze_pos_node
from app.agent.nodes.generate_scenarios import generate_scenarios_node
from app.agent.nodes.build_questions import build_questions_node
from app.agent.nodes.generate_explanation import generate_explanation_node
from app.agent.nodes.compile_response import compile_response_node
import uuid


def create_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for forecast analysis.

    Workflow sequence:
    1. Load Data → Validate input
    2. Calculate Metrics → NOV, totals, percentages
    3. Detect Variances → Find actuals > forecast
    4. Check Thresholds → 90% budget, NOV floor
    5. Check Project Status → Late detection, PO delivery analysis
    6. Analyze POs → Large POs detection
    7. Generate Scenarios → Create forecast options
    8. Build Questions → User questions
    9. Generate Explanation → LLM explanation
    10. Compile Response → Final output
    """
    # Create the state graph
    workflow = StateGraph(ForecastAgentState)

    # Add all nodes
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("calculate_metrics", calculate_metrics_node)
    workflow.add_node("detect_variances", detect_variances_node)
    workflow.add_node("check_thresholds", check_thresholds_node)
    workflow.add_node("check_project_status", check_project_status_node)
    workflow.add_node("analyze_pos", analyze_pos_node)
    workflow.add_node("generate_scenarios", generate_scenarios_node)
    workflow.add_node("build_questions", build_questions_node)
    workflow.add_node("generate_explanation", generate_explanation_node)
    workflow.add_node("compile_response", compile_response_node)

    # Set entry point
    workflow.set_entry_point("load_data")

    # Add edges in sequence
    workflow.add_edge("load_data", "calculate_metrics")
    workflow.add_edge("calculate_metrics", "detect_variances")
    workflow.add_edge("detect_variances", "check_thresholds")
    workflow.add_edge("check_thresholds", "check_project_status")
    workflow.add_edge("check_project_status", "analyze_pos")
    workflow.add_edge("analyze_pos", "generate_scenarios")
    workflow.add_edge("generate_scenarios", "build_questions")
    workflow.add_edge("build_questions", "generate_explanation")
    workflow.add_edge("generate_explanation", "compile_response")
    workflow.add_edge("compile_response", END)

    return workflow.compile()


async def run_forecast_analysis(request_data: dict) -> ForecastAgentState:
    """
    Run complete forecast analysis workflow asynchronously.

    Args:
        request_data: Input request data matching ForecastReviewRequest schema

    Returns:
        ForecastAgentState: Complete agent state with analysis results
    """
    # Initialize state
    initial_state: ForecastAgentState = {
        'request_id': request_data.get('request_id'),
        'session_id': str(uuid.uuid4()),
        'project': request_data.get('project'),
        'fiscal_year': request_data.get('fiscal_year'),
        'current_month': request_data.get('current_month'),
        'forecasts': request_data.get('forecasts'),
        'purchase_orders': request_data.get('purchase_orders', []),
        'available_reason_codes': request_data.get('reason_codes', []),
        # Metrics (calculated)
        'total_budget': 0,
        'total_approved': 0,
        'total_base_forecast': 0,
        'total_forecast_with_rollover': 0,
        'total_actuals': 0,
        'budget_consumption_percent': 0,
        'net_order_value': 0,
        'total_pos': 0,
        'months_with_actuals': 0,
        'months_remaining': 0,
        # Analysis results
        'variances': [],
        'flags': [],
        'threshold_alerts': [],
        'po_analysis': [],
        # Outputs
        'scenarios': [],
        'questions': [],
        'explanation': '',
        'summary': '',
        # Status
        'status': AgentStatus.INITIALIZED,
        'errors': [],
        'timestamp': ''
    }

    # Create and run workflow asynchronously
    workflow = create_workflow()
    result = await workflow.ainvoke(initial_state)

    return result
