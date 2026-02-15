"""
Node 4: Check Thresholds
Checks 90% budget threshold and NOV constraints
"""
from app.agent.state import ForecastAgentState


def check_thresholds_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Check 90% budget threshold and NOV constraints.

    Business Rules:
    1. Alert when budget consumption >= 90%
    2. Future forecast total MUST be >= NOV (minimum floor)
    """
    threshold_alerts = []

    # Check 90% budget consumption
    if state['budget_consumption_percent'] >= 90:
        threshold_alerts.append({
            'type': 'budget_threshold',
            'severity': 'high',
            'threshold': 90,
            'current': round(state['budget_consumption_percent'], 2),
            'message': f"Budget consumption at {state['budget_consumption_percent']:.1f}% - exceeds 90% threshold"
        })

    # Check NOV constraint
    # Future forecasts must be >= NOV
    future_forecasts = [
        f.get('forecast_with_rollover', 0)
        for f in state['forecasts']
        if f.get('actual') is None
    ]
    future_total = sum(future_forecasts)

    if future_total < state['net_order_value']:
        shortfall = state['net_order_value'] - future_total
        threshold_alerts.append({
            'type': 'nov_constraint',
            'severity': 'high',
            'nov': state['net_order_value'],
            'future_forecast_total': future_total,
            'shortfall': shortfall,
            'message': f"Future forecasts (${future_total:,.0f}) are below NOV (${state['net_order_value']:,.0f}). Shortfall: ${shortfall:,.0f}"
        })

    state['threshold_alerts'] = threshold_alerts
    return state
