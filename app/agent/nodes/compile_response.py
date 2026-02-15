"""
Node 9: Compile Response
Builds final response object
"""
from app.agent.state import ForecastAgentState, AgentStatus
from datetime import datetime


def compile_response_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Build final response object.

    This is the final node - marks status as COMPLETED
    """
    state['timestamp'] = datetime.utcnow().isoformat() + 'Z'
    state['status'] = AgentStatus.COMPLETED

    # Response is built from state - all data already in state
    # The API layer will extract relevant fields to match response schema
    return state
