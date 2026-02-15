"""
Node 1: Load Data
Validates and loads input data into agent state
"""
from app.agent.state import ForecastAgentState, AgentStatus


def load_data_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Validate and load input data.

    Business Rule: Ensure all required fields exist
    """
    # Validate required fields exist
    required = ['request_id', 'project', 'fiscal_year', 'current_month', 'forecasts']
    for field in required:
        if field not in state or state[field] is None:
            state['errors'].append(f"Missing required field: {field}")
            state['status'] = AgentStatus.ERROR
            return state

    # Extract project info
    project = state['project']
    state['total_budget'] = project.get('budget', 0)
    state['total_approved'] = project.get('approved_amount', 0)

    # Count months
    forecasts = state['forecasts']
    state['months_with_actuals'] = len([f for f in forecasts if f.get('actual') is not None])
    state['months_remaining'] = 12 - state['months_with_actuals']

    state['status'] = AgentStatus.PROCESSING
    return state
